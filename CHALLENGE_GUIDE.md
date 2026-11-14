# Surface-code layout experiment

Run from the repository directory in PowerShell:

```powershell
.\qiskit-env\Scripts\python.exe surface_code_challenge.py
```

The existing environment supplies Qiskit, Aer, Matplotlib and pylatexenc.
No IBM account, hardware jobs, or additional platform is required.
When copying the QEC notebooks to Colab or another folder, include `gf2.py`
alongside `lab4_util.py` and `qec_checkpoints.py`.

## Question

How does auxiliary workspace affect the time needed to perform a fixed
sequence of joint measurements on four logical patches?

The workload is ZZ on AB and CD, followed by XX on BC and AD. The latter
pair depends on both first-round measurements. Separate measurements within
a round act on disjoint data patches. All three layouts execute the same workload.

## Explicit model

- Each data patch occupies one tile. Z boundaries face north/south; X
  boundaries face east/west. Patches remain fixed.
- An auxiliary region is a connected, one-tile-wide path through empty tiles
  between the appropriate boundaries. Only its endpoint boundaries couple to
  data; incidental contact with other boundaries is assumed inactive.
- Every valid joint measurement takes one abstract game time step, independent
  of path length. Auxiliary preparation and release have zero additional cost
  in this restricted model. This is not a hardware timing estimate.
- Concurrent operations must have disjoint data patches and disjoint auxiliary
  tiles. The model assumes disjoint auxiliary regions can be controlled
  independently, including when neighboring one another.
- Board area includes every tile in the bounding rectangle, including idle
  workspace. Tile-steps means board area multiplied by elapsed steps.
- Routing uses breadth-first search. Scheduling greedily tries operations in
  their listed order; it is not an optimal routing or scheduling algorithm.
- There are no patch moves, rotations, Y measurements, magic states, noisy
  syndrome rounds, code-distance calculations, or decoder simulation.

These restrictions define our experiment. The complete game supports more
operations. Check a proposed physical implementation against the full rules:
https://pennylane.ai/demos/tutorial_game_of_surface_codes
and https://arxiv.org/abs/1808.02892.

## Results

For the unchanged four-operation workload:

- Original compact: 15 tiles, 4 steps, 60 tile-steps (1 operation/step).
- Original spacious: 35 tiles, 3 steps, 105 tile-steps (1.33 operations/step).
- Workload-aligned: 9 tiles, 2 steps, 18 tile-steps (2 operations/step).

The new layout places A/B on the left and D/C on the right. ZZ measurements
use the left/right middle tiles concurrently; XX measurements use the
top/bottom middle tiles concurrently. The central tile is idle but counted.
It halves elapsed steps and reduces area by 40% relative to compact, giving
70% fewer tile-steps. Relative to spacious it uses 74.3% less area and 82.9%
fewer tile-steps. It therefore dominates these two examples in this model.

The two dependency rounds require at least two steps, so this particular
schedule is time-optimal. This is NOT a proof of minimum area, global routing
optimality, or performance for arbitrary workloads. The placement was found
by checking the 24 assignments of four labels to board corners on several
small boards; the program stores the resulting layout, not a general optimizer.
Changing pairings, boundaries or preparation and movement costs can change
the result. Initial placement is free here; rearranging a running computation
would need explicit costs.

`challenge_results/` contains diagrams for every scheduled time step, six
Qiskit circuit images, a CSV comparison, and detailed JSON including paths.
The program validates boundary access, path continuity, occupancy, data
conflicts, dependencies and completeness before reporting a schedule.

The Qiskit component verifies ideal ZZ and XX measurements on representative
qubits for even, odd and entangled Bell inputs. Ancilla result 0 represents
eigenvalue +1; result 1 represents -1. This checks the quantum measurement
building block; it does not simulate encoded patches or fault-tolerant lattice
surgery. The board scheduler itself is classical Python.

## Make it your experiment

Edit `LAYOUTS` to change board dimensions or patch coordinates. Edit `WORKLOAD`
to change measurements and dependencies. Coordinates start at (0, 0) in the
upper left. Keep X/Z measurements only. Explicit dependencies are necessary
where measurement order matters; omitting them does not establish commutation.

Keep workload and assumptions fixed when comparing layouts. Explain both the
speed gain and extra area; a faster layout may consume more tile-steps. Do not
claim the greedy schedule is optimal or generalize from this one workload.

## Software complexity and trade-offs

These are classical computation costs, separate from logical tile-steps.
Let A be board area, P patch count, M operation count, D the number of unique
dependency edges, T scheduled steps, and R the total ready-operation visits
across all steps (R <= M*T).

- **Routing:** previously O(A*P) worst-case time because every occupancy query
  scanned all patch positions. An immutable occupancy set makes membership
  expected O(1), bringing BFS to expected O(A) time and O(A) search space.
  The layout adds O(P) storage and O(P) construction work. It snapshots the
  patch mapping to prevent stale cached occupancy; create a new Layout to move
  patches. BFS still returns a shortest path with the same tie-breaking.
- **Scheduling:** previously scans all M operations in every step and rebuilds
  dependency sets, costing O(T*(M+D)) overhead plus routing. Dependency-name
  validation also previously cost O(M*D). The ready set processes each edge
  once and sorts ready operations to preserve input order. New overhead is
  O(M+D+R*log(M+1)), plus at most O(R*A) routing. A chain improves from
  quadratic scanning to linear scheduling overhead. Contention can still make
  R quadratic; this is not an optimal scheduler. Extra dependency storage is
  O(M+D). Retained output paths cost O(M*A) in the worst case in both versions.
- **Binary rank:** the old dense elimination uses O(m^2*n) element work and
  copies m*n integer entries. The shared packed implementation validates and
  packs rows, then uses integer XOR. With rank r and integer word width w,
  elimination is O(m*r*ceil(n/w)) word work, plus O(m*n) input processing.
  Auxiliary storage for an existing NumPy input is O(r*ceil(n/w)+n) words
  including a row-sized conversion buffer. Python integers are arbitrary
  precision: XOR is not constant time. List input also needs an O(m*n) NumPy
  conversion. This remains Gaussian elimination, not a new subcubic algorithm.
  Packed storage is less readable, so randomized tests compare against an
  independent dense GF(2) implementation. Both lab and checkpoint call it.
- **Simulation:** the Surface-17 notebook explicitly used a statevector;
  its Clifford-only circuit now uses Aer stabilizer simulation. State storage
  changes from O(2^q) complex amplitudes to O(q^2) tableau bits, with polynomial
  Clifford operations. The challenge's three-qubit checks also select this
  method explicitly; their previous automatic method may already select it,
  so no exponential speedup is claimed there. T gates, arbitrary rotations or
  non-Clifford noise require a different simulator. The Steane notebook's
  arbitrary statevector initialization was left unchanged for this reason.
  See the [Aer method documentation](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html).
- **Rendering:** `--no-plots` avoids Matplotlib drawing when only JSON/CSV is
  needed. Default output still includes all diagrams. Rendering otherwise
  creates O(T*A) tile artists. Paths beyond the third concurrent measurement
  now also render (colors repeat instead of silently omitting paths).

## Reproduce checks and benchmarks

```powershell
.\qiskit-env\Scripts\python.exe -B -m unittest test_optimizations -v
.\qiskit-env\Scripts\python.exe -B benchmark_optimizations.py
.\qiskit-env\Scripts\python.exe -B surface_code_challenge.py --no-plots --output quick_results
```

On this machine with Python 3.14.6, the saved benchmark run measured:

- BFS on 60x60 tiles with 502 patches: 63.56 ms -> 2.12 ms, about 30x faster.
- A chain of 1,000 operations: 55.53 ms -> 3.00 ms, about 18.5x faster.
  Python peak allocation increased from 449,392 to 643,392 bytes (43%).
- Rank of the 72x144 toric X matrix: 1.058 ms -> 0.233 ms, about 4.5x faster.
  Python peak allocation decreased from 87,840 to 10,838 bytes (88%).

`benchmark_optimizations.py` contains the exact fixtures and loads trusted
baseline commit `938063c07bafcc15a182d94bd74a181db9495cbf` from local Git.
It uses the best of five timing repeats and measures tracemalloc separately.
Imports, fixture/layout construction, native allocations and rendering are
excluded. In particular, the routing memory measurement excludes the added
occupancy cache. These are kernel measurements, not end-to-end speedups for
the tiny default workload. Results vary by machine; raw values are saved in
`challenge_results/optimization_benchmarks.json`.

Validation completed: six regression tests (including 300 randomized schedule
comparisons and randomized GF(2) rank checks), six ideal quantum parity checks,
and all six completed QEC notebook checkpoints (64 shots, rendering skipped).
Surface-17 no-error, X-on-qubit-4 and Z-on-qubit-0 runs were compared with
statevector and stabilizer backends at 1,024 shots and seed 42; counts agreed
in these runs. This is a local circuit regression check, not a noise study.

## Review of the remaining repository

All three notebooks, Python modules, both repository PDFs and existing results
were reviewed. The supplied Downloads prompt adds “Focus on space-time
tradeoffs!” to slide 10; the repository PDF omits that sentence. The objective
and grading otherwise agree: Qiskit 10%, methods 20%, effect 30%, presentation
40%. The PDFs are challenge/reference material, not instructions to install
MCP servers, submit hardware jobs or perform the classroom exercises.

The Road to Fault-Tolerant notebook benefits from the shared rank routine.
Its 72x144 matrices remain dense for compatibility with the exercises; sparse
storage is worth considering only when scaling the code family. Its 10,000-shot
ideal checks and repeated plotting are further tunable overhead, not the
challenge's logical time metric. `minimum_distance` remains O(C^2*n) for C
explicit codewords; using minimum nonzero weight would require a guarantee
that the input is a complete linear code. That assumption is not in its API.
`Game_of_Surface_Codes.ipynb` and `test_qiskit.py` are tiny demonstrations,
not encoded lattice-surgery benchmarks.

The Surface-17 teaching notebook has conceptual limitations independent of
performance: its preparation is not a full encoded logical zero, some prose
reverses which stabilizers detect X versus Z errors, and parts of its printed
bit-order explanation conflict with its circuit. Its hardware timing formula
is an illustrative heuristic, not a calibrated execution estimate. The
simulator change preserves the existing circuit; it does not repair these
teaching claims or establish fault tolerance. Hardware cells were not run.

For a challenge presentation, lead with the fixed-workload comparison and
show both area and elapsed steps. Explain the model's limits before claiming
physical savings; representative-qubit parity checks do not validate a full
encoded patch implementation. The full game includes moves, rotations and
other operations not modeled here; see the
[game rules](https://pennylane.ai/demos/tutorial_game_of_surface_codes).
