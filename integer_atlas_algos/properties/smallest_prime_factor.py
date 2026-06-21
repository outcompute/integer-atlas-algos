from integer_atlas_algos.registry import property_method


@property_method("smallest_prime_factor", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={0: 0, 1: 1, 2: 2, 15: 3, 49: 7})
def smallest_prime_factor(n, ctx):
    m = ctx.abs_n
    if m < 2:
        return m  # spf(0)=0, spf(1)=1 by convention
    return min(ctx.factorization)
