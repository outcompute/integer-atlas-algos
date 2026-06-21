from integer_atlas_algos.registry import property_method


@property_method("is_palindrome", dtype="bool", complexity="O(d)",
                 test_vectors={0: True, 11: True, 121: True, 12: False, 123: False})
def is_palindrome(n, ctx):
    s = str(ctx.abs_n)
    return s == s[::-1]
