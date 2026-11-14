# Surface-code layout experiment

Run from the repository directory in PowerShell:

```powershell
.\qiskit-env\Scripts\python.exe surface_code_challenge.py
```

The existing environment supplies Qiskit, Aer, Matplotlib and pylatexenc.
No IBM account, hardware jobs, or additional platform is required.

## Question

How does auxiliary workspace affect the time needed to perform a fixed
sequence of joint measurements on four logical patches?

The workload is ZZ on AB and CD, followed by XX on BC and AD. The latter
pair depends on both first-round measurements. Separate measurements within
a round act on disjoint data patches. Both layouts execute the same workload.

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
