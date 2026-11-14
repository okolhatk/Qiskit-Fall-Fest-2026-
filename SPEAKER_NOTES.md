# Speaker notes: Surface-Code Layout Optimization

**Six slides. Target: 4:15; acceptable range: 4:00–4:30, excluding questions.**
Follow [PRESENTATION_README.md](PRESENTATION_README.md) for slide content.

## How to use these expanded notes

Each slide has two layers:

1. **Timed script — say this:** read or paraphrase only the quoted paragraphs.
2. **Background — do not read during the timed talk:** explanations to help you
   understand the claims, rehearse naturally, and answer questions.

The timed script is **524 words**. At about 130 words per minute, it
leaves a small allowance for pointing and slide transitions within the target.
Numbers and technical terms may take longer to say than their word counts suggest;
rehearse aloud with a timer. Added background and Q&A do not belong in the timed talk.

The slide checkpoints remain **0:30, 1:15, 2:05, 3:05, 3:45, and 4:15**.
If running late, skip the slide 5 benchmark paragraph; keep the result, Qiskit
integration, verification evidence, and model limitations. Do not speed-read
extra background to fit it in.

## Slide 1 — Problem and fixed workload

**30 seconds | 0:00–0:30**

### Timed script — say this

“Our project asks whether arranging logical-qubit patches differently can save both space and time. A patch represents encoded quantum information, not one physical qubit.

We compare the same workload: ZZ measurements on A-B and C-D, followed by XX on B-C and A-D. The second round must wait for the first.

Our combined metric is tile-steps: total board area multiplied by the number of measurement rounds.”

**Delivery cue:** Point to the arrow between rounds when saying “must wait.” Then point to the tile-steps formula. Do not explain every quantum term yet.

### Background — do not read during the timed talk

- **Why the workload stays fixed:** changing the operations would make it unclear whether an improvement came from placement or from doing less work. Only the layouts change in this comparison.
- **Why use a product:** latency alone hides the cost of allocating more workspace. Tile-steps counts the entire board for every elapsed step, including idle space.
- **What the dependency means:** both first-round measurements must finish before either second-round operation starts. The code preserves that order; it does not infer which operations may be reordered.
- **Avoid:** calling a tile a physical qubit or a logical step a measured number of microseconds.

## Slide 2 — Diagram and method

**45 seconds | 0:30–1:15**

### Timed script — say this

“Yellow tiles are data patches. Solid horizontal edges expose Z boundaries; dotted vertical edges expose X boundaries. Colored tiles provide auxiliary measurement paths. White tiles are unused but still count.

Placing ZZ partners vertically and XX partners horizontally gives each round two nonoverlapping paths, allowing simultaneous measurements.

Breadth-first search finds shortest paths by exploring nearby cells first. Our greedy scheduler reserves available paths in input order; a separate validator checks the result.

Patches remain fixed. Every joint measurement costs one step regardless of path length, with no additional preparation or release cost.”

**Delivery cue:** Trace A-B and C-D in step 1, then B-C and A-D in step 2. Point to the relevant solid or dotted edge. These are two snapshots of the same board.

### Background — do not read during the timed talk

- **Why orientation matters:** a vertical pair can meet through its facing north/south Z boundaries; a horizontal pair can meet through its east/west X boundaries. The pairing pattern matches the workload.
- **What “nonoverlapping” requires:** concurrent operations must share neither data patches nor auxiliary tiles. Different route colors identify operations, not X versus Z or an error state.
- **What BFS guarantees:** on this unweighted grid, it finds a shortest available route. It does not guarantee that choosing this route produces the best overall schedule for every workload.
- **Why keep the validator separate:** a scheduling bug should not be accepted merely because the scheduler generated the output. Validation checks geometry, dependencies, conflicts, and completeness independently.
- **Model boundary:** incidental contact with another patch is assumed inactive. Direct adjacent-patch surgery without an auxiliary path is not implemented.

## Slide 3 — What Qiskit contributes

**50 seconds | 1:15–2:05**

### Timed script — say this

“Qiskit checks the quantum operation behind our routes. Each circuit has two data qubits and an ancilla: an auxiliary qubit that collects parity information.

Two CNOTs collect ZZ parity without separately measuring the data qubits. Hadamard gates change the basis for XX. Gates before the barrier prepare the input.

We build and transpile these circuits, then run Qiskit Aer's stabilizer simulator. Six cases test even, odd, and Bell inputs in both bases, with 1,024 shots each. All even and Bell outcomes are zero; all odd outcomes are one, matching expectations.

These checks verify representative parity outcomes, not encoded fault-tolerant lattice surgery.”

**Delivery cue:** Point to q0/q1, then q2 and its meter. Show the two parity CNOTs after the barrier and the additional H gates in the XX circuit. Read outcomes from the counts table, not the small zero by the measurement arrow.

### Background — do not read during the timed talk

- **Parity in everyday terms:** in the Z basis, equal bits (`00` or `11`) have even parity; different bits (`01` or `10`) have odd parity. The ancilla reveals that relationship rather than the individual data values.
- **Outcome convention:** ancilla `0` corresponds to the measured observable's eigenvalue +1; `1` corresponds to -1. XX uses the analogous parity in the X basis, so the even/odd input preparation changes accordingly.
- **Bell preparation:** H on q0 followed by a CNOT from q0 to q1 creates the Bell input before the barrier. This particular Bell state has eigenvalue +1 for both ZZ and XX.
- **Why repeated outcomes are expected:** these chosen inputs are parity eigenstates and the simulation is ideal. A shot is one repeated circuit execution; 1,024 equal results do not demonstrate noise resilience.
- **Why this simulator:** the representative circuits contain Clifford operations, which suit stabilizer simulation. The board scheduler remains classical Python.
- **Evidence limit:** checking these outcomes alone does not prove arbitrary-state preservation or a physical implementation of a routed encoded patch. The diagram's classical-bit index is not a recorded measurement result.

## Slide 4 — Results and insight

**60 seconds | 2:05–3:05**

### Timed script — say this

“Compact uses 15 tiles and four steps: 60 tile-steps. Spacious uses 35 tiles and three steps: 105 tile-steps. More workspace reduces waiting but increases the total space-time cost.

Our aligned layout uses nine tiles and two steps: 18 tile-steps, including the idle center. Against compact, that saves 40 percent of the area, 50 percent of the steps, and 70 percent of the tile-steps.

The insight is that placement should match the measurement workload.

Two dependent rounds require at least two steps. Independent checks find at least one unroutable measurement in every one of 4,104 smaller eligible placements. Single-row or single-column boards lack required ports. Thus, both lower bounds are reached within our restricted model.”

**Delivery cue:** Move down the table in order: compact, spacious, aligned. Pause briefly on 60 → 18. Keep the words “within our restricted model” visible when discussing lower bounds.

### Background — do not read during the timed talk

- **Explain the mechanism if asked:** compact's ZZ pair competes for its middle corridor. Spacious separates those corridors, but its generated schedule still separates the XX pair. Aligned gives both rounds disjoint routes.
- **Check the percentages:** `(15−9)/15 = 40%`; `(4−2)/4 = 50%`; `(60−18)/60 = 70%`. Spacious increases tile-steps by `(105−60)/60 = 75%` relative to compact.
- **Why the area certificate is stronger than a greedy failure:** the independent BFS asks whether each measurement could route by itself. An individually impossible route cannot become possible merely by choosing a different concurrent schedule on the same fixed board.
- **What was enumerated:** all four-label placements on 2×2, 2×3, 3×2, 2×4, and 4×2 boards. One-row boards lack Z ports, one-column boards lack X ports, and fewer than four tiles cannot hold four distinct patches.
- **Exact scope:** rectangular boards, fixed single-tile patches, fixed boundary orientation, nonempty auxiliary paths, and this workload. No general optimality claim applies to rotations, moves, adjacent-patch surgery, or other workloads.

## Slide 5 — Implementation and testing

**40 seconds | 3:05–3:45**

### Timed script — say this

“We also reduced classical overhead. Occupancy sets replace repeated patch scans; ready lists avoid repeatedly sorting waiting operations; streaming validation avoids copying paths.

On 300 contending operations, scheduling was about three times faster with 33 percent less peak Python memory than the previously optimized version. This is a component benchmark, not quantum execution time.

All 11 tests pass normally and with Python optimization enabled, including 1,600 independent route comparisons and 300 randomized schedules. The quantum checks pass, and numerical outputs remain unchanged by these software refinements.”

**Delivery cue:** Point to the benchmark's baseline and the test totals. Emphasize “classical” and “component benchmark.” If behind schedule, omit the benchmark paragraph and retain the correctness evidence.

### Background — do not read during the timed talk

- **What the changes remove:** occupancy sets avoid searching all patch positions; ordered deferred lists avoid re-sorting the same waiting operations; validation avoids growing-set unions and duplicate path lists. Grid lines also replace individual background rectangles when drawing.
- **Complexity distinction:** occupancy caching reduced routing from O(A×P) to expected O(A), where A is area and P is patch count. The latest early-exit routing changes improve constants, not that worst-case bound. Scheduling still has potentially many retries under contention.
- **Memory scope:** the benchmark measures peak Python allocations separately from timing. It excludes native-library memory and does not represent physical-qubit usage or total process memory.
- **What the tests establish:** exact routes match an independent BFS; randomized schedules match the reference policy; invalid outputs are rejected. Explicit validation stays active under `-O`, which can disable ordinary Python assertions.
- **Keep the baselines separate:** the 70% tile-step gain compares layouts against original compact. The latest software benchmark compares implementations against the already-optimized version. Neither is a hardware measurement.

## Slide 6 — Trade-offs and conclusion

**30 seconds | 3:45–4:15**

### Timed script — say this

“The main trade-off is specialization: a different measurement workload may need a different placement. Dependency tracking also needs extra bookkeeping, and greedy scheduling is not generally optimal.

We do not model physical noise, decoding, movement, or hardware timing. Those are next steps, alongside broader workloads.

Our result is a verified placement improvement: 70 percent fewer tile-steps than compact, with lower classical overhead and preserved tested behavior.”

**Delivery cue:** Return to the aligned diagram and the 70% callout. Finish the sentence, pause, and invite questions. Do not add backup material to fill time.

### Background — do not read during the timed talk

- **Why this is the selected balance:** the placement reaches the model's area and time lower bounds, so a more expensive global search cannot improve those bounds for this exact workload. The software refinements remove redundant work without approximate routing or fewer shots.
- **What still costs memory:** the scheduler stores dependency relationships. The newer representation lowers measured overhead, but graph storage remains proportional to operations and unique dependency edges.
- **Why the limitation matters:** a physical system needs a justified noise, timing, and error-correction model. Ideal parity checks and an abstract grid do not establish hardware fault tolerance.
- **Recommended next experiment:** keep the assumptions fixed while varying workloads and layouts; then introduce additional physical/game costs explicitly. This separates a broader placement effect from an effect caused by changing the rules.
- **Closing emphasis:** the result combines a scoped resource improvement, clear reasoning, and regression evidence. Avoid claiming a universal breakthrough or quantum advantage.

## Questions and short answers — outside the timed presentation


**Why can the two operations in a round run together?**

They use disjoint data patches and disjoint auxiliary tiles, and their
dependencies are already satisfied. Our model assumes those disjoint regions
can be controlled independently.

**Why can't all four operations run in one step?**

The workload explicitly requires both first-round operations to finish before
either second-round operation starts. We preserve that dependency order.

**How do you know the smaller layouts are impossible?**

We enumerate every four-label placement on 2x2, 2x3, 3x2, 2x4, and 4x2 boards.
An independent BFS finds at least one individually unroutable measurement in
each placement. One-row or one-column boards lack Z or X ports, respectively.
This is stronger than simply observing failure of a greedy concurrent schedule.

**Does “nine tiles” mean nine physical qubits?**

No. Tiles are abstract logical resources. The project does not select code
distance or calculate the number of physical qubits per patch.

**Are the colored auxiliary paths the CNOT wires in the circuit images?**

No. The board describes logical geometry and concurrency. The circuit images
check representative parity outcomes using two data qubits and an ancilla.
They are not a physical gate-by-gate implementation of each routed patch.

**Why use the stabilizer simulator?**

The representative circuits use Clifford operations, which suit stabilizer
simulation. Arbitrary non-Clifford gates or noise would require an appropriate
alternative. We do not claim a measured exponential speedup for these tiny
three-qubit checks.

**Why do all 1,024 shots give the same answer?**

The test inputs are eigenstates of the measured parity operator, and the
simulation is ideal. Deterministic results are expected for these cases.

**Does that prove the circuit works for every possible quantum input?**

The tests establish the expected outcomes for these representative inputs.
They do not alone prove arbitrary-state preservation or encoded surgery correctness.

**Did you demonstrate quantum advantage or fault tolerance?**

No. We demonstrated an abstract resource improvement, validated classical
schedules, and checked representative quantum measurement outcomes with Qiskit.

**What is creative about the method?**

We connect the workload's measurement pairings to the geometry of the available
boundaries. The important insight is supported by a fixed-workload comparison
and scoped lower bounds, rather than only showing a faster example.

**Why not use a more advanced global optimizer?**

For this fixed case, the layout already reaches the model's area and time lower
bounds. Global optimization would add complexity without improving these bounds.
It could still be useful when exploring other workloads and constraints.

**What are the main software trade-offs?**

Dependency tracking requires storage proportional to operations and dependency
edges, plus more bookkeeping code than a full scan. The latest implementation
reduces that overhead but does not remove it. The faster validation also raises
`ValueError` rather than relying on assertions.

**Why report tile-steps as well as time?**

The spacious baseline demonstrates the reason: fewer steps can require enough
extra area to increase total space-time volume. We report area, latency, and
their product so the trade-off remains visible.

## Presenter accuracy reminders

- Say **“within our restricted model”** when discussing minimum area or time.
- Say **“compared with original compact”** for the 70% tile-step reduction.
- Say **“compared with the already-optimized version”** for the latest software
  benchmark speedups. Do not multiply separate benchmark passes into a claimed measurement.
- Say **“peak Python allocations”**, not “total computer memory” or “qubit savings.”
- Explain that route colors identify concurrent operations, not measurement basis.
- Do not claim error correction or noise suppression from ideal parity counts.
- When unsure, refer to the saved outputs and state what was actually tested.
