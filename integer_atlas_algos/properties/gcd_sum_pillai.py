from integer_atlas_algos.registry import property_method


@property_method("gcd_sum_pillai", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 2: 3, 6: 15, 12: 40})
def gcd_sum_pillai(n, ctx):
    """Pillai's arithmetical function P(n) = sum_{k=1..n} gcd(k, n).

    Multiplicative, with P(p^e) = (e+1)*p^e - e*p^(e-1).
    """
    if ctx.abs_n == 0:
        return 0
    r = 1
    for p, e in ctx.factorization.items():
        r *= (e + 1) * p**e - e * p**(e - 1)
    return r
