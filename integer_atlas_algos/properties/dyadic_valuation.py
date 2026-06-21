from integer_atlas_algos.registry import property_method


@property_method("dyadic_valuation", dtype="uint16", complexity="O(1)",
                 test_vectors={0: 0, 1: 0, 7: 0, 8: 3, 12: 2})
def dyadic_valuation(n, ctx):
    """2-adic valuation v2(n): exponent of 2 in n (0 reported for n = 0)."""
    m = ctx.abs_n
    if m == 0:
        return 0
    return (m & -m).bit_length() - 1
