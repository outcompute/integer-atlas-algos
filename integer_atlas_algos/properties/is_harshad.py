from integer_atlas_algos.registry import property_method


@property_method("is_harshad", dtype="bool", complexity="O(d)",
                 test_vectors={1: True, 12: True, 18: True, 11: False, 0: False})
def is_harshad(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return False
    return m % sum(int(c) for c in str(m)) == 0
