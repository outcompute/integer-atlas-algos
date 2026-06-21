# Algos executor — interface

The executor is a **Python CLI** (`atlas-algos`), runnable as a console script once
installed or as `python3 -m integer_atlas_algos.executor`. It is **stateless**: every
run is a pure function of its input manifest.

```
atlas-algos compute --manifest <work-order.json> --out <shard> [options]
atlas-algos verify  --manifest <entry.json>      --shard <shard> [options]
```

## compute — generate a shard

| Option | Default | Meaning |
| --- | --- | --- |
| `--manifest PATH` | required | work order: `{start, end, columns}` (+ optional `id`, `algorithm_release`) |
| `--out PATH` | required | destination shard path (extension normalized to the format) |
| `--format {parquet,csv}` | `parquet` | shard format. `parquet` needs pyarrow; `csv` is stdlib (dev/tests) |
| `--chunk-size N` | `50000` | rows per part / checkpoint interval — the resume granularity |
| `--force` | off | discard any existing output/checkpoint and rebuild |
| `--no-resume` | off | ignore the checkpoint and recompute from scratch (keeps `--out`) |
| `--keep-build` | off | keep the `.build` working dir after success (default: removed) |
| `--dry-run` | off | print the work estimate and exit without computing |
| `--log-file PATH` | none | also write logs here |
| `--log-level LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/… |

## verify — validate a shard

| Option | Default | Meaning |
| --- | --- | --- |
| `--manifest PATH` | required | manifest entry for the shard (`range_start`/`range_end`/`columns`) |
| `--shard PATH` | required | the shard file to check |
| `--degree F` | `0.1` | share of rows independently recomputed (0.1 sampled … 1.0 full) |
| `--seed N` | `0` | sample seed (deterministic) |
| `--format {parquet,csv}` | inferred from extension | override the shard format |
| `--log-file`, `--log-level` | | as above |

## Output

- **Shard file** at `--out` (e.g. `shard.parquet`), written atomically.
- **Manifest sidecar** at `<out>.manifest.json` — columns, types, row count, hashes
  (sha256, sha512, blake3 if available), range, `algorithm_release`, `verification.status: computed`.
- **Working dir** `<out>.build/` exists only while running (parts + `checkpoint.json`);
  removed on success unless `--keep-build`.

## stdout / stderr / logs

- **stdout**: exactly one line of JSON — the result summary — for machine consumption
  (the Go CLI parses this). Nothing else goes to stdout.
  - compute: `{"status": "ok|noop", "shard", "manifest", "row_count", "hashes"}`
  - verify: `{"status": "pass|fail", "degree", "checked_rows", "sampled", "row_count", "failures": [...]}`
- **stderr**: human-readable logs and per-chunk progress (`chunk 3/4 done (n=501..750, rows 750/1000)`).
- **log file**: same records as stderr when `--log-file` is given.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | success (compute ok/noop, or verify pass) |
| `2` | bad input — malformed work order or unknown column |
| `3` | verification mismatch (verify only) |
| `130` | interrupted (Ctrl-C) — progress checkpointed |
| `1` | other error |

## Recovery model

Parquet cannot be appended atomically per row, so resumability is by **chunked
commit + checkpoint**:

1. `[start, end]` is split into `--chunk-size` chunks (≈ one row group each).
2. Each chunk is computed in memory and written to its own part file **atomically**
   (temp → `fsync` → `rename`), then `checkpoint.json` is advanced atomically.
3. On restart, the executor **checks** the checkpoint, validates existing parts
   (presence + row counts), discards any partial/trailing temp or part beyond the
   trustworthy watermark, and **resumes from the next chunk**. At most one chunk is
   ever recomputed.
4. Finalize concatenates parts into the single shard (atomic), hashes it, and writes
   the manifest. The checkpoint phase moves `computing → finalizing → done`.

Re-running a completed work order is a **no-op** (`status: noop`) — detected from the
existing shard + manifest, so it is safe to retry blindly. Because methods are pure
and chunk ranges are deterministic, a resumed run produces byte-identical output to a
clean run (verified by the test suite).

## Work estimate, progress & interrupting

Every `compute` run prints a banner to stderr **before doing any work**:

```
Estimated work: 1,000,000 rows x 7 column(s), ~5 min (coarse).
Safe to interrupt (Ctrl-C) at any time — progress is checkpointed.
Resume with:
  atlas-algos compute --manifest wo.json --out shard.parquet --chunk-size 300
```

- **Estimate**: derived from each column's static `complexity` × row count (machine-independent, coarse). Super-linear columns (e.g. `partition_count`) are flagged because a flat per-row cost under-models them. `--dry-run` prints the full estimate as JSON and stops.
- **Progress**: each chunk logs `chunk i/N  P%  (done/total rows, eta …)` to stderr (and `--log-file`).
- **Interrupting**: Ctrl-C is safe at any moment — the chunk in flight is simply not committed, and the checkpoint always reflects the last durably-written chunk. On interrupt the executor prints the percentage reached and the exact **resume command** (re-running `compute` resumes by default), and exits with code 130.

## Running

```
# tests (stdlib unittest, zero dependencies)
python3 -m unittest discover -s tests -t .

# try it (CSV, no pyarrow needed)
atlas-algos compute --manifest tests/manifests/base_1_1000.json --out /tmp/shard --format csv
atlas-algos verify  --manifest /tmp/shard.csv.manifest.json --shard /tmp/shard.csv --degree 1.0

# real format
pip install pyarrow   # or: uv sync --extra parquet
atlas-algos compute --manifest <work-order>.json --out shard.parquet
```
