import numpy as np
from torch import Tensor


#
# Utils for `DatasetNot`
#
def all_bits_to_one(n: int) -> int:
    """
    Return an integer of length `n` bits, where all the bits are `1`
    """
    return (2**n) - 1


def all_bits_to_zero(n: int) -> int:
    """
    Return an integer of length `n` bits, where all the bits are `0`
    """
    return 0


#
# Transformers for `DatasetNot`
#
def state_to_weights(pure_state: Tensor) -> Tensor:
    """
    input: a `Tensor` of binary numbers (0 or 1)
    output: the required angle of rotation for `Rx`
    (in other words, |0> translates to no rotation, and |1> translates to `pi`)
    """
    # |0> requires a rotation by 0
    # |1> requires a rotation by pi
    return pure_state.bool().int() * np.pi


def state_to_label(pure_state: Tensor) -> Tensor:
    """
    input: a `Tensor` of binary numbers (0 or 1) - the return value of a measurement
    output: probability (from that measurement) of measuring 0
    (in other words,
        |0> translates to 100% chance for measuring |0> ==> return value is 1.0
        |1> translates to   0% chance for measuring |0> ==> return value is 0.0
    )
    """
    # |0> means 100% chance to get |0> ==> 100% == 1.0
    # |1> means   0% chance to get |0> ==>   0% == 0.0

    # This line basically does `1 - bool(pure_state)`
    return 1 - pure_state.bool().int()
