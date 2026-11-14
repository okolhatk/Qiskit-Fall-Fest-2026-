# Surface-Code Optimization — Quick Overview

**Goal:** perform the same four joint measurements using fewer tiles and fewer
logical time steps, while making the Python implementation faster and smaller.

## Main result

The workload measures **ZZ on A-B and C-D**, followed by **XX on B-C and A-D**.
The second round waits for both first-round measurements.

| Layout | Tiles | Steps | Tile-steps |
|---|---:|---:|---:|
| Original compact | 15 | 4 | 60 |
| Original spacious | 35 | 3 | 105 |
| Workload-aligned | **9** | **2** | **18** |

**Tile-steps = board area × elapsed steps.** Compared with compact, the aligned
layout uses **40% less area, 50% fewer steps, and 70% fewer tile-steps**.

```text
A . D
. . .
B . C
```

ZZ partners use the left/right middle tiles concurrently. XX partners then use
the top/bottom middle tiles concurrently. The unused center still counts.

Two dependency rounds require at least two steps. An independent exhaustive
check of **4,104 smaller-board placements**, plus exclusion of one-row/column
boards without the required ports, establishes nine tiles as minimum area
**for this workload under the implemented model**.

## How it works

- **Router:** breadth-first search finds a shortest available auxiliary path.
- **Scheduler:** runs ready operations in input order, deferring conflicts.
- **Validator:** independently checks paths, dependencies, boundaries, and conflicts.
- **Qiskit:** six ideal three-qubit circuits check ZZ/XX parity outcomes.

## Software improvements

- Occupancy sets reduce routing from **O(A × P)** to expected **O(A)** time,
  where A is board area and P is patch count. BFS memory remains O(A).
- Ordered ready lists avoid repeated sorting; compact dependency tracking reduces memory.
- Streaming validation removes quadratic completed-set copying and duplicate path storage.
- Grid lines replace per-tile background rectangles: geometry scales with
  **width + height**, rather than **width × height**, per displayed step.
- Packed XOR elimination reduces the QEC lab's binary-rank overhead.

The latest pass, compared with the already-optimized version, measured:

| Component benchmark | Speedup | Peak Python memory reduction |
|---|---:|---:|
| Large-board routing | 2.0× | Unchanged |
| 300 contending operations | 3.1× | 33% |
| Validation of 1,000 operations | 2.9× | 18% |
| Rendering/saving a 24×24 board | 5.6× | 86% |

These are local component measurements, not guaranteed end-to-end gains.
Python allocation tracking excludes native-library memory. **Software runtime
and memory are separate from logical steps and tiles.**

## Trade-offs and limits

- The placement is specialized to these pairings; the scheduler is still greedy
  for other workloads. Dependency tracking requires extra bookkeeping memory.
- The model uses fixed, single-tile patches with fixed X/Z boundaries on a
  rectangular board and nonempty auxiliary paths. Measurements cost one step
  regardless of path length; preparation/release add no cost.
- It excludes moves, rotations, direct adjacent-patch surgery, noise, decoding,
  code-distance calculations, and physical timing. Its optimum is scoped to
  these assumptions, not the full game or hardware.
- Qiskit checks representative parity outcomes, not encoded fault-tolerant surgery.
- Latest optimizations preserve routes, schedules, circuits, and shot counts.
  Invalid schedules now raise `ValueError`, including under Python `-O`.

## Verification

**11 tests passed normally and with `-O`**, covering 1,600 independent route
comparisons, 300 randomized schedules, smaller-board enumeration, invalid
schedules, rendering, binary rank, and quantum parity checks.

The full demonstration passed all six parity cases at **1,024 shots each**.
Numerical JSON/CSV results stayed unchanged after the latest software refinements.

## Run it

From the repository folder in PowerShell, using the existing environment:

```powershell
# Demonstration, figures, and results
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py

# Regression tests
.\qiskit-env\Scripts\python.exe -B -m unittest test_optimizations -v

# Faster numerical run without figures
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py --no-plots --output quick_results
```

**Presentation takeaway:** matching patch placement to the workload improved
both space and time; eliminating redundant computation improved the software
without sacrificing tested behavior.

For details, see [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md),
[CHALLENGE_GUIDE.md](CHALLENGE_GUIDE.md), and the
[layout diagram](challenge_results/workload_aligned_schedule.png).
