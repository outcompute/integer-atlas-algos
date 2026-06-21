from integer_atlas_algos.registry import property_method


@property_method("is_squarefree", dtype="bool", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: True, 6: True, 8: False, 12: False, 0: False})
def is_squarefree(n, ctx):
    if ctx.abs_n == 0:
        return False
    return all(e == 1 for e in ctx.factorization.values())
