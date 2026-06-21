"""Resumable, crash-safe shard generation.

Strategy (Parquet cannot be appended atomically per row):
  - split [start, end] into fixed-size chunks (one chunk ~ one row group);
  - compute a chunk fully in memory, write it to its own part file atomically
    (temp -> fsync -> rename), then advance an atomically-written checkpoint;
  - on restart, validate existing parts against the checkpoint and resume from
    the next chunk; at most one chunk is ever recomputed;
  - finalize by concatenating parts into the single shard file (atomic), hashing
    it, and writing the draft manifest.

The executor is stateless: all of the above lives next to the output, keyed only
by the work order. Re-running a completed work order is a no-op.
"""
import logging
import os
import shutil
import time

from integer_atlas_algos.context import Context
from . import manifest as M
from .atomicio import atomic_write_json, atomic_produce, cleanup_tmp, read_json
from .backends import get_backend

log = logging.getLogger("executor.compute")

DEFAULT_CHUNK_SIZE = 50_000


class SimulatedCrash(RuntimeError):
    """Test hook: raised to mimic an interruption mid-run."""


def _chunks(start, end, size):
    out, a = [], start
    while a <= end:
        b = min(a + size - 1, end)
        out.append((a, b))
        a = b + 1
    return out


def _with_ext(path, ext):
    base = path
    for e in (".parquet", ".csv"):
        if base.endswith(e):
            base = base[: -len(e)]
    return base + ext


def _build_dir(out_path):
    return out_path + ".build"


def _part_path(bd, i, ext):
    return os.path.join(bd, f"part-{i:06d}{ext}")


def _ckpt_path(bd):
    return os.path.join(bd, "checkpoint.json")


def _manifest_path(out_path):
    return out_path + ".manifest.json"


def _rm(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _rmtree(path):
    shutil.rmtree(path, ignore_errors=True)


def _valid_watermark(bd, chunks, backend, claimed):
    """Largest i such that parts 0..i all exist with the expected row counts."""
    last = -1
    for i in range(0, claimed + 1):
        p = _part_path(bd, i, backend.EXT)
        if not os.path.exists(p):
            break
        try:
            rc = backend.count_rows(p)
        except Exception:
            break
        a, b = chunks[i]
        if rc != (b - a + 1):
            break
        last = i
    return last


def _compute_chunk(a, b, methods):
    rows = []
    for n in range(a, b + 1):
        ctx = Context(n)
        row = {"n": n}
        for m in methods:
            row[m.name] = m.fn(n, ctx)
        rows.append(row)
    return rows


def _human(seconds):
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.1f}min"
    return f"{seconds / 3600:.1f}h"


def resolve_paths(out_path, fmt):
    """(shard_path, build_dir, checkpoint_path) for an --out / --format pair."""
    p = _with_ext(out_path, get_backend(fmt).EXT)
    bd = _build_dir(p)
    return p, bd, _ckpt_path(bd)


def read_checkpoint(out_path, fmt):
    _, _, cp = resolve_paths(out_path, fmt)
    return read_json(cp) if os.path.exists(cp) else None


def _summary(out_path, status, manifest=None):
    m = manifest or read_json(_manifest_path(out_path))
    return {
        "status": status,
        "shard": out_path,
        "manifest": _manifest_path(out_path),
        "row_count": m.get("row_count"),
        "hashes": m.get("hashes"),
    }


def compute(work_order_path, out_path, chunk_size=DEFAULT_CHUNK_SIZE, resume=True,
            force=False, keep_build=False, fmt="parquet", _fault_after_chunk=None):
    wo = M.load_work_order(work_order_path)
    start, end, columns = wo["start"], wo["end"], wo["columns"]
    schema, methods = M.resolve_schema(columns)  # raises UnknownColumnError before any fs writes

    backend = get_backend(fmt)
    out_path = _with_ext(out_path, backend.EXT)
    bd = _build_dir(out_path)
    chunks = _chunks(start, end, chunk_size)
    nchunks = len(chunks)
    expected_rows = end - start + 1

    if force:
        _rm(out_path)
        _rm(_manifest_path(out_path))
        _rmtree(bd)

    # Idempotent no-op: a completed run leaves the shard + manifest behind.
    if (not force and os.path.exists(out_path) and os.path.exists(_manifest_path(out_path))
            and backend.count_rows(out_path) == expected_rows):
        log.info("already complete, nothing to do: %s", out_path)
        return _summary(out_path, "noop")

    ckpt = read_json(_ckpt_path(bd)) if os.path.exists(_ckpt_path(bd)) else None
    # A checkpoint from a different shape can't be resumed.
    if ckpt and (ckpt.get("chunk_size") != chunk_size or ckpt.get("columns") != columns
                 or ckpt.get("format") != fmt):
        log.warning("incompatible checkpoint found; starting fresh")
        ckpt = None
        _rmtree(bd)

    os.makedirs(bd, exist_ok=True)
    cleanup_tmp(bd)

    done_through = -1
    if resume and ckpt and not force:
        done_through = _valid_watermark(bd, chunks, backend, ckpt.get("last_completed_chunk", -1))
        if done_through >= 0:
            log.info("resuming after chunk %d/%d", done_through + 1, nchunks)
    # drop any parts past the trustworthy watermark
    for i in range(done_through + 1, nchunks):
        _rm(_part_path(bd, i, backend.EXT))

    rows_done = sum((b - a + 1) for a, b in chunks[: done_through + 1])
    ckpt = {
        "work_order_id": wo.get("id"),
        "start": start, "end": end, "columns": columns,
        "chunk_size": chunk_size, "num_chunks": nchunks, "format": fmt,
        "algorithm_release": wo.get("algorithm_release"),
        "last_completed_chunk": done_through, "rows_done": rows_done,
        "phase": "computing",
        "created_at": (ckpt or {}).get("created_at", M.now_utc()),
        "updated_at": M.now_utc(),
    }
    atomic_write_json(_ckpt_path(bd), ckpt)

    t0 = time.monotonic()
    rows_at_start = ckpt["rows_done"]
    for i in range(done_through + 1, nchunks):
        a, b = chunks[i]
        rows = _compute_chunk(a, b, methods)
        part = _part_path(bd, i, backend.EXT)
        atomic_produce(part, lambda tmp: backend.write_table(tmp, schema, rows))
        ckpt["last_completed_chunk"] = i
        ckpt["rows_done"] += (b - a + 1)
        ckpt["updated_at"] = M.now_utc()
        atomic_write_json(_ckpt_path(bd), ckpt)
        pct = 100.0 * ckpt["rows_done"] / expected_rows
        elapsed = time.monotonic() - t0
        done_this_run = ckpt["rows_done"] - rows_at_start
        rate = done_this_run / elapsed if elapsed > 0 else 0
        eta = (expected_rows - ckpt["rows_done"]) / rate if rate > 0 else 0
        log.info("chunk %d/%d  %.1f%%  (%d/%d rows, eta %s)",
                 i + 1, nchunks, pct, ckpt["rows_done"], expected_rows, _human(eta))
        if _fault_after_chunk is not None and i == _fault_after_chunk:
            raise SimulatedCrash(f"fault injected after chunk {i}")

    # Finalize: concatenate parts -> single shard file, atomically.
    ckpt["phase"] = "finalizing"
    ckpt["updated_at"] = M.now_utc()
    atomic_write_json(_ckpt_path(bd), ckpt)

    part_files = [_part_path(bd, i, backend.EXT) for i in range(nchunks)]

    def _concat(tmp):
        # Stream one part at a time so finalize memory stays bounded by chunk size.
        writer = backend.open_writer(tmp, schema)
        try:
            for pf in part_files:
                writer.write_table(backend.read_table(pf, schema))
        finally:
            writer.close()

    atomic_produce(out_path, _concat)

    hashes = M.hash_file(out_path)
    row_count = backend.count_rows(out_path)
    manifest = M.draft_manifest(wo, schema, methods, row_count, hashes, fmt,
                                backend.COMPRESSION, out_path)
    atomic_write_json(_manifest_path(out_path), manifest)

    ckpt["phase"] = "done"
    ckpt["row_count"] = row_count
    ckpt["hashes"] = hashes
    ckpt["updated_at"] = M.now_utc()
    atomic_write_json(_ckpt_path(bd), ckpt)

    if not keep_build:
        _rmtree(bd)
    log.info("done: %s (%d rows)", out_path, row_count)
    return _summary(out_path, "ok", manifest)
