from integer_atlas_algos._lib.multiplicative import sigma
from integer_atlas_algos.registry import property_method


@property_method("is_perfect", dtype="bool", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={6: True, 28: True, 12: False, 1: False})
def is_perfect(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return False
    return sigma(ctx.factorization) == 2 * m
