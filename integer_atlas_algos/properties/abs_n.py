from integer_atlas_algos.registry import property_method


@property_method("abs_n", dtype="uint64", complexity="O(1)",
                 test_vectors={5: 5, -3: 3, 0: 0})
def abs_n(n, ctx):
    return ctx.abs_n
