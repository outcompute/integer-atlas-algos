"""Stateless verification: recompute a sample and compare to the shard.

`degree` is the share of rows independently recomputed (0.1 sampled ... 1.0
full). The range boundaries are always included. Returns a result dict; the CLI
maps a failing result to a non-zero exit code.
"""
import logging
import math
import random

from integer_atlas_algos.context import Context
from . import manifest as M
from .atomicio import read_json
from .backends import get_backend

log = logging.getLogger("executor.verify")


def _fmt_from_path(path):
    return "parquet" if path.endswith(".parquet") else "csv"


def verify(manifest_path, shard_path, degree=0.1, seed=0, fmt=None):
    entry = read_json(manifest_path)
    start = entry.get("range_start", entry.get("start"))
    end = entry.get("range_end", entry.get("end"))
    raw_cols = entry["columns"]
    columns = [c["name"] if isinstance(c, dict) else c for c in raw_cols]
    columns = [c for c in columns if c != "n"]

    fmt = fmt or _fmt_from_path(shard_path)
    backend = get_backend(fmt)
    schema, methods = M.resolve_schema(columns)

    rows = backend.read_table(shard_path, schema)
    by_n = {r["n"]: r for r in rows}
    expected = end - start + 1
    failures = []

    if len(rows) != expected:
        failures.append({"kind": "row_count", "expected": expected, "actual": len(rows)})

    population = range(start, end + 1)
    k = min(expected, max(2, math.ceil(degree * expected)))
    sample = {start, end}
    rng = random.Random(seed)
    while len(sample) < k:
        sample.add(rng.randrange(start, end + 1))

    checked = 0
    for n in sorted(sample):
        row = by_n.get(n)
        if row is None:
            failures.append({"kind": "missing_row", "n": n})
            continue
        ctx = Context(n)
        for m in methods:
            exp = m.fn(n, ctx)
            act = row.get(m.name)
            if exp != act:
                failures.append({"kind": "value", "n": n, "column": m.name,
                                 "expected": exp, "actual": act})
        checked += 1

    # If the manifest carries hashes and we did a full recompute, also check the file hash.
    if degree >= 1.0 and entry.get("hashes", {}).get("sha256"):
        got = M.hash_file(shard_path)["sha256"]
        if got != entry["hashes"]["sha256"]:
            failures.append({"kind": "sha256", "expected": entry["hashes"]["sha256"], "actual": got})

    status = "pass" if not failures else "fail"
    log.info("verify %s: checked %d/%d rows at degree %.3f, %d failure(s)",
             status, checked, expected, degree, len(failures))
    return {
        "status": status, "degree": degree, "checked_rows": checked,
        "sampled": len(sample), "row_count": len(rows), "failures": failures[:50],
    }
