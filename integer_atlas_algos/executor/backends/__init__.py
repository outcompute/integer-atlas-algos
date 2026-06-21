"""Pluggable shard file backends.

The resume/checkpoint/atomic machinery in compute.py is format-agnostic; a
backend only knows how to write/read/count one file. `csv` is stdlib and always
available (handy for dev and tests); `parquet` is the real shard format and
needs pyarrow.
"""


def get_backend(name):
    if name == "csv":
        from . import csv_backend
        return csv_backend
    if name == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "parquet format requires pyarrow (pip install pyarrow). "
                "For a dependency-free run use --format csv."
            ) from e
        from . import parquet_backend
        return parquet_backend
    raise ValueError(f"unknown format: {name}")
