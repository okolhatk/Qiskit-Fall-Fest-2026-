# Presentation plan: Surface-Code Layout Optimization

**Format: six slides, 4:00–4:30 total. Target: 4:15, excluding questions.**
The matching spoken script is in [SPEAKER_NOTES.md](SPEAKER_NOTES.md).
Use the short script rather than reading every slide annotation aloud.

**Central message:** workload-aware placement reduced tile-steps by 70%
compared with the original compact layout, with bounds established within our
restricted model and representative parity outcomes verified using Qiskit.

## Timing and grading coverage

| Slide | Topic | Duration | Cumulative time | Main criteria |
|---|---|---:|---|---|
| 1 | Problem and fixed workload | 30 seconds | 0:00–0:30 | Methods, presentation |
| 2 | Diagram and method | 45 seconds | 0:30–1:15 | Methods, presentation |
| 3 | Qiskit integration | 50 seconds | 1:15–2:05 | Qiskit, methods |
| 4 | Results and insight | 60 seconds | 2:05–3:05 | Effect, presentation |
| 5 | Implementation and testing | 40 seconds | 3:05–3:45 | Methods, evidence |
| 6 | Trade-offs and conclusion | 30 seconds | 3:45–4:15 | Effect, presentation |

All four grading categories remain covered:

- **Qiskit — 10%:** actual circuits, simulator use, and measured parity outcomes.
- **Methods — 20%:** boundary-aware placement, correct parity interpretation,
  routing/scheduling choices, assumptions, and independent validation.
- **Effect — 30%:** fixed-workload comparison, 70% improvement, explanation of
  why placement matters, and scoped lower bounds.
- **Presentation — 40%:** readable diagrams, defined metrics, justified choices,
  a concise narrative, and honest limitations throughout.

## Slide 1 — Problem and fixed workload

**30 seconds.** Put these on the slide:

- Title and team names.
- Question: **Can placement reduce both space and measurement time?**
- `ZZ(A,B), ZZ(C,D)` → `XX(B,C), XX(A,D)`.
- Both second-round measurements wait for both first-round measurements.
- **Tile-steps = board tiles × elapsed logical steps.**

Explain that all layouts run the same four measurements. Tiles are logical
resources, not individual physical qubits. Do not open with software benchmarks.

## Slide 2 — Diagram and method

**45 seconds.** Use the
[aligned-layout diagram](challenge_results/workload_aligned_schedule.png).

Keep the legend short:

- Yellow: data patches; colored tiles: auxiliary routes; white: idle workspace.
- Solid horizontal edges: Z boundaries; dotted vertical edges: X boundaries.
- Each panel: a later step on the same board.

Explain the design: vertical ZZ partners and horizontal XX partners allow two
nonoverlapping measurements per round. Idle tiles still count toward area.

Show: **BFS shortest paths → ordered greedy scheduler → independent validator**.
Justify BFS with the unweighted grid and greedy scheduling with low cost and
deterministic operation order.

Keep this model caption visible: **Fixed single-tile patches; fixed boundaries;
rectangular board; nonempty auxiliary paths; one step per measurement regardless
of length; no extra preparation/release cost.** Incidental contacts are inactive;
concurrent operations cannot share data patches or auxiliary tiles.

## Slide 3 — What Qiskit contributes

**50 seconds.** Show [ZZ_bell.png](challenge_results/ZZ_bell.png) and
[XX_bell.png](challenge_results/XX_bell.png) side by side.

Label q0/q1 as data and q2 as ancilla. Point out the parity CNOTs and the
Hadamard basis changes for XX. Preparation is before the barrier.

Include this results summary:

| Input case | ZZ outcome | XX outcome |
|---|---|---|
| Even parity in the relevant basis | All 1,024 shots: 0 | All 1,024 shots: 0 |
| Odd parity in the relevant basis | All 1,024 shots: 1 | All 1,024 shots: 1 |
| Bell state | All 1,024 shots: 0 | All 1,024 shots: 0 |

Add: **0 = eigenvalue +1; 1 = eigenvalue -1**.
Mention circuit construction, transpilation, and local Aer stabilizer simulation.

Required qualification: **Representative parity checks, not encoded
fault-tolerant lattice surgery.** The board scheduler is classical Python.
The small zero beside the measurement arrow labels classical bit zero; use
saved counts, not that label, as evidence of outcomes.

## Slide 4 — Results and insight

**60 seconds.** Keep this table large and readable:

| Layout | Tiles | Steps | Tile-steps |
|---|---:|---:|---:|
| Original compact | 15 | 4 | 60 |
| Original spacious | 35 | 3 | 105 |
| Workload-aligned | **9** | **2** | **18** |

Callout: **Versus compact: 40% less area · 50% fewer steps · 70% fewer tile-steps.**

Keep the aligned diagram visible beside the table or reveal it again. There
is not enough time to walk through every panel of all three layout diagrams;
keep the [compact](challenge_results/compact_schedule.png) and
[spacious](challenge_results/spacious_schedule.png) diagrams as backup.

Explain the insight: extra space saved a step but increased tile-steps to 105;
matching placement to the workload instead improved both space and time.

State the scoped bounds concisely:

- Two dependent rounds require at least two steps.
- Independent routing checks reject all 4,104 placements on smaller eligible
  rectangular boards; one-row/column boards lack the required ports.
- **Nine tiles and two steps attain both bounds within this model.**

The aligned board's idle center counts. This is not a full-game or hardware optimum.

## Slide 5 — Implementation and testing

**40 seconds.** Put the implementation ideas in one line:

**Occupancy sets · ordered ready lists · streaming validation · grid-line drawing**

Use one software benchmark in the spoken presentation:

> **300 contending operations: about 3.1× faster, 33% less peak Python memory.**

Caption: **Second pass versus the already-optimized version; local component
benchmark, best of five timings; excludes native memory. Not a logical-time gain.**

Evidence bullets:

- **11 tests pass normally and under `-O`.**
- **1,600** independent route comparisons; **300** randomized schedule comparisons.
- Smaller-layout enumeration and corrupt-schedule checks.
- Six parity cases pass; JSON/CSV results unchanged by the latest software refinements.

Do not explain every optimization or benchmark here. Keep detailed complexity,
rank calculation, and other timings for questions.

## Slide 6 — Trade-offs and conclusion

**30 seconds.** Include:

- **Trade-offs:** workload-specific placement, dependency bookkeeping, and a
  greedy scheduler that is not generally optimal.
- **Scope:** no noise, decoding, code distance, movement/rotation, direct
  adjacent-patch surgery, or hardware timing model.
- **Next step:** broader workloads and realistic operation costs.

Close with:

> **Better placement cut tile-steps by 70%; software refinements reduced overhead
> while preserving tested results.**

## Rehearsal and time control

- Rehearse toward **4:15**, giving a 15-second margin before 4:30.
- Timings include brief pointing and slide transitions; they are estimates.
- Aim for approximately 130 spoken words per minute, with short diagram pauses.
- If behind schedule, skip the spoken software benchmark on slide 5; preserve
  the test evidence, Qiskit result, main comparison, and model limitations.
- If comfortably ahead, pause at the result table rather than adding another topic.
- Do not run a live benchmark or full demo inside the timed talk. Use prepared
  images and saved results; demonstrate the code afterward if requested.
- Questions and backup material are outside the 4:00–4:30 presentation.

## Final checklist

- [ ] Each number has a clear baseline and unit.
- [ ] Logical tile-steps are separate from software runtime and memory.
- [ ] The aligned board and at least one circuit are actually explained.
- [ ] The Qiskit results and lower-bound scope are stated accurately.
- [ ] Slides are readable; the script fits 4:00–4:30 in rehearsal.
- [ ] No claim of quantum advantage, hardware fault tolerance, or general optimality.

## Backup evidence and preparation

Keep these available for questions:

- [SPEAKER_NOTES.md](SPEAKER_NOTES.md): spoken script and judge Q&A.
- [PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md): full methods and complexity.
- [results.json](challenge_results/results.json): exact routes and quantum counts.
- [refinement_benchmarks.json](challenge_results/refinement_benchmarks.json): timings and memory.
- [test_optimizations.py](test_optimizations.py): independent checks and area certificate.

Before presenting, run from the repository directory in PowerShell:

```powershell
.\qiskit-env\Scripts\python.exe -B -m unittest test_optimizations -v
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py
```
