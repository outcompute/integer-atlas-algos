from integer_atlas_algos.registry import property_method


@property_method("largest_prime_factor", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={0: 0, 1: 1, 12: 3, 17: 17})
def largest_prime_factor(n, ctx):
    m = ctx.abs_n
    if m < 2:
        return m
    return max(ctx.factorization)
