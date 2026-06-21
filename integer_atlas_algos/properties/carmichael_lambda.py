from math import lcm

from integer_atlas_algos.registry import property_method


@property_method("carmichael_lambda", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 1, 8: 2, 15: 4, 7: 6})
def carmichael_lambda(n, ctx):
    if ctx.abs_n == 0:
        return 0
    res = 1
    for p, e in ctx.factorization.items():
        if p == 2:
            l = 1 if e == 1 else (2 if e == 2 else 2 ** (e - 2))
        else:
            l = p ** (e - 1) * (p - 1)
        res = lcm(res, l)
    return res
