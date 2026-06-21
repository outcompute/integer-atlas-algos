from integer_atlas_algos.registry import property_method

# Module-level memo: grows once as n increases, so computing partition_count over
# an ascending range is O(N sqrt N) in total rather than per row. Values grow
# enormously with n (hundreds of digits), so this column is only practical for
# small ranges regardless of speed.
_P = [1]  # p(0) = 1


def _ensure(n):
    p = _P
    for i in range(len(p), n + 1):
        k, total = 1, 0
        while True:
            g1 = k * (3 * k - 1) // 2
            g2 = k * (3 * k + 1) // 2
            if g1 > i and g2 > i:
                break
            sign = 1 if k % 2 else -1
            if g1 <= i:
                total += sign * p[i - g1]
            if g2 <= i:
                total += sign * p[i - g2]
            k += 1
        p.append(total)


@property_method("partition_count", dtype="bigint", complexity="O(n sqrt n)",
                 test_vectors={0: 1, 1: 1, 5: 7, 10: 42})
def partition_count(n, ctx):
    m = ctx.abs_n
    _ensure(m)
    return _P[m]
