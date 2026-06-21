from integer_atlas_algos.registry import property_method


@property_method("digit_sum", dtype="uint32", complexity="O(d)",
                 test_vectors={0: 0, 9: 9, 123: 6, 1000: 1})
def digit_sum(n, ctx):
    return sum(int(c) for c in str(ctx.abs_n))
