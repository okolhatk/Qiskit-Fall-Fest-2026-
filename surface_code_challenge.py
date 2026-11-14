r"""Restricted tile-game experiment; not a physical surface-code simulation.

Run: .\qiskit-env\Scripts\python.exe surface_code_challenge.py
Outputs are written to challenge_results/ by default.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import deque
from dataclasses import dataclass, field
from heapq import merge
from types import MappingProxyType
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

Cell = tuple[int, int]
OFFSETS = {"Z": ((0, -1), (0, 1)), "X": ((-1, 0), (1, 0))}


@dataclass(frozen=True)
class Layout:
    name: str
    width: int
    height: int
    patches: dict[str, Cell]
    _occupied: frozenset[Cell] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Board dimensions must be positive")
        patches = {label: tuple(cell) for label, cell in self.patches.items()}
        occupied = frozenset(patches.values())
        if len(occupied) != len(patches):
            raise ValueError("Patches must occupy distinct tiles")
        if any(not (0 <= x < self.width and 0 <= y < self.height)
               for x, y in occupied):
            raise ValueError("Patch outside board")
        object.__setattr__(self, "patches", MappingProxyType(patches))
        object.__setattr__(self, "_occupied", occupied)

    @property
    def area(self):
        return self.width * self.height

    def empty(self, cell):
        x, y = cell
        return (0 <= x < self.width and 0 <= y < self.height
                and cell not in self._occupied)


@dataclass(frozen=True)
class Measurement:
    name: str
    first: str
    second: str
    basis: str
    after: tuple[str, ...] = ()


# The second pair waits for BOTH first-round results, preserving this order
# even where two observables do not commute. Within each pair, data is disjoint.
WORKLOAD = (
    Measurement("AB_ZZ", "A", "B", "Z"),
    Measurement("CD_ZZ", "C", "D", "Z"),
    Measurement("BC_XX", "B", "C", "X", ("AB_ZZ", "CD_ZZ")),
    Measurement("AD_XX", "A", "D", "X", ("AB_ZZ", "CD_ZZ")),
)
LAYOUTS = (
    Layout("compact", 5, 3, {"A": (0, 0), "B": (4, 0),
                              "C": (0, 2), "D": (4, 2)}),
    Layout("spacious", 7, 5, {"A": (0, 0), "B": (6, 0),
                               "C": (0, 4), "D": (6, 4)}),
    # Put ZZ partners vertically and XX partners horizontally.
    Layout("workload_aligned", 3, 3, {"A": (0, 0), "B": (0, 2),
                                       "C": (2, 2), "D": (2, 0)}),
)


def route(layout, operation, reserved=frozenset()):
    """Shortest empty-tile path between suitable boundary-adjacent tiles.

    Z boundaries are north/south; X boundaries are east/west. Only endpoint
    boundaries are coupled; incidental contact with other patches is inactive.
    """
    offsets = OFFSETS[operation.basis]

    def ports(label):
        x, y = layout.patches[label]
        return [(x + dx, y + dy) for dx, dy in offsets
                if layout.empty((x + dx, y + dy))
                and (x + dx, y + dy) not in reserved]

    starts, targets = ports(operation.first), set(ports(operation.second))
    if not starts or not targets:
        return None
    # A shared boundary tile is already a shortest route.
    for cell in starts:
        if cell in targets:
            return [cell]
    parents = {cell: None for cell in starts}
    queue = deque(starts)
    width, height, occupied = layout.width, layout.height, layout._occupied
    while queue:
        cell = queue.popleft()
        x, y = cell
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nxt = x + dx, y + dy
            if (nxt not in parents and 0 <= nxt[0] < width
                    and 0 <= nxt[1] < height and nxt not in occupied
                    and nxt not in reserved):
                parents[nxt] = cell
                # FIFO discovery order has the same shortest-path tie-break
                # as dequeue order. Do not expand the rest of this BFS layer.
                if nxt in targets:
                    path = [nxt]
                    while cell is not None:
                        path.append(cell)
                        cell = parents[cell]
                    path.reverse()
                    return path
                queue.append(nxt)
    return None


def schedule(layout, workload=WORKLOAD):
    """Deterministic greedy scheduling; makes no optimality claim."""
    workload = tuple(workload)
    indices = {op.name: i for i, op in enumerate(workload)}
    if len(indices) != len(workload):
        raise ValueError("Measurement names must be unique")
    if any(dep not in indices for op in workload for dep in op.after):
        raise ValueError("Unknown dependency")
    for op in workload:
        if op.basis not in OFFSETS:
            raise ValueError("Only X and Z measurements are supported")
        if op.first == op.second or any(p not in layout.patches
                                       for p in (op.first, op.second)):
            raise ValueError("Measurements need two distinct known patches")
    # Only reconsider ready operations. Release dependents AFTER the step.
    remaining = [0] * len(workload)
    dependents = [None] * len(workload)
    for index, op in enumerate(workload):
        dependencies = set(op.after)
        remaining[index] = len(dependencies)
        for dep in dependencies:
            parent = indices[dep]
            if dependents[parent] is None:
                dependents[parent] = []
            dependents[parent].append(index)
    del indices
    ready = [i for i, count in enumerate(remaining) if count == 0]
    completed, steps = 0, []
    while completed < len(workload):
        reserved, busy, current = set(), set(), []
        deferred, finished = [], []
        for index in ready:
            op = workload[index]
            if op.first in busy or op.second in busy:
                deferred.append(index)
                continue
            path = route(layout, op, reserved)
            if path is None:
                deferred.append(index)
                continue
            current.append({"operation": op.name, "basis": op.basis,
                            "patches": [op.first, op.second], "path": path})
            reserved.update(path)
            busy.update((op.first, op.second))
            finished.append(index)
        if not current:
            raise ValueError(f"{layout.name}: blocked route or cyclic dependencies")
        steps.append(current)
        completed += len(finished)
        newly_ready = []
        for parent in finished:
            for index in dependents[parent] or ():
                remaining[index] -= 1
                if remaining[index] == 0:
                    newly_ready.append(index)
            dependents[parent] = None  # Release edges as soon as consumed.
        # Deferred operations are already in input order. Each newly ready
        # operation is sorted only once, not again on every contention retry.
        newly_ready.sort()
        ready = (list(merge(deferred, newly_ready)) if deferred and newly_ready
                 else deferred or newly_ready)
    return steps


def validate_schedule(layout, steps, workload=WORKLOAD):
    """Check the schedule independently, including when Python runs with -O.

    Stream path cells into the step's reserved set instead of copying paths
    and building another set per operation. Invalid schedules raise ValueError.
    """
    workload = tuple(workload)
    operations = {op.name: op for op in workload}
    if len(operations) != len(workload):
        raise ValueError("Measurement names must be unique")

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    completed = set()
    for step in steps:
        require(bool(step), "Empty schedule step")
        reserved, busy, finishing = set(), set(), set()
        for item in step:
            require(item["operation"] in operations, "Unknown operation")
            op = operations[item["operation"]]
            require(op.basis in OFFSETS, "Unsupported measurement basis")
            require(op.first != op.second and op.first in layout.patches
                    and op.second in layout.patches, "Invalid measurement patches")
            require(item["basis"] == op.basis
                    and tuple(item["patches"]) == (op.first, op.second),
                    "Measurement metadata does not match workload")
            require(op.name not in completed and op.name not in finishing,
                    "Duplicate operation")
            require(all(dep in completed for dep in op.after),
                    "Unfinished dependency")
            require(op.first not in busy and op.second not in busy,
                    "Concurrent operations share data patches")
            first = previous = None
            for raw_cell in item["path"]:
                cell = tuple(raw_cell)
                require(layout.empty(cell), "Path leaves board or crosses data patch")
                require(cell not in reserved, "Repeated or reserved path tile")
                if previous is not None:
                    require(abs(cell[0]-previous[0]) + abs(cell[1]-previous[1]) == 1,
                            "Discontinuous path")
                else:
                    first = cell
                reserved.add(cell)
                previous = cell
            require(first is not None, "Empty path")
            for endpoint, label in ((first, op.first), (previous, op.second)):
                x, y = layout.patches[label]
                require((endpoint[0]-x, endpoint[1]-y) in OFFSETS[op.basis],
                        "Path touches wrong boundary")
            busy.update((op.first, op.second))
            finishing.add(op.name)
        completed.update(finishing)
    require(len(completed) == len(operations), "Incomplete schedule")


def parity_circuit(basis, preparation):
    """Ideal representative-qubit measurement, NOT encoded lattice surgery."""
    if basis not in OFFSETS:
        raise ValueError("Only X and Z measurements are supported")
    qc = QuantumCircuit(3, 1)
    if preparation == "odd":
        qc.x(0)
    elif preparation == "bell":
        qc.h(0)
        qc.cx(0, 1)
    elif preparation != "even":
        raise ValueError(preparation)
    # For X eigenstates, rotate prepared computational states into X basis.
    if basis == "X" and preparation != "bell":
        qc.h([0, 1])
    qc.barrier()
    if basis == "X":
        qc.h([0, 1])
    qc.cx(0, 2)
    qc.cx(1, 2)
    if basis == "X":
        qc.h([0, 1])
    qc.measure(2, 0)
    return qc


def verify_quantum(shots, out=None):
    if shots <= 0:
        raise ValueError("shots must be positive")
    backend = AerSimulator(method="stabilizer")
    results = {}
    for basis in ("Z", "X"):
        for preparation, expected in (("even", "0"), ("odd", "1"), ("bell", "0")):
            qc = parity_circuit(basis, preparation)
            counts = backend.run(transpile(qc, backend), shots=shots,
                                 seed_simulator=42).result().get_counts()
            if counts != {expected: shots}:
                raise AssertionError((basis, preparation, counts))
            key = f"{basis}{basis}_{preparation}"
            results[key] = {"counts": counts, "expected_bit": expected,
                            "expected_eigenvalue": 1 if expected == "0" else -1}
            if out is not None:
                fig = qc.draw("mpl")
                fig.savefig(out / f"{key}.png", bbox_inches="tight")
                plt.close(fig)
    return results


def draw_schedule(layout, steps, destination):
    fig, axes = plt.subplots(1, len(steps), figsize=(4*len(steps), 4), squeeze=False)
    for index, (ax, step) in enumerate(zip(axes[0], steps), 1):
        # The empty board needs one background and W+H+2 grid segments,
        # rather than W*H independently allocated Rectangle artists.
        ax.add_patch(Rectangle((0, 0), layout.width, layout.height,
                               facecolor="white", edgecolor="none", zorder=0))
        ax.vlines(range(layout.width + 1), 0, layout.height,
                  colors="#dddddd", linewidths=1, zorder=.5)
        ax.hlines(range(layout.height + 1), 0, layout.width,
                  colors="#dddddd", linewidths=1, zorder=.5)
        colors = ("#a8dadc", "#f4b183", "#c6b5e5")
        for item_index, item in enumerate(step):
            color = colors[item_index % len(colors)]
            for x, y in item["path"]:
                ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor="gray"))
        for label, (x, y) in layout.patches.items():
            ax.add_patch(Rectangle((x, y), 1, 1, facecolor="#ffe7a0", edgecolor="none"))
            ax.text(x+.5, y+.5, label, ha="center", va="center", weight="bold")
            ax.plot([x, x+1], [y, y], color="black")
            ax.plot([x, x+1], [y+1, y+1], color="black")
            ax.plot([x, x], [y, y+1], color="black", linestyle=":")
            ax.plot([x+1, x+1], [y, y+1], color="black", linestyle=":")
        ax.set(xlim=(-.2, layout.width+.2), ylim=(layout.height+.2, -.2),
               title=f"Step {index}\n" + ", ".join(i["operation"] for i in step))
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(f"{layout.name}: {layout.area} tiles; solid Z / dotted X boundaries")
    fig.tight_layout()
    fig.savefig(destination, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("challenge_results"))
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip figure rendering for quick experiments")
    args = parser.parse_args()
    if args.shots <= 0:
        parser.error("--shots must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    summaries, schedules = [], {}
    for layout in LAYOUTS:
        steps = schedule(layout)
        validate_schedule(layout, steps)
        schedules[layout.name] = steps
        summary = {"layout": layout.name, "tiles": layout.area,
                   "time_steps": len(steps), "operations": len(WORKLOAD),
                   "tile_steps": layout.area * len(steps)}
        summaries.append(summary)
        if not args.no_plots:
            draw_schedule(layout, steps, args.output / f"{layout.name}_schedule.png")
        print(f"{layout.name}: {layout.area} tiles, {len(steps)} steps, "
              f"{summary['tile_steps']} tile-steps")
        for index, step in enumerate(steps, 1):
            print(f"  Step {index}: " + ", ".join(i["operation"] for i in step))
    quantum = verify_quantum(args.shots, None if args.no_plots else args.output)
    with (args.output / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    (args.output / "results.json").write_text(json.dumps(
        {"comparison": summaries, "schedules": schedules, "quantum_checks": quantum},
        indent=2), encoding="utf-8")
    print(f"All schedules validated; {len(quantum)} quantum checks passed.")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()
