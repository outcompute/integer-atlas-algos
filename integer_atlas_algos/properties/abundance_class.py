from integer_atlas_algos._lib.multiplicative import sigma
from integer_atlas_algos.registry import property_method


@property_method("abundance_class", dtype="string", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={6: "perfect", 12: "abundant", 8: "deficient", 1: "deficient"})
def abundance_class(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return "deficient"
    s = sigma(ctx.factorization)
    return "abundant" if s > 2 * m else "perfect" if s == 2 * m else "deficient"
