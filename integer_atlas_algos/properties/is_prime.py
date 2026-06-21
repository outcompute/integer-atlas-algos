from integer_atlas_algos.registry import property_method


@property_method("is_prime", dtype="bool", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={2: True, 3: True, 97: True, 1: False, 4: False, 0: False})
def is_prime(n, ctx):
    f = ctx.factorization
    return len(f) == 1 and next(iter(f.values())) == 1
