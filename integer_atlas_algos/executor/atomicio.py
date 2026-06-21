"""Crash-safe file primitives.

Every durable write goes to a temp file in the same directory, is fsync'd, then
atomically renamed into place (os.replace). The containing directory is fsync'd
so the rename itself survives a crash. A partial temp file is never visible under
the real name, so a reader either sees the previous version or the new one.
"""
import json
import os
import tempfile


def _fsync_file(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(d):
    try:
        fd = os.open(d, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        # Some platforms disallow fsync on a directory; the rename is still atomic.
        pass


def _safe_unlink(path):
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def atomic_write_bytes(path, data: bytes):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        _fsync_dir(d)
    except BaseException:
        _safe_unlink(tmp)
        raise


def atomic_write_text(path, text: str):
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path, obj):
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=True))


def atomic_produce(path, writer):
    """Atomically create `path` via writer(tmp_path), which writes the whole file.

    Used for backends (e.g. Parquet) that write their own file format.
    """
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".part")
    os.close(fd)
    try:
        writer(tmp)
        _fsync_file(tmp)
        os.replace(tmp, path)
        _fsync_dir(d)
    except BaseException:
        _safe_unlink(tmp)
        raise


def read_json(path):
    with open(path) as f:
        return json.load(f)


def cleanup_tmp(directory):
    if not os.path.isdir(directory):
        return
    for name in os.listdir(directory):
        if name.startswith(".tmp-"):
            _safe_unlink(os.path.join(directory, name))
