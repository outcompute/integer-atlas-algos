from math import isqrt

from integer_atlas_algos.registry import property_method


@property_method("is_triangular", dtype="bool", complexity="O(1)",
                 test_vectors={1: True, 3: True, 6: True, 10: True, 4: False, 5: False})
def is_triangular(n, ctx):
    m = 8 * ctx.abs_n + 1
    r = isqrt(m)
    return r * r == m
