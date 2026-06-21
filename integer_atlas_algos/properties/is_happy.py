from integer_atlas_algos.registry import property_method


@property_method("is_happy", dtype="bool", complexity="O(k d)",
                 test_vectors={1: True, 7: True, 10: True, 13: True, 2: False, 4: False})
def is_happy(n, ctx):
    m = ctx.abs_n
    if m == 0:
        return False
    seen = set()
    while m != 1 and m not in seen:
        seen.add(m)
        m = sum(int(c) ** 2 for c in str(m))
    return m == 1
