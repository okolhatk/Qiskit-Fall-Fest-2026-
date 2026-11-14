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

## How the project addresses the grading criteria

### Qiskit integration — 10%

**Criterion:** How did the participants integrate Qiskit into their project?

We use Qiskit to construct and verify the quantum measurement building blocks
represented by the board operations. `QuantumCircuit` creates circuits with
two data qubits and one ancilla. CNOT gates collect ZZ parity on the ancilla;
Hadamard basis changes enable XX parity measurement. We transpile the circuits
and execute them locally with Qiskit Aer's stabilizer simulator.

Six cases cover even, odd, and Bell-state inputs for both measurement bases.
Each demonstration case runs for **1,024 shots**. Even and Bell inputs return
ancilla bit `0` in all shots; odd inputs return `1`. These correspond to parity
eigenvalues +1 and -1. The X cases use the appropriate X-basis preparation.

**Show the judges:** a [ZZ circuit](challenge_results/ZZ_bell.png), an
[XX circuit](challenge_results/XX_bell.png), and the recorded counts in
[results.json](challenge_results/results.json). Explain how each circuit relates
to a scheduled board operation. The scheduler itself is classical Python;
these checks do not simulate encoded patches or validate physical lattice surgery.

### Methods and QEC accuracy — 20%

**Criterion:** Is it creative and accurately incorporating QEC elements?

The design idea is to **place patches according to the workload's measurement
boundaries**, rather than simply increase the board size. Vertical ZZ partners
and horizontal XX partners give each round separate auxiliary routes.

The method incorporates QEC-relevant structure: logical patches, X/Z boundaries,
ancilla-mediated joint parity measurements, and space-time resource accounting.
Routes must touch the correct boundaries, avoid occupied tiles, and respect
concurrent reservations. Dependencies prevent the second measurement round
from executing before the first finishes.

**Why these methods:** BFS gives exact shortest paths on the unweighted grid;
ordered greedy scheduling is deterministic and inexpensive; independent
validation catches invalid schedules. Stabilizer simulation fits the Clifford
circuits used here. These choices make the experiment reproducible and easy
to explain. The simplified model does not establish fault tolerance, and the
greedy scheduler is not generally optimal.

### Effect and insights — 30%

**Criterion:** Does it provide conceptual breakthroughs and further insights?

Our demonstrated insight is that **workload-aware placement can improve both
space and time**, while more workspace alone can make total space-time cost
worse. The spacious layout saves one step over compact but increases tile-steps
from 60 to 105, or **75%**. The aligned layout instead reduces them to 18,
or **70% below compact**, without changing the workload.

The result is stronger than finding one favorable example: dependency constraints
establish a two-step lower bound, and exhaustive smaller-board checks establish
the nine-tile lower bound within the stated model. The aligned layout meets
both bounds. This is a verified insight for this experiment, not a claim of a
new general quantum-computing breakthrough or quantum advantage.

**Show the judges:** the three-layout comparison, the two-step diagram, and
the smaller-layout test in [test_optimizations.py](test_optimizations.py).
Explain that the separate Python speedups improve experiment efficiency;
they do not reduce logical measurement time. A useful next investigation is
whether the advantage persists across other workloads and more realistic costs.

### Presentation and design justification — 40%

**Criterion:** Can the participants explain their methods succinctly and justify
their design choice?

Lead with the fixed workload and the 60-to-18 tile-step result. Then use the
[aligned-layout diagram](challenge_results/workload_aligned_schedule.png) to
show exactly which two operations run in each step. Define tile-steps before
using the metric, and keep software milliseconds separate from logical steps.

For a short presentation, follow this order:

1. **Problem:** perform the same four measurements with less space and time.
2. **Method:** arrange partners by boundary type; route and schedule without conflicts.
3. **Evidence:** compare all three layouts and show the Qiskit parity results.
4. **Justification:** explain the two lower bounds, the algorithm choices, and
   why all board tiles—including idle tiles—count toward area.
5. **Limits:** state the fixed-placement assumptions, workload specialization,
   and absence of a noise or hardware model.

**Suggested closing statement:** “For this fixed workload, matching patch
placement to measurement boundaries reduced area by 40% and elapsed steps by
50%, cutting tile-steps by 70%. Independent checks establish optimality within
our restricted model, and Qiskit verifies the representative parity outcomes.”

The strongest presentation explains why the result occurs and where it applies,
rather than only listing percentages. These points map the evidence to the
rubric; they do not guarantee a particular score.

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
