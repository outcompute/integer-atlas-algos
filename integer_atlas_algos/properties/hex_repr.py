from integer_atlas_algos.registry import property_method


@property_method("hex_repr", dtype="string", complexity="O(b)",
                 test_vectors={0: "0", 255: "ff", 4096: "1000"})
def hex_repr(n, ctx):
    return format(ctx.abs_n, "x")
