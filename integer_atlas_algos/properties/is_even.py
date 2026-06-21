from integer_atlas_algos.registry import property_method


@property_method("is_even", dtype="bool", complexity="O(1)",
                 test_vectors={2: True, 3: False, 0: True})
def is_even(n, ctx):
    return ctx.abs_n % 2 == 0
