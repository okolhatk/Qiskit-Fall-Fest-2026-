"""Local checkpoints for the quantum error correction hackathon lab.

Each function checks one exercise and prints whether it passed.
`checkpoint_progress` summarizes the exercises run in this kernel session.
"""

from __future__ import annotations

import numpy as np

_STATUS = {}

_EXERCISES = (
    "Exercise 1",
    "Exercise 2",
    "Exercise 3",
    "Exercise 4",
    "Exercise 5",
    "Exercise 6",
)


def _record(name, passed):
    _STATUS[name] = bool(passed)


def _finish(name, problems):
    if problems:
        _record(name, False)
        print(f"{name} is not complete yet.")
        for problem in problems:
            print(f"- {problem}")
        return
    _record(name, True)
    print(f"{name} passed.")


def _clean_map(mapping):
    if not isinstance(mapping, dict):
        return None
    cleaned = {}
    for key, value in mapping.items():
        if isinstance(key, str):
            key = key.strip()
        if isinstance(value, str):
            value = value.strip()
        cleaned[key] = value
    return cleaned


def _bitflip_decoder():
    """Syndrome key is s1 then s0. A 1 means that stabilizer anti-commutes with the X error."""
    # S0 = ZZI acts on qubits 1 and 2. S1 = IZZ acts on qubits 0 and 1.
    supports = {0: {1, 2}, 1: {0, 1}}
    decoder = {"00": "I"}
    for qubit in range(3):
        syndrome = "".join(
            "1" if qubit in supports[bit] else "0" for bit in (1, 0)
        )
        decoder[syndrome] = f"X{qubit}"
    return decoder


def _steane_decoder():
    """Syndrome key is s5 s4 s3 s2 s1 s0, matching the lab's Steane table."""
    parity = np.array(
        [
            [1, 1, 1, 1, 0, 0, 0],
            [1, 1, 0, 0, 1, 1, 0],
            [1, 0, 1, 0, 1, 0, 1],
        ],
        dtype=int,
    )
    decoder = {"000000": "I"}
    for qubit in range(7):
        column = parity[:, qubit]
        for pauli in "XYZ":
            bits = [0] * 6
            for row in range(3):
                if column[row] == 0:
                    continue
                if pauli in "ZY":
                    bits[row] = 1
                if pauli in "XY":
                    bits[row + 3] = 1
            syndrome = "".join(str(bits[index]) for index in (5, 4, 3, 2, 1, 0))
            decoder[syndrome] = f"{pauli}{qubit}"
    return decoder


def _check_decoder(name, student, expected, empty_hint, example_hint):
    mapping = _clean_map(student)
    if mapping is None:
        _finish(name, ["The checkpoint expects the decoder dictionary."])
        return

    problems = []
    if any(key == "" for key in mapping):
        problems.append(empty_hint)

    non_strings = [
        repr(key)
        for key, value in mapping.items()
        if not isinstance(key, str) or not isinstance(value, str)
    ]
    if non_strings:
        problems.append(
            "Syndrome keys and corrections should both be strings. "
            f"Check: {', '.join(non_strings[:6])}."
        )
        _finish(name, problems)
        return

    if any(isinstance(key, str) and key[:1] in "IXYZ" for key in mapping):
        problems.append(example_hint)

    wrong = []
    for syndrome, correction in expected.items():
        if mapping.get(syndrome) != correction:
            wrong.append(syndrome)
    if wrong:
        shown = ", ".join(wrong[:8])
        extra = len(wrong) - min(len(wrong), 8)
        suffix = f", and {extra} more" if extra else ""
        problems.append(
            f"These syndromes do not map to the right correction: {shown}{suffix}."
        )

    extras = sorted(set(mapping) - set(expected) - {""})
    if extras:
        shown = ", ".join(repr(key) for key in extras[:6])
        problems.append(f"These keys are not syndromes for this decoder: {shown}.")

    _finish(name, problems)


def checkpoint_1(hardcode_decoder_bit_flip_syndrome_map):
    """Check the 3-qubit bit-flip syndrome decoder."""
    _check_decoder(
        "Exercise 1",
        hardcode_decoder_bit_flip_syndrome_map,
        _bitflip_decoder(),
        "Fill in every syndrome. Empty strings are still in the dictionary.",
        "Map each syndrome bitstring to a correction, for example '00': 'I'. "
        "The key order in the template is s1 then s0.",
    )


def checkpoint_2(steane_decoder_syndrome_map):
    """Check the Steane-code lookup table."""
    _check_decoder(
        "Exercise 2",
        steane_decoder_syndrome_map,
        _steane_decoder(),
        "Fill in every single-qubit error. Empty syndrome strings are still in the dictionary.",
        "Map each 6-bit syndrome to an error code, as in '111000': 'X0'. "
        "The bit order is s5 s4 s3 s2 s1 s0.",
    )


def _steane_logical_zero():
    parity = np.array(
        [
            [1, 1, 1, 1, 0, 0, 0],
            [1, 1, 0, 0, 1, 1, 0],
            [1, 0, 1, 0, 1, 0, 1],
        ],
        dtype=int,
    )
    state = np.zeros(128, dtype=complex)
    for mask in range(8):
        vector = np.zeros(7, dtype=int)
        for bit in range(3):
            if mask & (1 << bit):
                vector = (vector + parity[bit]) % 2
        index = int(vector @ (1 << np.arange(7)))
        state[index] = 1 / np.sqrt(8)
    return state


def _apply_pauli(state, pauli, qubit):
    updated = np.zeros_like(state)
    shift = 1 << qubit
    for basis, amplitude in enumerate(state):
        if amplitude == 0:
            continue
        bit = (basis >> qubit) & 1
        if pauli == "X":
            updated[basis ^ shift] += amplitude
        elif pauli == "Z":
            updated[basis] += amplitude if bit == 0 else -amplitude
        elif pauli == "Y":
            phase = 1j if bit == 0 else -1j
            updated[basis ^ shift] += amplitude * phase
    return updated


def _same_state(left, right):
    overlap = np.vdot(right, left)
    if abs(overlap) < 1e-8:
        return False
    phase = overlap / abs(overlap)
    return np.linalg.norm(left - phase * right) < 1e-6


def _injected_error(amplitudes):
    logical = _steane_logical_zero()
    for pauli in "XYZ":
        for qubit in range(7):
            if _same_state(amplitudes, _apply_pauli(logical, pauli, qubit)):
                return f"{pauli}{qubit}"
    return None


def checkpoint_3(error_code):
    """Check the error detected on the provided Steane state."""
    problems = []
    if not isinstance(error_code, str) or not error_code.strip():
        problems.append(
            "error_code should be a string such as 'X1', using the code you read from the lookup table."
        )
        _finish("Exercise 3", problems)
        return

    try:
        from lab4_util import bring_states
    except Exception as exc:
        _finish(
            "Exercise 3",
            [f"Could not load the lab state from lab4_util.py ({exc})."],
        )
        return

    expected = _injected_error(np.asarray(bring_states().data, dtype=complex))
    if expected is None:
        _finish(
            "Exercise 3",
            ["The provided state is not a single-qubit Pauli error on logical |0>."],
        )
        return

    submitted = error_code.strip().upper()
    if submitted != expected:
        problems.append(
            "That error code does not match the syndrome of the provided state. "
            "Use the bitstring that appeared with probability 1, and the short label from your lookup table."
        )
    _finish("Exercise 3", problems)


def _blue(row, col, nrows=6, ncols=12):
    return int(np.mod(row, nrows)) + int(np.mod(col, ncols)) * nrows


def _orange(row, col):
    return 72 + _blue(row, col)


def _toric_matrices():
    checks_x = np.zeros((72, 144), dtype=int)
    checks_z = np.zeros((72, 144), dtype=int)
    for row in range(6):
        for col in range(12):
            index = _blue(row, col)
            checks_x[index, [_blue(row, col), _blue(row + 1, col)]] = 1
            checks_x[index, [_orange(row, col - 1), _orange(row, col)]] = 1
            checks_z[index, [_blue(row, col), _blue(row, col + 1)]] = 1
            checks_z[index, [_orange(row, col), _orange(row - 1, col)]] = 1
    return checks_x, checks_z


def _gross_matrices():
    checks_x, checks_z = _toric_matrices()
    checks_x = checks_x.copy()
    checks_z = checks_z.copy()
    for row in range(6):
        for col in range(12):
            index = _blue(row, col)
            # Offsets continue the worked example: X checks touch qubits
            # 0, 1, 20, 72, 135, 138 and Z checks touch 0, 6, 15, 72, 77, 130.
            checks_x[index, [_blue(row + 2, col + 3), _orange(row - 3, col - 2)]] = 1
            checks_z[index, [_blue(row + 3, col + 2), _orange(row - 2, col - 3)]] = 1
    return checks_x, checks_z


def _as_binary_matrix(value):
    array = np.asarray(value)
    if array.shape != (72, 144):
        return None, f"expected shape (72, 144), got {array.shape}."
    if array.dtype == bool:
        return array.astype(int), None
    if not np.issubdtype(array.dtype, np.number):
        return None, "entries must be numbers."
    numeric = np.asarray(array, dtype=float)
    if not np.all(np.isfinite(numeric)) or np.max(np.abs(numeric - np.rint(numeric))) > 1e-8:
        return None, "entries must be 0 or 1."
    binary = np.mod(np.rint(numeric).astype(int), 2)
    if not np.all((numeric == 0) | (numeric == 1)):
        return None, "entries must be 0 or 1."
    return binary, None


def _matrix_rank(matrix):
    """Rank over GF(2), matching lab4_util.matrixRank."""
    reduced = matrix.copy()
    pivots = {}
    for row in range(len(reduced)):
        pivot = next((index for index, value in enumerate(reduced[row]) if value != 0), -1)
        if pivot < 0:
            continue
        for other in range(len(reduced)):
            if other != row and reduced[other][pivot] == 1:
                reduced[other] = (reduced[other] + reduced[row]) % 2
        pivots[row] = pivot
    return len(pivots)


def _check_checks(name, checks_x, checks_z, reference_x, reference_z, weight, code_name):
    problems = []
    parsed = {}
    for label, value in (("HX", checks_x), ("HZ", checks_z)):
        binary, problem = _as_binary_matrix(value)
        if problem:
            problems.append(f"{label} {problem}")
        else:
            parsed[label] = binary
    if problems:
        _finish(name, problems)
        return

    for label, binary in parsed.items():
        weights = set(np.unique(binary.sum(axis=1)))
        if weights != {weight}:
            problems.append(
                f"Each {label} row of the {code_name} should have {weight} ones. "
                f"The row weights found were {sorted(int(item) for item in weights)}."
            )

    if np.any((parsed["HX"] @ parsed["HZ"].T) % 2):
        problems.append(
            "Some X checks and Z checks anti-commute. "
            "On a CSS code every row of HX should overlap every row of HZ evenly."
        )

    for label, student, reference in (
        ("HX", parsed["HX"], reference_x),
        ("HZ", parsed["HZ"], reference_z),
    ):
        if np.array_equal(student, reference):
            continue
        student_rows = [tuple(row.tolist()) for row in student]
        reference_rows = [tuple(row.tolist()) for row in reference]
        if sorted(student_rows) == sorted(reference_rows):
            problems.append(
                f"{label} has the right checks, but the rows are not in stabilizer-index order. "
                "Row j belongs to the check at grid index j."
            )
            continue
        differ = int(np.sum(np.any(student != reference, axis=1)))
        problems.append(
            f"{differ} of 72 rows in {label} do not match the {code_name} checks at that stabilizer index."
        )

    _finish(name, problems)


def checkpoint_4(HXtc, HZtc):
    """Check the toric-code parity-check matrices."""
    reference_x, reference_z = _toric_matrices()
    _check_checks("Exercise 4", HXtc, HZtc, reference_x, reference_z, 4, "toric code")


def checkpoint_5(HXgc, HZgc):
    """Check the gross-code parity-check matrices."""
    reference_x, reference_z = _gross_matrices()
    _check_checks("Exercise 5", HXgc, HZgc, reference_x, reference_z, 6, "gross code")


def _as_int(value):
    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, (float, np.floating)) and not float(value).is_integer():
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _logical_qubits(checks_x, checks_z):
    return 144 - _matrix_rank(checks_x) - _matrix_rank(checks_z)


def checkpoint_6(k_toric, k_gross):
    """Check the number of logical qubits for both codes."""
    toric_x, toric_z = _toric_matrices()
    gross_x, gross_z = _gross_matrices()
    expected = {
        "k_toric": _logical_qubits(toric_x, toric_z),
        "k_gross": _logical_qubits(gross_x, gross_z),
    }
    submitted = {"k_toric": _as_int(k_toric), "k_gross": _as_int(k_gross)}
    problems = []
    for name in ("k_toric", "k_gross"):
        if submitted[name] is None:
            problems.append(f"{name} should be an integer.")
        elif submitted[name] != expected[name]:
            problems.append(
                f"{name} is not k = n - rank(HX) - rank(HZ) for that code, with n = 144."
            )
    _finish("Exercise 6", problems)


def checkpoint_progress():
    """Print which exercise checkpoints have passed in this kernel session."""
    passed = sum(1 for name in _EXERCISES if _STATUS.get(name))
    print(f"Checkpoints passed: {passed} of {len(_EXERCISES)}")
    for name in _EXERCISES:
        if _STATUS.get(name):
            print(f"- {name}: passed")
        elif name in _STATUS:
            print(f"- {name}: not yet")
        else:
            print(f"- {name}: not run")
