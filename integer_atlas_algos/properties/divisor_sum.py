from integer_atlas_algos._lib.multiplicative import sigma
from integer_atlas_algos.registry import property_method


@property_method("divisor_sum", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 6: 12, 12: 28, 28: 56})
def divisor_sum(n, ctx):
    if ctx.abs_n == 0:
        return 0
    return sigma(ctx.factorization)
