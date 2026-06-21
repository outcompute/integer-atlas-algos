from integer_atlas_algos.registry import property_method


@property_method("is_prime_power", dtype="bool", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={7: True, 8: True, 9: True, 12: False, 1: False})
def is_prime_power(n, ctx):
    return len(ctx.factorization) == 1
