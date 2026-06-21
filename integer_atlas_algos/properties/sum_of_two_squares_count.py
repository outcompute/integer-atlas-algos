from integer_atlas_algos.registry import property_method


@property_method("sum_of_two_squares_count", dtype="uint32", complexity="O(sqrt n)",
                 requires=("divisors",),
                 test_vectors={0: 1, 1: 4, 2: 4, 3: 0, 5: 8, 25: 12})
def sum_of_two_squares_count(n, ctx):
    """r2(n): representations n = a^2 + b^2 over the integers (ordered, signed)."""
    m = ctx.abs_n
    if m == 0:
        return 1
    d1 = d3 = 0
    for d in ctx.divisors:
        if d % 4 == 1:
            d1 += 1
        elif d % 4 == 3:
            d3 += 1
    return 4 * (d1 - d3)
