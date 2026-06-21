"""Measure wall time, CPU, and peak memory for a compute run.

Builds a work order (all registered columns by default, minus any --exclude),
runs the executor in-process, and reports timing/CPU/memory from the stdlib
`resource` module. For an external cross-check, also run the same compute under
`/usr/bin/time -l` (macOS) or `/usr/bin/time -v` (Linux).

  python3 tools/perfrun.py --start 0 --end 100000 --exclude partition_count
"""
import argparse
import json
import os
import resource
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = os.path.dirname(HERE)
if ALGOS not in sys.path:
    sys.path.insert(0, ALGOS)

from integer_atlas_algos.executor import compute as C  # noqa: E402
from integer_atlas_algos import registry  # noqa: E402  (executor import below registers methods)
from integer_atlas_algos.executor import manifest as _m  # noqa: E402,F401


def _human_bytes(b):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if b < 1024 or unit == "GiB":
            return f"{b:.1f} {unit}"
        b /= 1024


def _maxrss_bytes(ru):
    # macOS reports ru_maxrss in bytes; Linux in kilobytes.
    return ru.ru_maxrss if sys.platform == "darwin" else ru.ru_maxrss * 1024


def main(argv=None):
    p = argparse.ArgumentParser(description="benchmark a compute run")
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--columns", default=None, help="comma list; default all registered")
    p.add_argument("--exclude", default=None, help="comma list of columns to drop")
    p.add_argument("--format", choices=["parquet", "csv"], default="csv")
    p.add_argument("--chunk-size", type=int, default=50000)
    p.add_argument("--out", default=None, help="output path (default: a temp file)")
    a = p.parse_args(argv)

    columns = a.columns.split(",") if a.columns else sorted(registry.REGISTRY)
    if a.exclude:
        drop = set(a.exclude.split(","))
        columns = [c for c in columns if c not in drop]

    tmpdir = tempfile.mkdtemp(prefix="ia_perf_")
    wo_path = os.path.join(tmpdir, "wo.json")
    with open(wo_path, "w") as f:
        json.dump({"id": f"perf_{a.start}_{a.end}", "start": a.start, "end": a.end,
                   "columns": columns, "algorithm_release": "perf"}, f)
    out = a.out or os.path.join(tmpdir, "shard")
    rows = a.end - a.start + 1

    print(f"columns : {len(columns)}  ({a.format})")
    print(f"range   : {a.start}..{a.end}  ({rows:,} rows)")
    print(f"chunk   : {a.chunk_size}")
    sys.stdout.flush()

    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    t0 = time.perf_counter()
    res = C.compute(wo_path, out, chunk_size=a.chunk_size, fmt=a.format, force=True)
    wall = time.perf_counter() - t0
    ru1 = resource.getrusage(resource.RUSAGE_SELF)

    ucpu = ru1.ru_utime - ru0.ru_utime
    scpu = ru1.ru_stime - ru0.ru_stime
    cpu_pct = 100.0 * (ucpu + scpu) / wall if wall else 0.0
    size = os.path.getsize(res["shard"])

    print("-" * 48)
    print(f"status        : {res['status']}  rows={res['row_count']:,}")
    print(f"wall time     : {wall:.2f} s")
    print(f"cpu (user)    : {ucpu:.2f} s")
    print(f"cpu (sys)     : {scpu:.2f} s")
    print(f"cpu util      : {cpu_pct:.0f}%")
    print(f"throughput    : {rows / wall:,.0f} rows/s  ({wall / rows * 1e6:.2f} us/row)")
    print(f"peak memory   : {_human_bytes(_maxrss_bytes(ru1))}")
    print(f"output size   : {_human_bytes(size)}  ({size / rows:.1f} B/row)")
    print(f"output        : {res['shard']}")


if __name__ == "__main__":
    main()
