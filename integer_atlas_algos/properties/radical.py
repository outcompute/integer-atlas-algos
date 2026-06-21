from math import prod

from integer_atlas_algos.registry import property_method


@property_method("radical", dtype="uint64", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={0: 0, 1: 1, 8: 2, 12: 6, 360: 30})
def radical(n, ctx):
    if ctx.abs_n == 0:
        return 0
    return prod(ctx.factorization)  # product of distinct primes; empty -> 1
