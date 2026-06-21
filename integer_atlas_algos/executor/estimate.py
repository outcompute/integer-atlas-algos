"""Work estimate for a shard, computed before generation starts.

Uses each requested column's static complexity to estimate a per-row cost, times
the row count. This is deliberately coarse (and machine-independent); the Shards
planner can refine it with measured numbers from tools/bench.py. Super-linear
columns (e.g. partition_count) are flagged because a constant per-row cost
under-models them.
"""
from . import manifest as M

# Rough microseconds-per-row by complexity class (order-of-magnitude only).
COST_US_BY_COMPLEXITY = {
    "O(1)": 0.05,
    "O(b)": 0.08,
    "O(d)": 0.30,
    "O(spf)": 0.10,
    "O(sqrt n)": 0.80,
    "O(log^2 n)": 0.50,
    "O(k d)": 0.50,
    "O(steps)": 7.0,
    "O(n sqrt n)": 4000.0,
}
DEFAULT_COST_US = 1.0
SUPERLINEAR = {"O(n sqrt n)", "O(steps)"}


def estimate(work_order_path, fmt="parquet"):
    wo = M.load_work_order(work_order_path)
    rows = wo["end"] - wo["start"] + 1
    _, methods = M.resolve_schema(wo["columns"])

    columns, per_row_us, flagged = [], 0.0, []
    for m in methods:
        cost = COST_US_BY_COMPLEXITY.get(m.complexity, DEFAULT_COST_US)
        per_row_us += cost
        columns.append({"column": m.name, "complexity": m.complexity,
                        "cost_us_per_row": cost})
        if m.complexity in SUPERLINEAR:
            flagged.append(m.name)

    return {
        "rows": rows,
        "columns": columns,
        "est_us_per_row": round(per_row_us, 3),
        "est_seconds": round(rows * per_row_us / 1e6, 3),
        "superlinear_columns": flagged,
        "note": "coarse estimate from static complexity; refine with tools/bench.py",
    }


def human_seconds(s):
    if s < 1:
        return f"{s * 1000:.0f} ms"
    if s < 90:
        return f"{s:.1f} s"
    if s < 5400:
        return f"{s / 60:.1f} min"
    return f"{s / 3600:.1f} h"
