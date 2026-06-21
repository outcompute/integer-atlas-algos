from integer_atlas_algos.registry import property_method


@property_method("collatz_stopping_time", dtype="uint32", complexity="O(steps)",
                 test_vectors={1: 0, 2: 1, 3: 7, 6: 8, 7: 16})
def collatz_stopping_time(n, ctx):
    """Total stopping time: steps of the 3x+1 map to reach 1 (0 for n <= 1)."""
    m = ctx.abs_n
    if m <= 1:
        return 0
    steps = 0
    while m != 1:
        m = m // 2 if m % 2 == 0 else 3 * m + 1
        steps += 1
    return steps
