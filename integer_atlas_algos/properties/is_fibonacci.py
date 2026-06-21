from math import isqrt

from integer_atlas_algos.registry import property_method


def _is_square(m):
    r = isqrt(m)
    return r * r == m


@property_method("is_fibonacci", dtype="bool", complexity="O(1)",
                 test_vectors={1: True, 8: True, 21: True, 4: False, 6: False})
def is_fibonacci(n, ctx):
    m = ctx.abs_n
    return _is_square(5 * m * m + 4) or _is_square(5 * m * m - 4)
