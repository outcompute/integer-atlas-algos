from integer_atlas_algos.registry import property_method


@property_method("is_powerful", dtype="bool", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: True, 4: True, 8: True, 9: True, 2: False, 12: False})
def is_powerful(n, ctx):
    if ctx.abs_n == 0:
        return False
    return all(e >= 2 for e in ctx.factorization.values())
