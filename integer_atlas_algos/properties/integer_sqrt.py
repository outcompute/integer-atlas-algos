from math import isqrt

from integer_atlas_algos.registry import property_method


@property_method("integer_sqrt", dtype="uint64", complexity="O(1)",
                 test_vectors={0: 0, 10: 3, 16: 4, 99: 9})
def integer_sqrt(n, ctx):
    return isqrt(ctx.abs_n)
