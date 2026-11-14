"""Packed binary linear algebra shared by the lab and its checkpoints."""

import numpy as np


def binary_rank(matrix):
    """Return GF(2) rank without modifying the input binary 2-D array.

    Rows are packed into Python integers. XOR eliminates a whole packed row;
    only independent rows are retained. This is not real-valued matrix rank.
    """
    matrix = np.asarray(matrix)
    if matrix.ndim != 2:
        raise ValueError("Expected a two-dimensional binary matrix")
    pivots = {}
    for row in matrix:
        if not np.all((row == 0) | (row == 1)):
            raise ValueError("Matrix entries must be 0 or 1")
        packed = int.from_bytes(np.packbits(row.astype(np.uint8),
                                          bitorder="little").tobytes(), "little")
        while packed:
            pivot = packed.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = packed
                break
            packed ^= pivots[pivot]
    return len(pivots)
