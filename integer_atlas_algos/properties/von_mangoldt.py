from math import log

from integer_atlas_algos.registry import property_method


@property_method("von_mangoldt", dtype="double", complexity="O(sqrt n)",
                 requires=("factorization",),
                 test_vectors={1: 0.0, 6: 0.0, 8: log(2), 7: log(7)})
def von_mangoldt(n, ctx):
    """Λ(n) = ln p if n is a power of a single prime p, else 0."""
    f = ctx.factorization
    if len(f) == 1:
        return log(next(iter(f)))
    return 0.0
