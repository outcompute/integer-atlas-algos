"""Shared multiplicative-function helpers derived from a factorization."""


def sigma(factorization):
    """Sum of divisors from prime -> exponent (1 for the empty factorization)."""
    s = 1
    for p, e in factorization.items():
        s *= (p ** (e + 1) - 1) // (p - 1)
    return s
