from integer_atlas_algos.registry import property_method


@property_method("binary_repr", dtype="string", complexity="O(b)",
                 test_vectors={0: "0", 10: "1010", 255: "11111111"})
def binary_repr(n, ctx):
    return format(ctx.abs_n, "b")
