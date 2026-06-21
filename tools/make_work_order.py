"""Dev helper: emit a work-order manifest for a range.

By default it requests *all currently registered* columns, so it stays current
as properties are added. This mimics what the Shards planner would emit; the
stateless executor just consumes the result.

  python tools/make_work_order.py --start 1 --end 100 --out wo.json
  python tools/make_work_order.py --start 1 --end 100 --columns is_even,integer_sqrt
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = os.path.dirname(HERE)
if ALGOS not in sys.path:
    sys.path.insert(0, ALGOS)

from integer_atlas_algos.executor import manifest  # noqa: E402,F401  (import registers all methods)
from integer_atlas_algos import registry  # noqa: E402


def main(argv=None):
    p = argparse.ArgumentParser(description="emit a work-order manifest")
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--columns", default=None,
                   help="comma-separated; default = all registered columns")
    p.add_argument("--exclude", default=None, help="comma-separated columns to drop")
    p.add_argument("--id", default=None)
    p.add_argument("--algorithm-release", default="dev")
    p.add_argument("--out", default=None, help="write here instead of stdout")
    a = p.parse_args(argv)

    columns = a.columns.split(",") if a.columns else sorted(registry.REGISTRY)
    if a.exclude:
        drop = set(a.exclude.split(","))
        columns = [c for c in columns if c not in drop]
    wo = {
        "id": a.id or f"all_{a.start}_{a.end}",
        "start": a.start,
        "end": a.end,
        "columns": columns,
        "algorithm_release": a.algorithm_release,
    }
    text = json.dumps(wo, indent=2)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text + "\n")
        print(f"wrote {a.out} ({len(columns)} columns, n={a.start}..{a.end})", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
