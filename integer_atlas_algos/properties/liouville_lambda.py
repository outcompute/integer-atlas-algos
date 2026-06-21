from integer_atlas_algos.registry import property_method


@property_method("liouville_lambda", dtype="int8", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 2: -1, 4: 1, 12: -1})
def liouville_lambda(n, ctx):
    return -1 if sum(ctx.factorization.values()) % 2 else 1
