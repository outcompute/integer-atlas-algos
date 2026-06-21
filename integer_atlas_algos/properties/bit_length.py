from integer_atlas_algos.registry import property_method


@property_method("bit_length", dtype="uint16", complexity="O(1)",
                 test_vectors={0: 0, 1: 1, 8: 4, 255: 8})
def bit_length(n, ctx):
    return ctx.abs_n.bit_length()
