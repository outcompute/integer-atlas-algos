"""Flat registry of column methods.

Each property method registers only its own column, plus light metadata:
its dtype, time complexity (Big-O, static and machine-independent), and a few
test vectors. Packs, shards, releases, and the lifecycle are unknown here — that
state lives in the Shards repo. Sample timings are NOT stored here; they are
machine-specific and produced by tools/bench.py to seed the planner cost model.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple


class UnknownColumnError(Exception):
    def __init__(self, columns):
        self.columns = list(columns)
        super().__init__("unknown column(s): " + ", ".join(self.columns))


@dataclass(frozen=True)
class Method:
    name: str
    dtype: str
    nullable: bool
    requires: Tuple[str, ...]
    complexity: Optional[str]
    test_vectors: dict
    fn: Callable


REGISTRY: dict[str, Method] = {}


def property_method(name, dtype, nullable=False, requires=(), complexity=None,
                    test_vectors=None):
    """Register a column function. The name becomes the column name.

    complexity: Big-O in the input (n value, b=bit length, d=decimal digits).
    test_vectors: {n: expected, ...}, reused by the property gate and verification.
    """
    def deco(fn):
        if name in REGISTRY:
            raise ValueError(f"duplicate column method: {name}")
        REGISTRY[name] = Method(name, dtype, nullable, tuple(requires),
                                complexity, dict(test_vectors or {}), fn)
        return fn
    return deco


def get_methods(columns):
    missing = [c for c in columns if c not in REGISTRY]
    if missing:
        raise UnknownColumnError(missing)
    return [REGISTRY[c] for c in columns]
