from integer_atlas_algos.registry import property_method


@property_method("omega_distinct", dtype="uint16", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 0, 7: 1, 12: 2, 30: 3})
def omega_distinct(n, ctx):
    return len(ctx.factorization)
