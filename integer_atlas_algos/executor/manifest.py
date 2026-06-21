"""Work-order loading and draft-manifest construction.

A work order is the only input the executor interprets: {start, end, columns}
(plus optional id / algorithm_release). The executor does not enforce project
conventions on it.
"""
import hashlib
import os
from datetime import datetime, timezone

from integer_atlas_algos import properties  # noqa: F401  (importing registers every column method)
from integer_atlas_algos.registry import get_methods


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_work_order(path):
    with open(path) as f:
        wo = __import__("json").load(f)
    for key in ("start", "end", "columns"):
        if key not in wo:
            raise ValueError(f"work order missing required field '{key}'")
    if wo["start"] > wo["end"]:
        raise ValueError(f"start ({wo['start']}) > end ({wo['end']})")
    if not wo["columns"]:
        raise ValueError("work order requests no columns")
    return wo


def resolve_schema(columns):
    """Return (schema, methods). `n` is always the implicit first column.

    Accepts column entries as plain names (work orders) or as
    {"name": ...} dicts (manifest column lists); `n` is ignored either way.
    """
    names = []
    for c in columns:
        name = c["name"] if isinstance(c, dict) else c
        if name != "n":
            names.append(name)
    methods = get_methods(names)  # raises UnknownColumnError
    schema = [("n", "int64")] + [(m.name, m.dtype) for m in methods]
    return schema, methods


def _new_blake3():
    """Native blake3 if installed (fast), else the bundled pure-Python fallback."""
    try:
        import blake3
        return blake3.blake3()
    except ImportError:
        from integer_atlas_algos._lib.blake3_py import Blake3
        return Blake3()


def hash_file(path):
    h256, h512, hb3 = hashlib.sha256(), hashlib.sha512(), _new_blake3()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h256.update(chunk)
            h512.update(chunk)
            hb3.update(chunk)
    return {"sha256": h256.hexdigest(), "sha512": h512.hexdigest(),
            "blake3": hb3.hexdigest()}


def draft_manifest(work_order, schema, methods, row_count, hashes, fmt, compression, out_path):
    nullable = {m.name: m.nullable for m in methods}
    columns = [
        {"name": name, "type": dt, "nullable": (False if name == "n" else nullable.get(name, True))}
        for name, dt in schema
    ]
    return {
        "filename": os.path.basename(out_path),
        "range_start": work_order["start"],
        "range_end": work_order["end"],
        "columns": columns,
        "row_count": row_count,
        "format": fmt,
        "compression": compression,
        "hashes": hashes,
        "algorithm_release": work_order.get("algorithm_release"),
        "generated_at_utc": now_utc(),
        "verification": {"status": "computed"},
    }
