"""Command-line interface to the stateless executor.

  python -m executor compute --manifest <work-order.json> --out <shard> [opts]
  python -m executor verify  --manifest <entry.json> --shard <shard> [opts]

stdout: a single JSON result line (for machine consumption / the Go CLI).
stderr: human-readable progress and logs (also to --log-file if given).
exit codes: 0 ok | 2 bad input / unknown column | 3 verification mismatch | 1 other.
"""
import argparse
import json
import logging
import shlex
import sys

from integer_atlas_algos.registry import UnknownColumnError
from . import compute as compute_mod
from . import estimate as estimate_mod
from . import verify as verify_mod

EXIT_OK, EXIT_OTHER, EXIT_BAD_INPUT, EXIT_VERIFY_FAIL = 0, 1, 2, 3


def _setup_logging(level, log_file):
    logger = logging.getLogger("executor")
    logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(fmt)
        logger.addHandler(fh)


def _build_parser():
    p = argparse.ArgumentParser(prog="atlas-algos",
                                description="Integer Atlas stateless shard executor")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compute", help="generate a shard from a work-order manifest")
    c.add_argument("--manifest", required=True, help="work order: {start, end, columns}")
    c.add_argument("--out", required=True, help="destination shard path")
    c.add_argument("--chunk-size", type=int, default=compute_mod.DEFAULT_CHUNK_SIZE)
    c.add_argument("--format", choices=["parquet", "csv"], default="parquet")
    c.add_argument("--no-resume", dest="resume", action="store_false",
                   help="ignore any checkpoint and recompute from scratch")
    c.add_argument("--force", action="store_true", help="discard existing output and rebuild")
    c.add_argument("--keep-build", action="store_true", help="keep the .build dir after success")
    c.add_argument("--dry-run", action="store_true",
                   help="print the work estimate and exit without computing")
    c.add_argument("--log-file")
    c.add_argument("--log-level", default="INFO")
    c.set_defaults(resume=True)

    v = sub.add_parser("verify", help="recompute a sample and compare against a shard")
    v.add_argument("--manifest", required=True)
    v.add_argument("--shard", required=True)
    v.add_argument("--degree", type=float, default=0.1, help="share of rows to recompute (0..1)")
    v.add_argument("--seed", type=int, default=0)
    v.add_argument("--format", choices=["parquet", "csv"], default=None)
    v.add_argument("--log-file")
    v.add_argument("--log-level", default="INFO")

    cols = sub.add_parser("columns", help="list the registered column names")
    cols.add_argument("--csv", action="store_true", help="print comma-separated")
    cols.add_argument("--json", action="store_true", help="print a JSON array")
    cols.add_argument("--log-file")
    cols.add_argument("--log-level", default="INFO")
    return p


def _eprint(msg):
    print(msg, file=sys.stderr)


def _resume_command(args):
    parts = ["atlas-algos compute",
             "--manifest", shlex.quote(args.manifest), "--out", shlex.quote(args.out)]
    if args.format != "parquet":
        parts += ["--format", args.format]
    if args.chunk_size != compute_mod.DEFAULT_CHUNK_SIZE:
        parts += ["--chunk-size", str(args.chunk_size)]
    return " ".join(parts)


def main(argv=None):
    args = _build_parser().parse_args(argv)
    _setup_logging(args.log_level, args.log_file)
    err = logging.getLogger("executor")
    try:
        if args.cmd == "compute":
            est = estimate_mod.estimate(args.manifest, fmt=args.format)
            resume = _resume_command(args)
            _eprint(f"Estimated work: {est['rows']:,} rows x {len(est['columns'])} column(s), "
                    f"~{estimate_mod.human_seconds(est['est_seconds'])} (coarse).")
            if est["superlinear_columns"]:
                _eprint("  note: super-linear column(s) "
                        f"{', '.join(est['superlinear_columns'])} may dominate; estimate is rough.")
            if args.dry_run:
                print(json.dumps(est))
                return EXIT_OK
            _eprint("Safe to interrupt (Ctrl-C) at any time — progress is checkpointed.")
            _eprint(f"Resume with:\n  {resume}")
            try:
                result = compute_mod.compute(
                    args.manifest, args.out, chunk_size=args.chunk_size, resume=args.resume,
                    force=args.force, keep_build=args.keep_build, fmt=args.format)
            except KeyboardInterrupt:
                ckpt = compute_mod.read_checkpoint(args.out, args.format) or {}
                done = ckpt.get("rows_done", 0)
                total = (ckpt.get("end", 0) - ckpt.get("start", 0) + 1) if ckpt else 0
                pct = (100.0 * done / total) if total else 0.0
                _eprint(f"\nInterrupted at {pct:.1f}% ({done}/{total} rows). Progress saved.")
                _eprint(f"Resume with:\n  {resume}")
                return 130
            print(json.dumps(result))
            return EXIT_OK
        if args.cmd == "columns":
            from integer_atlas_algos import registry
            names = sorted(registry.REGISTRY)
            if args.json:
                print(json.dumps(names))
            elif args.csv:
                print(",".join(names))
            else:
                print("\n".join(names))
            return EXIT_OK
        result = verify_mod.verify(
            args.manifest, args.shard, degree=args.degree, seed=args.seed, fmt=args.format)
        print(json.dumps(result))
        return EXIT_OK if result["status"] == "pass" else EXIT_VERIFY_FAIL
    except UnknownColumnError as e:
        err.error("%s", e)
        return EXIT_BAD_INPUT
    except (ValueError, FileNotFoundError) as e:
        err.error("%s", e)
        return EXIT_BAD_INPUT
    except compute_mod.SimulatedCrash as e:
        err.error("interrupted: %s", e)
        return EXIT_OTHER


if __name__ == "__main__":
    sys.exit(main())
