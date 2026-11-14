"""Run with python -m unittest test_optimizations -v (no hardware access)."""

import random
import unittest
import copy
import json
from collections import deque
from itertools import permutations
from unittest.mock import patch

import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

from gf2 import binary_rank
from qec_checkpoints import _toric_matrices, _gross_matrices
from surface_code_challenge import (
    LAYOUTS, Layout, Measurement, WORKLOAD, parity_circuit, route, schedule,
    validate_schedule, verify_quantum, draw_schedule,
)


def reference_rank(matrix):
    """Independent dense column-pivot elimination over GF(2)."""
    a = matrix.copy().astype(np.uint8)
    rank = 0
    for col in range(a.shape[1]):
        candidates = np.flatnonzero(a[rank:, col])
        if not len(candidates):
            continue
        pivot = rank + candidates[0]
        a[[rank, pivot]] = a[[pivot, rank]]
        for row in range(rank + 1, len(a)):
            if a[row, col]:
                a[row] ^= a[rank]
        rank += 1
    return rank


def reference_route(layout, op, reserved=frozenset()):
    """Independent tuple BFS oracle with the original dequeue termination."""
    occupied = set(layout.patches.values())
    offsets = {'X': ((-1, 0), (1, 0)), 'Z': ((0, -1), (0, 1))}

    def free(cell):
        return (0 <= cell[0] < layout.width and 0 <= cell[1] < layout.height
                and cell not in occupied and cell not in reserved)

    def ports(label):
        x, y = layout.patches[label]
        return [(x+dx, y+dy) for dx, dy in offsets[op.basis] if free((x+dx, y+dy))]

    starts, targets = ports(op.first), set(ports(op.second))
    parents = {cell: None for cell in starts}
    queue = deque(starts)
    while queue:
        cell = queue.popleft()
        if cell in targets:
            path = []
            while cell is not None:
                path.append(cell)
                cell = parents[cell]
            return path[::-1]
        x, y = cell
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nxt = x+dx, y+dy
            if free(nxt) and nxt not in parents:
                parents[nxt] = cell
                queue.append(nxt)
    return None


def reference_schedule(layout, workload):
    """Original full-scan scheduling policy, for equivalence checks."""
    completed, steps = set(), []
    while len(completed) < len(workload):
        reserved, busy, current = set(), set(), []
        for op in workload:
            if op.name in completed or not set(op.after) <= completed:
                continue
            if busy.intersection((op.first, op.second)):
                continue
            path = reference_route(layout, op, reserved)
            if path is None:
                continue
            current.append(dict(operation=op.name, basis=op.basis,
                                patches=[op.first, op.second], path=path))
            reserved.update(path)
            busy.update((op.first, op.second))
        if not current:
            raise ValueError("blocked")
        steps.append(current)
        completed.update(item['operation'] for item in current)
    return steps


class OptimizationTests(unittest.TestCase):
    def test_routes_match_independent_bfs(self):
        rng = random.Random(184)
        for _ in range(800):
            w, h = rng.randint(2, 12), rng.randint(2, 12)
            cells = [(x, y) for x in range(w) for y in range(h)]
            rng.shuffle(cells)
            count = rng.randint(2, min(len(cells), 20))
            layout = Layout('random', w, h,
                            {str(i): cell for i, cell in enumerate(cells[:count])})
            reserved = set(cells[count:count+rng.randint(0, len(cells)-count)])
            for basis in 'XZ':
                op = Measurement('test', '0', '1', basis)
                self.assertEqual(route(layout, op, reserved),
                                 reference_route(layout, op, reserved))

    def test_nine_tiles_is_minimum_in_restricted_model(self):
        # A one-tile-wide/high board has no X/Z ports, respectively.
        # Enumerate ALL remaining rectangular boards below nine tiles,
        # including ALL assignments of four labeled single-tile patches.
        checked = 0
        for width in range(2, 9):
            for height in range(2, 9):
                if width * height >= 9:
                    continue
                cells = [(x, y) for x in range(width) for y in range(height)]
                for positions in permutations(cells, 4):
                    layout = Layout('exhaustive', width, height,
                                    dict(zip('ABCD', positions)))
                    self.assertFalse(all(reference_route(layout, op) is not None
                                         for op in WORKLOAD))
                    checked += 1
        self.assertEqual(checked, 4104)
        self.assertEqual(len(schedule(LAYOUTS[-1])), 2)

    def test_layout_results_and_dependencies(self):
        for layout, expected in zip(LAYOUTS, (4, 3, 2)):
            result = schedule(layout)
            validate_schedule(layout, result)
            self.assertEqual(len(result), expected)
            self.assertEqual(result, reference_schedule(layout, WORKLOAD))
        self.assertEqual(LAYOUTS[-1].area * len(schedule(LAYOUTS[-1])), 18)

    def test_ready_queue_preserves_policy(self):
        rng = random.Random(42)
        for _ in range(100):
            workload = []
            for i in range(15):
                first, second = rng.sample(list('ABCD'), 2)
                after = tuple(op.name for op in workload if rng.random() < .15)
                workload.append(Measurement(str(i), first, second,
                                            rng.choice('XZ'), after))
            rng.shuffle(workload)  # Dependency order need not equal list order.
            for layout in LAYOUTS:
                expected = reference_schedule(layout, workload)
                actual = schedule(layout, workload)
                self.assertEqual(actual, expected)
                validate_schedule(layout, actual, workload)

    def test_invalid_inputs_and_cycles(self):
        for workload in [
            (Measurement('a', 'A', 'B', 'Z', ('missing',)),),
            (Measurement('a', 'A', 'B', 'Z', ('a',)),),
            (Measurement('a', 'A', 'A', 'Z'),),
            (Measurement('a', 'A', 'B', 'Y'),),
            (Measurement('a', 'A', 'E', 'Z'),),
            (WORKLOAD[0], WORKLOAD[0]),
        ]:
            with self.assertRaises(ValueError):
                schedule(LAYOUTS[0], workload)
        self.assertEqual(schedule(LAYOUTS[0], ()), [])
        blocked = Layout('blocked', 2, 1, {'A': (0, 0), 'B': (1, 0)})
        self.assertIsNone(route(blocked, WORKLOAD[0]))

    def test_duplicate_dependencies_release_once_and_at_step_end(self):
        workload = (Measurement('second', 'C', 'D', 'Z', ('first', 'first')),
                    Measurement('first', 'A', 'B', 'Z'))
        steps = schedule(LAYOUTS[-1], workload)
        self.assertEqual(steps, reference_schedule(LAYOUTS[-1], workload))
        self.assertEqual([step[0]['operation'] for step in steps], ['first', 'second'])

    def test_validator_rejects_corrupt_schedules(self):
        layout = LAYOUTS[-1]
        good = schedule(layout)
        # JSON paths are lists, not tuples, and must still validate.
        validate_schedule(layout, json.loads(json.dumps(good)))
        corrupt = []
        bad = copy.deepcopy(good); bad[0][0]['basis'] = 'X'; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['patches'].reverse(); corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['path'] = []; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['path'] *= 2; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['path'] = [(0, 0)]; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['path'] = [(1, 0)]; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['path'] = [(-1, 1)]; corrupt.append(bad)
        bad = copy.deepcopy(good); bad[0][0]['operation'] = 'unknown'; corrupt.append(bad)
        corrupt.extend([good[::-1], good[:1], [good[0], good[0], good[1]],
                        [good[0] + good[1]], [[], *good]])
        for bad in corrupt:
            with self.assertRaises(ValueError):
                validate_schedule(layout, bad)
        compact = copy.deepcopy(schedule(LAYOUTS[0]))
        with self.assertRaises(ValueError):
            validate_schedule(LAYOUTS[0], [compact[0] + compact[1], *compact[2:]])
        compact[0][0]['path'].pop(1)
        with self.assertRaises(ValueError):
            validate_schedule(LAYOUTS[0], compact)

    def test_grid_rendering_and_four_concurrent_paths(self):
        import matplotlib.pyplot as plt
        patches = {f'{i}{side}': (3*i, y) for i in range(4)
                   for side, y in [('a', 0), ('b', 2)]}
        layout = Layout('four paths', 10, 3, patches)
        workload = tuple(Measurement(str(i), f'{i}a', f'{i}b', 'Z') for i in range(4))
        steps = schedule(layout, workload)
        self.assertEqual(len(steps), 1)
        validate_schedule(layout, steps, workload)
        try:
            with patch('matplotlib.figure.Figure.savefig'), patch.object(plt, 'close'):
                draw_schedule(layout, steps, 'unused.png')
            ax = plt.gcf().axes[0]
            self.assertEqual(len(ax.patches), 1 + 4 + 8)
            self.assertEqual(sum(len(c.get_segments()) for c in ax.collections), 15)
        finally:
            plt.close('all')

    def test_occupancy_snapshot(self):
        patches = {'A': (0, 0), 'B': (2, 2)}
        layout = Layout('test', 3, 3, patches)
        patches['A'] = (1, 1)
        self.assertFalse(layout.empty((0, 0)))
        self.assertTrue(layout.empty((1, 1)))
        with self.assertRaises(TypeError):
            layout.patches['A'] = (1, 1)

    def test_packed_rank_random_and_lab_codes(self):
        rng = np.random.default_rng(42)
        for m, n in [(0, 0), (0, 5), (5, 0), (1, 1), (7, 3), (3, 7),
                     (20, 65), (72, 144)]:
            for _ in range(12):
                a = rng.integers(0, 2, (m, n))
                original = a.copy()
                self.assertEqual(binary_rank(a), reference_rank(a))
                np.testing.assert_array_equal(a, original)
        for matrices in (_toric_matrices(), _gross_matrices()):
            for a in matrices:
                self.assertEqual(binary_rank(a), reference_rank(a))
        self.assertEqual(144 - sum(map(binary_rank, _toric_matrices())), 2)
        with self.assertRaises(ValueError):
            binary_rank([[0, 2]])

    def test_quantum_parities_and_reference_backend(self):
        self.assertEqual(len(verify_quantum(64)), 6)
        backend = AerSimulator(method='statevector')
        for basis in 'ZX':
            for preparation, expected in [('even', '0'), ('odd', '1'), ('bell', '0')]:
                qc = parity_circuit(basis, preparation)
                counts = backend.run(transpile(qc, backend), shots=64).result().get_counts()
                self.assertEqual(counts, {expected: 64})


if __name__ == '__main__':
    unittest.main()
