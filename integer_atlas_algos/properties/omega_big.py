from integer_atlas_algos.registry import property_method


@property_method("omega_big", dtype="uint16", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 0, 8: 3, 12: 3, 30: 3})
def omega_big(n, ctx):
    return sum(ctx.factorization.values())
