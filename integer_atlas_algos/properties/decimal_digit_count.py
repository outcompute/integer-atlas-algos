from integer_atlas_algos.registry import property_method


@property_method("decimal_digit_count", dtype="uint16", complexity="O(d)",
                 test_vectors={0: 1, 9: 1, 1000: 4})
def decimal_digit_count(n, ctx):
    return len(str(ctx.abs_n))
