# Integer Atlas — Algos

The property methods and the compute engine (the executor). This repository is **independent and stateless**: nothing here imports the other repos, and it stores no information about any shard, pack, release, or lifecycle. It is used exactly twice per shard — `compute` (by a contributor) and `verify` (by a maintainer).

## Purpose

- Define each integer property as a small registered method.
- Provide the executor that computes shards and verifies them.
- Cut algorithm releases that downstream shards pin to.

## What lives here

Algorithms are a **single flat directory** — one method per file, the filename matching the column it produces. Pack, shard, and release names never appear in the layout. Shared helpers live in `_lib`. There are no work-order or manifest files here — those live in the Shards repository.

```
integer_atlas_algos/        the installable package (atlas-algos)
  registry.py               @property_method + the flat column registry
  context.py                per-n memoized context (factorization, divisors)
  properties/               one method per file; filename = column name (47 columns)
  _lib/                     shared helpers
    factorization.py        prime-table factorization
    multiplicative.py       sigma() shared by divisor functions
    blake3_py.py            pure-Python BLAKE3 fallback
  precomputed/              regenerable resource cache (not state)
    primes_le_31623.txt     base primes up to ceil(sqrt(1e9))
  executor/                 the stateless engine
    cli.py                  argparse CLI (compute / verify, estimate, resume)
    compute.py              chunked, resumable, crash-safe, streaming finalize
    verify.py               sampled recompute + compare
    estimate.py             pre-run work estimate from static complexity
    manifest.py             work-order loading, draft manifest, hashing
    atomicio.py             atomic write / checkpoint primitives
    backends/               csv_backend (stdlib) + parquet_backend (pyarrow)
tools/                      bench.py, perfrun.py, make_work_order.py (dev only)
tests/                      unittest suite + sample work-order manifests
pyproject.toml              package metadata, console script, extras
COMMANDS.md  INTERFACE.md           reference docs
```

Run it with `pip install -e .` then `atlas-algos …`, or from a source checkout as
`python3 -m integer_atlas_algos.executor …` (run from the repository root).

All 47 properties are implemented. See [INTERFACE.md](INTERFACE.md) for the
complete command reference, output layout, exit codes, and the resume model.

## Precomputed data

To factor any n up to BOUND² you only need primes up to BOUND; with
BOUND = 31623 (≥ √1e9) that is ~3401 primes covering the whole 0..1e9 range.
`precomputed/primes_le_31623.txt` holds them — a deterministic, regenerable cache
(sieved on first use if missing), not state about any shard or pack. It bounds
worst-case factorization to ~3401 trial divisions regardless of n's size in range.

## Limitations

- A single shard is computed single-threaded (~3,700 rows/s/core in pure Python);
  scale by computing many shards concurrently, one process each.
- `n` is stored as int64 (covers 0..2^63).
- `partition_count` is practical only for small n — its values grow to hundreds of
  digits — so omit it from large ranges.

## Method contract

- Signature is `f(n, ctx) -> value`. The method **name becomes the column name**.
- `ctx` is a memoized context of shared intermediates (factorization, divisor list, binary representation) declared via `requires`, so expensive work is computed once per number, not once per method.
- Metadata (canonical column id, dtype, nullable, zero/negative behavior, `requires`, test vectors) is registered next to the function, so the schema, column ids, and manifest columns are generated from code. A method declares **only its own column** — it says nothing about packs, shards, releases, or any other entity.
- A method may provide an optional **vectorized fast-path** for speed; the **scalar form is always the verification ground truth**.
- **Test vectors live with the method** and are reused by both the property-proposal gate and shard verification.

## Executor verbs

The executor is **stateless** — both verbs are pure functions of an input manifest that names a `start`, an `end`, and the requested columns. It does not interpret packs, the grid, or policy; if the manifest does not follow project conventions that is fine, and it errors only if a requested column name is unknown.

- `compute --manifest <work-order> --out <shard>` — run the requested column functions over `[start, end]` and write the shard, filling the output manifest's column types and hashes from the method metadata.
- `verify --manifest <entry> --shard <file> --degree <fraction>` — recompute a share of the requested columns (0.1 sampled … 1.0 full) and compare against the shard; report pass/fail.

## Releases

Cut an algorithm release once enough methods have merged. It is stamped with the commit id and PR URLs, and is what a shard's `algorithm_versions` pins to. Only released methods are eligible for official shards; unreleased methods exist only for local side-loading.

## Packaging

Published to PyPI as `integer-atlas-algos`; install with `pip install integer-atlas-algos`
(add the `parquet` extra for Parquet output, `hash` for the native BLAKE3 speedup).
Factorization speed comes from the precomputed prime table; native libraries
(gmpy2, primesieve) and a column's optional vectorized fast-path can speed it further.

## State: none

This repository stores no information about any shard, release, or lifecycle — work
orders and manifests live in the Shards repository. The executor sees a given shard
exactly twice: `compute` (by a contributor) and `verify` (by a maintainer).

## Contributing

Add an algorithm by dropping a file in `properties/` (one method per file) with its
metadata and test vectors, then open a pull request. See [INTERFACE.md](INTERFACE.md)
for the method contract.
