from integer_atlas_algos.registry import property_method


@property_method("is_practical", dtype="bool", complexity="O(sqrt n)",
                 requires=("divisors",),
                 test_vectors={1: True, 2: True, 4: True, 6: True, 8: True, 3: False, 5: False})
def is_practical(n, ctx):
    m = ctx.abs_n
    if m == 1:
        return True
    if m == 0 or m % 2 == 1:
        return False
    s = 0
    for d in ctx.divisors:  # ascending
        if d > s + 1:
            return False
        s += d
    return True
