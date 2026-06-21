from integer_atlas_algos.registry import property_method


@property_method("is_perfect_power", dtype="bool", complexity="O(log^2 n)",
                 test_vectors={1: True, 4: True, 8: True, 9: True, 16: True, 2: False, 12: False})
def is_perfect_power(n, ctx):
    m = ctx.abs_n
    if m == 1:
        return True
    if m == 0:
        return False
    for k in range(2, m.bit_length() + 1):
        r = round(m ** (1.0 / k))
        for c in (r - 1, r, r + 1):
            if c >= 2 and c ** k == m:
                return True
    return False
