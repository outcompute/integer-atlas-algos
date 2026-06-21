"""Importing this package registers every column method.

Add a new property by dropping a file in this directory — no other wiring.
"""
import pkgutil
from importlib import import_module
from pathlib import Path

_pkg = Path(__file__).parent
for _m in pkgutil.iter_modules([str(_pkg)]):
    if not _m.name.startswith("_"):
        import_module(f"{__name__}.{_m.name}")
