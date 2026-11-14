# Speaker notes: Surface-Code Layout Optimization

These notes correspond to the seven slides in
[PRESENTATION_README.md](PRESENTATION_README.md). The target is approximately six
minutes. Rehearse the script and shorten or expand it for your speaking pace.

Bracketed directions are actions for the presenter, not words to read aloud.

## Slide 1 — The problem and fixed workload

**Target: 35 seconds.**

“Our project asks whether better placement of logical-qubit patches can reduce
both space and measurement time.

We keep the computation fixed: first, ZZ measurements on A-B and C-D; then,
after both finish, XX measurements on B-C and A-D.

We measure space in board tiles and time in abstract measurement steps. Our
combined metric is tile-steps: board area multiplied by elapsed steps. Keeping
the workload identical lets us compare placements fairly.”

[Point to the two rounds and the dependency arrow.]

## Slide 2 — Model, layout idea, and method

**Target: 50 seconds.**

“In this diagram, yellow tiles are logical data patches. Solid horizontal edges
are Z boundaries; dotted vertical edges are X boundaries. Colored tiles are
auxiliary routes, and white tiles are idle space that still counts toward area.

Our idea is to arrange ZZ partners vertically and XX partners horizontally, so
each round can use two disjoint routes.

The software uses breadth-first search for shortest paths, a deterministic
greedy scheduler, and an independent validator. We chose these because they
are inexpensive and straightforward to check.

The model keeps patches fixed and assigns one step to each joint measurement,
regardless of route length. It assumes no extra preparation or release cost.
These assumptions define the scope of our results.”

[Point to a solid boundary, a dotted boundary, and a colored auxiliary tile.
Emphasize that the two panels reuse the same board.]

## Slide 3 — What Qiskit contributes

**Target: 60 seconds.**

“Qiskit checks the quantum measurement building blocks represented by our board
operations. These circuits have two data qubits and one ancilla.

Before the barrier, a Hadamard and a CNOT prepare a Bell state. After the
barrier, two CNOTs collect the data qubits' Z parity on the ancilla. Measuring
that ancilla gives the ZZ result. For XX, Hadamard gates change the data's basis
around the parity circuit.

We construct and transpile the circuits in Qiskit and run them locally using
Aer's stabilizer simulator. We test even, odd, and Bell inputs for both bases,
with 1,024 shots per case. Even and Bell cases return zero; odd cases return one,
matching the expected parity eigenvalues.

This demonstrates representative parity outcomes. It does not simulate fully
encoded surface-code patches or fault-tolerant lattice surgery.”

[Point to preparation, then the parity CNOTs, then the ancilla readout. The
small printed zero by the arrow labels classical bit zero; use the results
table to show the actual outcomes.]

## Slide 4 — Results: the same workload, three layouts

**Target: 70 seconds.**

“The original compact board has 15 tiles and takes four steps. Its two ZZ
measurements reuse the middle corridor in separate steps, and the scheduler
also separates the XX measurements. That gives 60 tile-steps.

The spacious board has 35 tiles. Separate corridors allow the ZZ pair to run
together, reducing the schedule to three steps. But 35 times three is 105:
space-time volume actually increases by 75 percent compared with compact.

Our aligned board uses nine tiles. In the first step, the two vertical ZZ pairs
use separate middle tiles. In the second, the horizontal XX pairs use separate
top and bottom tiles. The center is unused, but we still count it.

The result is 18 tile-steps. Relative to compact, that is 40 percent less area,
50 percent fewer steps, and a 70 percent reduction in tile-steps. Placement
improves both resources for this workload.”

[Walk through the table, then point to the two paths in each aligned panel.
Pause on 60 versus 18.]

## Slide 5 — Why this result matters, and the bounds

**Target: 50 seconds.**

“The insight is that placement should match the measurement workload. Adding
workspace alone did not produce the best space-time result.

We can also justify the selected point. The dependency structure requires at
least two steps. For area, an independent breadth-first search checks all 4,104
placements on smaller eligible rectangular boards. Every placement makes at
least one required measurement individually unroutable. One-row and one-column
boards lack the required boundary access.

Our nine-tile, two-step layout therefore reaches both lower bounds within this
model. This is not a claim that the greedy algorithm is always optimal, or
that nine tiles is a minimum under every rule of the full surface-code game.”

[Keep the scope statement visible while saying “both lower bounds.”]

## Slide 6 — Efficient implementation and correctness evidence

**Target: 55 seconds.**

“We separately improved the classical implementation. Occupancy sets avoid
scanning every patch. Ordered ready lists avoid repeatedly sorting waiting
operations. Streaming validation avoids copying paths and growing sets, and
grid lines replace hundreds of background rectangle objects.

Compared with the already-optimized version, our latest benchmarks show about
twice-as-fast large-board routing, three-times-as-fast contended scheduling,
and 5.6-times-as-fast diagram generation. Scheduling and rendering also use
less peak Python memory. These are component benchmarks, not reductions in
logical measurement time or guaranteed whole-program speedups.

All 11 regression tests pass normally and with Python optimization enabled.
They include independent routing comparisons, randomized schedules, and
corrupted-output checks. The full demonstration still passes all six quantum
parity cases, and its numerical outputs are unchanged by these refinements.”

[Point to the benchmark caption. Do not imply all program components improved
by the largest listed factor.]

## Slide 7 — Trade-offs, limits, and conclusion

**Target: 40 seconds.**

“The balance we recommend is the workload-aligned layout with exact BFS,
ordered greedy scheduling, and independent validation.

The main trade-offs are specialization to these pairings and additional
dependency bookkeeping. Other workloads can favor different placements, and
the general scheduler remains heuristic. Our model also excludes physical
noise, decoding, movement, and hardware timing.

The next step is testing more workloads and realistic operation costs.

Our main result is that better placement cut tile-steps by 70 percent. We also
reduced classical computation overhead while preserving the tested behavior.”

[Finish on the aligned-layout diagram and the 60-to-18 comparison.]

## Questions and short answers

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
