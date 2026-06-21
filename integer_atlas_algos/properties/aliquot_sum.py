from integer_atlas_algos._lib.multiplicative import sigma
from integer_atlas_algos.registry import property_method


@property_method("aliquot_sum", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 0, 6: 6, 12: 16, 28: 28})
def aliquot_sum(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return 0
    return sigma(ctx.factorization) - m
