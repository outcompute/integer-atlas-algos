from integer_atlas_algos._lib.multiplicative import sigma
from integer_atlas_algos.registry import property_method


@property_method("abundancy_index", dtype="double", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1.0, 6: 2.0, 28: 2.0})
def abundancy_index(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return 0.0
    return sigma(ctx.factorization) / m
