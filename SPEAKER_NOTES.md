# Speaker notes: Surface-Code Layout Optimization

**Six slides. Target: 4:15; acceptable range: 4:00–4:30, excluding questions.**
Follow [PRESENTATION_README.md](PRESENTATION_README.md) for slide content.
Read only the quoted paragraphs. Bracketed cues are actions, not spoken text.
Rehearse at approximately 130 words per minute with brief diagram pauses;
actual duration depends on delivery. The Q&A below is backup, not part of the talk.

## Slide 1 — Problem and fixed workload

**30 seconds | 0:00–0:30**

“Our project asks whether better placement of logical-qubit patches can reduce
both space and measurement time.

Every layout runs the same workload: ZZ on A-B and C-D, followed by XX on B-C
and A-D. Both first-round measurements must finish before the second round.

We measure board area in tiles and elapsed time in abstract steps. Multiplying
them gives tile-steps, our combined resource metric.”

[Point to the dependency arrow.]

## Slide 2 — Diagram and method

**45 seconds | 0:30–1:15**

“Yellow tiles are logical data patches. Solid horizontal edges are Z boundaries;
dotted vertical edges are X boundaries. Colored tiles are auxiliary routes.
White tiles are idle, but still count toward area.

Our idea is to place ZZ partners vertically and XX partners horizontally, so
each round has two disjoint routes.

We use breadth-first search for shortest paths, ordered greedy scheduling,
and independent validation. These are deterministic and inexpensive to check.

The model keeps patches fixed. Each joint measurement costs one step, regardless
of path length, with no additional preparation or release cost.”

[Point to one boundary of each type, then the two routes in each panel.]

## Slide 3 — What Qiskit contributes

**50 seconds | 1:15–2:05**

“Qiskit verifies the measurement building blocks represented by these board
operations. Each circuit has two data qubits and one ancilla.

In the ZZ circuit, two CNOTs collect joint parity on the ancilla. Hadamard gates
change the basis for XX measurement. Gates before the barrier prepare the input.

We construct and transpile the circuits with Qiskit, then run Aer's local
stabilizer simulator. Six cases cover even, odd, and Bell inputs for both bases,
with 1,024 shots each. Even and Bell cases return zero; odd cases return one,
as expected.

These are representative parity checks, not a fully encoded fault-tolerant
lattice-surgery simulation.”

[Point to the ancilla and the actual results table. The printed zero by the
measurement arrow is a classical-bit index, not an outcome.]

## Slide 4 — Results and insight

**60 seconds | 2:05–3:05**

“The compact layout uses 15 tiles and four steps: 60 tile-steps. The spacious
layout uses 35 tiles and three steps: 105 tile-steps. Extra space saves time,
but increases total space-time volume.

Our aligned layout uses nine tiles and two steps: 18 tile-steps. Its center
remains idle but is counted. Compared with compact, that means 40 percent less
area, 50 percent fewer steps, and 70 percent fewer tile-steps.

The insight is to match placement to the workload, rather than simply add space.

Two dependent rounds require at least two steps. Independent checks reject all
4,104 smaller eligible placements; one-row and one-column boards lack the
required ports. Our layout therefore reaches both area and time lower bounds
within this restricted model.”

[Pause on 60 versus 18. Keep “within this model” visible.]

## Slide 5 — Implementation and testing

**40 seconds | 3:05–3:45**

“We also removed redundant software work through occupancy sets, ordered ready
lists, streaming validation, and simpler grid drawing.

Against the previously optimized version, a contended scheduling benchmark was
about three times faster with 33 percent less peak Python memory. This is a
component benchmark, separate from logical measurement time.

All 11 tests pass normally and with Python optimization enabled. They include
1,600 independent route comparisons, 300 randomized schedules, and invalid-output
checks. The six quantum parity cases also pass, and the latest software changes
preserve the numerical results.”

[If running late, omit the benchmark paragraph; retain the testing evidence.]

## Slide 6 — Trade-offs and conclusion

**30 seconds | 3:45–4:15**

“The main trade-offs are specialization to these pairings and extra dependency
bookkeeping. The scheduler remains greedy for other workloads. We do not model
physical noise, decoding, movement, or hardware timing.

Next, we would test broader workloads and more realistic costs.

Our contribution is a verified placement improvement: 70 percent fewer tile-steps
than compact, plus lower classical computation overhead while preserving the
tested behavior.”

[Finish on the aligned diagram and the 70% result.]

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
