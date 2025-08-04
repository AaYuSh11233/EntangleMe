import random


def create_random_seed() -> int:
    _min_seed = 0
    _max_seed = (
        2**32 - 1
    )  # not certain of underline limitation in minizinc, 32bit should enough
    return random.SystemRandom().randint(a=_min_seed, b=_max_seed)
