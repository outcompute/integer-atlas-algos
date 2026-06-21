"""Per-n memoized context passed to every method.

Shared, expensive intermediates (factorization, etc.) are computed once per n
and reused across methods that declare them via `requires`. Cheap methods just
read ctx.n / ctx.abs_n and ignore the rest.
"""
from functools import cached_property

from integer_atlas_algos._lib.factorization import factorize


class Context:
    def __init__(self, n: int):
        self.n = n
        self.abs_n = abs(n)

    @cached_property
    def factorization(self) -> dict[int, int]:
        """prime -> exponent for abs(n); empty for 0 and 1."""
        return factorize(self.abs_n)

    @cached_property
    def divisors(self) -> list[int]:
        """Sorted positive divisors of abs(n) (for abs(n) >= 1)."""
        divs = [1]
        for p, e in self.factorization.items():
            divs = [d * p ** k for d in divs for k in range(e + 1)]
        return sorted(divs)
