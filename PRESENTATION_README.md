# Presentation plan: Surface-Code Layout Optimization

This is the checklist for what to put in the presentation. The matching spoken
script is in [SPEAKER_NOTES.md](SPEAKER_NOTES.md).

**Suggested format:** seven slides, approximately six minutes, plus questions.
Timings are planning estimates; rehearse and adjust to the event's actual limit.

**Central message:** Matching patch placement to a fixed measurement workload
reduced space-time volume by 70% versus the original compact layout. We verified
the resource bounds within our restricted model, checked representative quantum
parities with Qiskit, and improved the classical implementation separately.

## 1. Grading criteria and required evidence

| Criterion | What the presentation must establish | Evidence to show | Slides |
|---|---|---|---|
| **Qiskit — 10%** | Qiskit performs a meaningful quantum check connected to the board operations. | ZZ and XX circuits; six ideal cases; 1,024 shots per case; expected counts. | 3 |
| **Methods — 20%** | The method is creative for this task and uses QEC concepts accurately. | Boundary-aware placement; ancilla-mediated parity; BFS routing; dependency/conflict handling; explicit model. | 1, 2, 3, 5 |
| **Effect — 30%** | The result yields an insight supported by a fair comparison. | Identical workload; 60/105/18 tile-steps; 70% improvement; scoped lower bounds; explanation of why placement matters. | 4, 5 |
| **Presentation — 40%** | The team explains the result clearly and justifies its choices. | Readable diagrams, defined units, a consistent story, stated trade-offs, and defensible answers. | All |

Presentation quality applies throughout; the 40% weight does not mean dedicating
40% of the talk to a slide about presentation. This plan addresses the rubric
but does not guarantee a particular score.

## 2. Slide-by-slide content

### Slide 1 — The problem and fixed workload

**Time:** 35 seconds. **Purpose:** define what is being optimized.

Include:

- Title: **Surface-Code Layout Optimization** and the team members' names.
- Question: **Can better placement reduce both space and measurement time?**
- Workload: `ZZ(A,B)` and `ZZ(C,D)` → `XX(B,C)` and `XX(A,D)`.
- Both second-round measurements wait for both first-round measurements.
- Definitions: space = board tiles; time = abstract steps;
  **tile-steps = tiles × steps**.

Show the workload as two rounds with an arrow between them. State that every
layout executes exactly these same four measurements. Avoid opening with Python
benchmarks before the audience understands the challenge objective.

### Slide 2 — Model, layout idea, and method

**Time:** 50 seconds. **Purpose:** explain the method and assumptions.

Use [workload_aligned_schedule.png](challenge_results/workload_aligned_schedule.png).

Include a small legend:

- Yellow A-D tiles = logical data patches.
- Solid top/bottom edges = Z boundaries; dotted left/right edges = X boundaries.
- Teal/orange = auxiliary paths; white = idle workspace that still counts.
- Each panel = a later step on the same board.

Explain the idea: **vertical ZZ partners and horizontal XX partners create
disjoint routes within each round**.

Include three method labels: **shortest-path BFS → ordered greedy scheduling →
independent validation**.

State the essential assumptions visibly, even if in smaller text:

- Fixed, single-tile patches with fixed X/Z orientation on a rectangular board.
- Nonempty auxiliary paths; simultaneous measurements cannot share data or paths.
- One step per joint measurement regardless of route length; no extra
  preparation/release cost; incidental boundary contacts are inactive.

Justification: BFS matches the unweighted grid; greedy scheduling is inexpensive
and deterministic. It is not generally a globally optimal scheduler.

### Slide 3 — What Qiskit contributes

**Time:** 60 seconds. **Purpose:** demonstrate meaningful quantum integration.

Place these two circuits side by side:

- [ZZ_bell.png](challenge_results/ZZ_bell.png).
- [XX_bell.png](challenge_results/XX_bell.png).

Label q0/q1 as data and q2 as ancilla. Explain that the two parity CNOTs collect
ZZ information; H gates around that block enable XX measurement. Distinguish
the Bell-preparation gates before the barrier from measurement logic after it.

Include this compact results table:

| Input case | ZZ result | XX result |
|---|---|---|
| Even parity in the relevant basis | `0`: 1,024 shots | `0`: 1,024 shots |
| Odd parity in the relevant basis | `1`: 1,024 shots | `1`: 1,024 shots |
| Bell state | `0`: 1,024 shots | `0`: 1,024 shots |

Add: **0 ↔ eigenvalue +1; 1 ↔ eigenvalue -1**.

Mention `QuantumCircuit`, transpilation, and local Qiskit Aer stabilizer
simulation. These are Clifford circuits; no hardware job is required.

Required qualification: **representative three-qubit parity checks, not a full
encoded lattice-surgery simulation**. The classical scheduler does not run on
a quantum processor. The printed `0` beside a circuit's measurement arrow is
the classical-bit index, not an experimental outcome.

### Slide 4 — Results: the same workload, three layouts

**Time:** 70 seconds. **Purpose:** make the main effect unmistakable.

Display this table prominently:

| Layout | Tiles | Steps | Tile-steps |
|---|---:|---:|---:|
| Original compact | 15 | 4 | 60 |
| Original spacious | 35 | 3 | 105 |
| Workload-aligned | **9** | **2** | **18** |

Show readable schedule images, using a progressive reveal or enlarging one at
a time if all three would be too small:

- [compact_schedule.png](challenge_results/compact_schedule.png): four sequential operations.
- [spacious_schedule.png](challenge_results/spacious_schedule.png): concurrent ZZ, separate XX steps.
- [workload_aligned_schedule.png](challenge_results/workload_aligned_schedule.png): two concurrent operations in each of two steps.

Call out the comparison against **original compact**, with the baseline named:

> **40% less area · 50% fewer steps · 70% fewer tile-steps**

Explain the trade-off in the spacious baseline: it saves one step but increases
tile-steps by 75%. The aligned placement improves both dimensions. This is a
logical-resource result; milliseconds and Python memory do not belong in this table.

### Slide 5 — Why this result matters, and the bounds

**Time:** 50 seconds. **Purpose:** substantiate the insight and optimality scope.

Use three statements:

1. **Placement should match the measurement workload:** extra workspace alone
   did not yield the best space-time volume.
2. **Time lower bound:** two dependent rounds require at least two steps.
3. **Area lower bound:** an independent BFS rejects every one of 4,104 labeled
   placements on smaller eligible rectangular boards because at least one
   required operation is individually unroutable.

Add that one-row/column boards lack the required Z/X ports, and boards with
fewer than four tiles cannot hold the data patches.

Conclusion: **9 tiles and 2 steps achieve both lower bounds under our model**.
The corresponding minimum product is 18 tile-steps.

Keep the scope statement visible: **fixed patches, fixed boundary orientation,
rectangular boards, nonempty auxiliary paths, unchanged workload**.

Do not call this a universal placement algorithm, a full-game optimum, a quantum
advantage result, or a new general breakthrough in fault-tolerant computing.

### Slide 6 — Efficient implementation and correctness evidence

**Time:** 55 seconds. **Purpose:** support the method without distracting from
the main logical-resource result.

Explain these changes in plain language:

- Occupancy sets avoid scanning every patch during routing.
- Ordered ready lists avoid sorting all waiting operations each round.
- Streaming validation avoids repeated completed-set and path copies.
- Grid lines replace one graphics object per empty tile.

Show only a few representative **second-pass** benchmarks:

| Component fixture | Runtime improvement | Peak Python memory |
|---|---:|---:|
| Large-board routing | About 2.0× faster | Unchanged |
| 300 contending operations | About 3.1× faster | 33% lower |
| Render/save a 24×24 board | About 5.6× faster | 86% lower |

Caption: **Compared with the already-optimized version; best of five timings;
Python allocation tracking, not total process memory. Not end-to-end speedups.**

Include the correctness evidence:

- **11 tests pass normally and under `-O`.**
- 1,600 independent route comparisons and 300 randomized schedule comparisons.
- 4,104 smaller-layout checks; corrupt schedules rejected.
- Six ideal parity cases pass; full-run JSON/CSV remain unchanged by the latest
  software refinements.

The area enumeration supports the logical bound; the route/schedule comparisons
support behavior preservation. Neither is a hardware noise test.

### Slide 7 — Trade-offs, limits, and conclusion

**Time:** 40 seconds. **Purpose:** justify the selected balance and finish clearly.

Include:

- **Recommended point:** the 9-tile layout plus exact BFS, ordered greedy
  scheduling, streamed validation, and line-based drawing.
- **Main trade-offs:** workload specialization; dependency-graph storage; more
  bookkeeping code; no general greedy-scheduler optimality guarantee.
- **Not modeled:** movement/rotation, direct adjacent-patch surgery, physical
  noise, decoding, code distance, or hardware execution time.
- **Next step:** test broader workloads and more realistic operation costs.

Finish with:

> **Better placement reduced tile-steps by 70%; verified software refinements
> reduced computation overhead without changing tested results.**

## 3. Presentation checklist

- [ ] Every number names its baseline and unit.
- [ ] All layouts use the same workload and dependency order.
- [ ] White/idle tiles are included in area; the aligned board's center counts.
- [ ] At least one board diagram is explained, not merely displayed.
- [ ] At least one Qiskit circuit and its actual counts are explained.
- [ ] A tile is described as a logical resource, not one physical qubit.
- [ ] The nine-tile certificate is scoped to the implemented model.
- [ ] Software benchmarks are separate from logical resource improvements.
- [ ] No claim of quantum advantage, noise resilience, or hardware fault tolerance.
- [ ] Each member can explain the contribution and answer the main questions.
- [ ] Diagrams remain readable from the back of the room.
- [ ] Rehearse against the actual time limit; do not try to read this file aloud.

## 4. Optional backup material

Keep these available for questions rather than crowding the main slides:

- Detailed complexity: route O(A) expected time/space after occupancy caching;
  graph storage O(M + D); scheduler retries can still be quadratic.
- Binary rank: packed XOR elimination in [gf2.py](gf2.py); this improves lab
  utilities and is separate from the board layout result.
- [results.json](challenge_results/results.json): exact scheduled paths and counts.
- [refinement_benchmarks.json](challenge_results/refinement_benchmarks.json): timings,
  memory measurements, and baseline revision.
- [test_optimizations.py](test_optimizations.py): independent BFS and exhaustive
  smaller-layout checks.
- The six circuit images and all three schedule images in `challenge_results/`.

For the complete explanation, use [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md).

## 5. Demo preparation

Run the following from the repository directory in PowerShell before presenting:

```powershell
.\qiskit-env\Scripts\python.exe -B -m unittest test_optimizations -v
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py
```

If showing a live numerical run, use:

```powershell
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py --no-plots --output demo_results
```

Keep the generated images available as a fallback. A live benchmark is optional;
the measured results already have reproducible source and saved output.
