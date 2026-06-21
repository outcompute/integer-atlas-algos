"""Factorization backed by a precomputed base-primes table.

To factor any n up to BOUND**2 you only need primes up to BOUND. With
BOUND = 31623 (>= sqrt(1e9)) this covers the whole 0..1e9 range using ~3401
primes. The table is a deterministic, regenerable resource cached in
algos/precomputed/ — not state about any shard or pack. For n beyond BOUND**2
factorization stays correct by continuing trial division past the table.
"""
import os

_PRECOMP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "precomputed")
DEFAULT_BOUND = 31623  # ceil(sqrt(1e9)); factors any n <= 1e9

_primes_cache: dict[int, list[int]] = {}


def _sieve(bound: int) -> list[int]:
    flags = bytearray([1]) * (bound + 1)
    flags[0] = flags[1] = 0
    i = 2
    while i * i <= bound:
        if flags[i]:
            flags[i * i::i] = bytearray(len(flags[i * i::i]))
        i += 1
    return [i for i in range(2, bound + 1) if flags[i]]


def small_primes(bound: int = DEFAULT_BOUND) -> list[int]:
    """Primes <= bound, cached in memory and persisted under precomputed/."""
    cached = _primes_cache.get(bound)
    if cached is not None:
        return cached
    path = os.path.join(_PRECOMP_DIR, f"primes_le_{bound}.txt")
    if os.path.exists(path):
        with open(path) as f:
            primes = [int(x) for x in f.read().split()]
    else:
        primes = _sieve(bound)
        try:
            os.makedirs(_PRECOMP_DIR, exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                f.write("\n".join(map(str, primes)))
            os.replace(tmp, path)
        except OSError:
            pass  # read-only filesystem: fall back to in-memory only
    _primes_cache[bound] = primes
    return primes


def factorize(m: int) -> dict[int, int]:
    """prime -> exponent for abs(m); empty dict for 0 and 1."""
    m = abs(int(m))
    f: dict[int, int] = {}
    if m < 2:
        return f
    primes = small_primes()
    broke = False
    for p in primes:
        if p * p > m:
            broke = True
            break
        if m % p == 0:
            c = 0
            while m % p == 0:
                m //= p
                c += 1
            f[p] = c
    if m > 1:
        if broke or m <= primes[-1] * primes[-1]:
            # remaining cofactor is prime (it has no factor <= sqrt(m))
            f[m] = f.get(m, 0) + 1
        else:
            # n exceeded the table's reach: keep trial-dividing past the bound
            d = primes[-1] + 2
            while d * d <= m:
                if m % d == 0:
                    c = 0
                    while m % d == 0:
                        m //= d
                        c += 1
                    f[d] = c
                d += 2
            if m > 1:
                f[m] = f.get(m, 0) + 1
    return f
