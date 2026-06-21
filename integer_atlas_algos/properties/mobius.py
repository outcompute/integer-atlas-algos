from integer_atlas_algos.registry import property_method


@property_method("mobius", dtype="int8", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 2: -1, 4: 0, 6: 1, 30: -1, 0: 0})
def mobius(n, ctx):
    if ctx.abs_n == 0:
        return 0
    f = ctx.factorization
    if any(e > 1 for e in f.values()):
        return 0
    return -1 if len(f) % 2 else 1
