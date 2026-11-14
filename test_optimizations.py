"""Run with python -m unittest test_optimizations -v (no hardware access)."""

import random
import unittest

import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator

from gf2 import binary_rank
from qec_checkpoints import _toric_matrices, _gross_matrices
from surface_code_challenge import (
    LAYOUTS, Layout, Measurement, WORKLOAD, parity_circuit, route, schedule,
    validate_schedule, verify_quantum,
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
            path = route(layout, op, reserved)
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
