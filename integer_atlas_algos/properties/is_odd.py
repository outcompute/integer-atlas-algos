from integer_atlas_algos.registry import property_method


@property_method("is_odd", dtype="bool", complexity="O(1)",
                 test_vectors={3: True, 2: False, 0: False})
def is_odd(n, ctx):
    return ctx.abs_n % 2 == 1
