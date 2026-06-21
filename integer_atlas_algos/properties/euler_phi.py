from integer_atlas_algos.registry import property_method


@property_method("euler_phi", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 9: 6, 10: 4, 12: 4})
def euler_phi(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return 0
    r = m
    for p in ctx.factorization:
        r -= r // p
    return r
