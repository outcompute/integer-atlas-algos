from integer_atlas_algos.registry import property_method


@property_method("digital_root", dtype="uint8", complexity="O(1)",
                 test_vectors={0: 0, 9: 9, 99: 9, 123: 6})
def digital_root(n, ctx):
    m = ctx.abs_n
    return 0 if m == 0 else 1 + (m - 1) % 9
