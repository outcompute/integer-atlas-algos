from integer_atlas_algos.registry import property_method


@property_method("sign", dtype="int8", complexity="O(1)",
                 test_vectors={5: 1, 0: 0, -3: -1})
def sign(n, ctx):
    return -1 if n < 0 else (0 if n == 0 else 1)
