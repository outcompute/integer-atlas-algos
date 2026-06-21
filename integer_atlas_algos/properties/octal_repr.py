from integer_atlas_algos.registry import property_method


@property_method("octal_repr", dtype="string", complexity="O(b)",
                 test_vectors={0: "0", 8: "10", 64: "100"})
def octal_repr(n, ctx):
    return format(ctx.abs_n, "o")
