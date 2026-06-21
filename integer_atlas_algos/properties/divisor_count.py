from integer_atlas_algos.registry import property_method


@property_method("divisor_count", dtype="uint32", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 6: 4, 12: 6, 28: 6})
def divisor_count(n, ctx):
    if ctx.abs_n == 0:
        return 0
    r = 1
    for e in ctx.factorization.values():
        r *= (e + 1)
    return r
