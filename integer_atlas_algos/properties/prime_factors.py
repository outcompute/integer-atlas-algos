from integer_atlas_algos.registry import property_method


@property_method("prime_factors", dtype="uint64[]", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={0: [], 1: [], 2: [2], 12: [2, 2, 3], 360: [2, 2, 2, 3, 3, 5]})
def prime_factors(n, ctx):
    """Prime factors of abs(n) with multiplicity, ascending: 360 -> [2, 2, 2, 3, 3, 5].

    Empty list for 0 and 1 (no prime factors).
    """
    out = []
    for p, e in sorted(ctx.factorization.items()):
        out.extend([p] * e)
    return out
