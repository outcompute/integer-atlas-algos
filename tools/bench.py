"""Benchmark reference implementations of candidate properties at a sample n.

Prints: column<TAB>big-O<TAB>per-call microseconds (best of 5 autorange runs).
These are pure-Python reference timings on one machine — indicative only, meant
to seed the planner's cost model, not to be frozen into method metadata.
"""
import math
import sys
import timeit
from math import gcd, isqrt, lcm

N = int(sys.argv[1]) if len(sys.argv) > 1 else 1000


def factorize(m):
    m = abs(m)
    f = {}
    while m % 2 == 0:
        f[2] = f.get(2, 0) + 1
        m //= 2
    d = 3
    while d * d <= m:
        while m % d == 0:
            f[d] = f.get(d, 0) + 1
            m //= d
        d += 2
    if m > 1:
        f[m] = f.get(m, 0) + 1
    return f


def divisors(n):
    f = factorize(n)
    divs = [1]
    for p, e in f.items():
        divs = [d * p**k for d in divs for k in range(e + 1)]
    return sorted(divs)


def is_square(n):
    r = isqrt(n)
    return r * r == n


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def euler_phi(n):
    r = n
    for p in factorize(n):
        r -= r // p
    return r


def divisor_sum(n):
    s = 1
    for p, e in factorize(n).items():
        s *= (p**(e + 1) - 1) // (p - 1)
    return s


def carmichael(n):
    res = 1
    for p, e in factorize(n).items():
        if p == 2:
            l = 1 if e == 1 else (2 if e == 2 else 2**(e - 2))
        else:
            l = p**(e - 1) * (p - 1)
        res = lcm(res, l)
    return res


def gcd_sum(n):  # Pillai: sum_{d|n} d*phi(n/d); multiplicative closed form
    r = 1
    for p, e in factorize(n).items():
        r *= (e + 1) * p**e - e * p**(e - 1)
    return r


def r2(n):  # number of representations as sum of two squares
    d1 = d3 = 0
    for d in divisors(n):
        if d % 4 == 1:
            d1 += 1
        elif d % 4 == 3:
            d3 += 1
    return 4 * (d1 - d3)


def is_perfect_power(n):
    if n <= 1:
        return True
    for k in range(2, n.bit_length() + 1):
        r = round(n ** (1 / k))
        for c in (r - 1, r, r + 1):
            if c >= 2 and c**k == n:
                return True
    return False


def is_practical(n):
    if n == 1:
        return True
    if n % 2:
        return False
    s = 0
    for d in divisors(n):
        if d > s + 1:
            return False
        s += d
    return True


def partition(n):
    p = [0] * (n + 1)
    p[0] = 1
    for i in range(1, n + 1):
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
        p[i] = total
    return p[n]


def collatz_steps(n):
    c = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        c += 1
    return c


def is_happy(n):
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = sum(int(c) ** 2 for c in str(n))
    return n == 1


def digit_sum(n):
    return sum(int(c) for c in str(n))


def smallest_prime_factor(n):
    if n % 2 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d += 2
    return n


def abundance_class(n):
    s = divisor_sum(n)
    return "abundant" if s > 2 * n else "perfect" if s == 2 * n else "deficient"


# (column, big-O in input, callable)
CASES = [
    # representations / powers / transcendentals
    ("square", "O(1)", lambda: N * N),
    ("cube", "O(1)", lambda: N * N * N),
    ("log10", "O(1)", lambda: math.log10(N)),
    ("ln", "O(1)", lambda: math.log(N)),
    ("sqrt", "O(1)", lambda: math.sqrt(N)),
    ("integer_sqrt", "O(1)", lambda: isqrt(N)),
    ("binary_repr", "O(b)", lambda: format(N, "b")),
    ("octal_repr", "O(b)", lambda: format(N, "o")),
    ("hex_repr", "O(b)", lambda: format(N, "x")),
    # base pack
    ("bit_length", "O(1)", lambda: N.bit_length()),
    ("binary_popcount", "O(b)", lambda: N.bit_count()),
    ("dyadic_valuation", "O(1)", lambda: (N & -N).bit_length() - 1),
    ("digit_sum", "O(d)", lambda: digit_sum(N)),
    ("digital_root", "O(1)", lambda: 1 + (N - 1) % 9),
    ("decimal_digit_count", "O(d)", lambda: len(str(N))),
    ("is_palindrome", "O(d)", lambda: str(N) == str(N)[::-1]),
    ("is_harshad", "O(d)", lambda: N % digit_sum(N) == 0),
    ("is_square", "O(1)", lambda: is_square(N)),
    ("is_fibonacci", "O(1)", lambda: is_square(5 * N * N + 4) or is_square(5 * N * N - 4)),
    ("is_triangular", "O(1)", lambda: is_square(8 * N + 1)),
    # primality / factor structure
    ("is_prime", "O(sqrt n)", lambda: is_prime(N)),
    ("factorize", "O(sqrt n)", lambda: factorize(N)),
    ("omega_distinct", "O(sqrt n)", lambda: len(factorize(N))),
    ("omega_big", "O(sqrt n)", lambda: sum(factorize(N).values())),
    ("smallest_prime_factor", "O(spf), worst O(sqrt n)", lambda: smallest_prime_factor(N)),
    ("largest_prime_factor", "O(sqrt n)", lambda: max(factorize(N))),
    ("radical", "O(sqrt n)", lambda: math.prod(factorize(N))),
    ("is_squarefree", "O(sqrt n)", lambda: all(e == 1 for e in factorize(N).values())),
    ("is_powerful", "O(sqrt n)", lambda: all(e >= 2 for e in factorize(N).values())),
    ("is_prime_power", "O(sqrt n)", lambda: len(factorize(N)) == 1),
    ("mobius", "O(sqrt n)", lambda: 0 if any(e > 1 for e in factorize(N).values()) else (-1) ** len(factorize(N))),
    # multiplicative functions
    ("euler_phi", "O(sqrt n)", lambda: euler_phi(N)),
    ("carmichael_lambda", "O(sqrt n)", lambda: carmichael(N)),
    ("divisor_count", "O(sqrt n)", lambda: math.prod(e + 1 for e in factorize(N).values())),
    ("divisor_sum", "O(sqrt n)", lambda: divisor_sum(N)),
    ("aliquot_sum", "O(sqrt n)", lambda: divisor_sum(N) - N),
    ("abundancy_index", "O(sqrt n)", lambda: divisor_sum(N) / N),
    ("von_mangoldt", "O(sqrt n)", lambda: (math.log(next(iter(factorize(N)))) if len(factorize(N)) == 1 else 0.0)),
    ("gcd_sum_pillai", "O(sqrt n)", lambda: gcd_sum(N)),
    # classifications / heavier
    ("is_perfect", "O(sqrt n)", lambda: divisor_sum(N) == 2 * N),
    ("abundance_class", "O(sqrt n)", lambda: abundance_class(N)),
    ("is_perfect_power", "O(log^2 n)", lambda: is_perfect_power(N)),
    ("is_practical", "O(sqrt n)", lambda: is_practical(N)),
    ("sum_of_two_squares_count", "O(sqrt n)", lambda: r2(N)),
    ("is_happy", "O(k d)", lambda: is_happy(N)),
    ("collatz_stopping_time", "O(steps)", lambda: collatz_steps(N)),
    ("partition_count", "O(n sqrt n)", lambda: partition(N)),
]


def main():
    print(f"# n = {N}")
    print("column\tbig_o\tusec")
    for name, bigo, fn in CASES:
        t = timeit.Timer(fn)
        number, _ = t.autorange()
        best = min(t.repeat(repeat=5, number=number)) / number
        print(f"{name}\t{bigo}\t{best * 1e6:.3f}")


if __name__ == "__main__":
    main()
