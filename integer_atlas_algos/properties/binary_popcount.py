from integer_atlas_algos.registry import property_method


@property_method("binary_popcount", dtype="uint16", complexity="O(b)",
                 test_vectors={0: 0, 7: 3, 255: 8})
def binary_popcount(n, ctx):
    return ctx.abs_n.bit_count()
