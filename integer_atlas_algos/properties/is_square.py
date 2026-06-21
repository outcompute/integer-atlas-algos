from math import isqrt

from integer_atlas_algos.registry import property_method


@property_method("is_square", dtype="bool", complexity="O(1)",
                 test_vectors={0: True, 1: True, 4: True, 9: True, 2: False, 10: False})
def is_square(n, ctx):
    r = isqrt(ctx.abs_n)
    return r * r == ctx.abs_n
