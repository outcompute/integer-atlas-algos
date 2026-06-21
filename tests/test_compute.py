import json
import logging
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = os.path.dirname(HERE)
if ALGOS not in sys.path:
    sys.path.insert(0, ALGOS)
MANIFESTS = os.path.join(HERE, "manifests")

logging.getLogger("executor").addHandler(logging.NullHandler())
logging.getLogger("executor").setLevel(logging.WARNING)

from integer_atlas_algos.executor import compute as C  # noqa: E402
from integer_atlas_algos.executor import manifest as M  # noqa: E402
from integer_atlas_algos.executor.backends import csv_backend  # noqa: E402
from integer_atlas_algos.registry import UnknownColumnError  # noqa: E402


def _rows(shard, manifest_path):
    with open(manifest_path) as f:
        cols = json.load(f)["columns"]
    schema, _ = M.resolve_schema(cols)
    return {r["n"]: r for r in csv_backend.read_table(shard, schema)}


class ComputeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _compute(self, manifest_name, chunk_size=137):
        out = os.path.join(self.tmp, "shard.csv")
        return C.compute(os.path.join(MANIFESTS, manifest_name), out,
                         chunk_size=chunk_size, fmt="csv")

    def test_basic_range(self):
        res = self._compute("base_1_1000.json")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["row_count"], 1000)
        by_n = _rows(res["shard"], res["manifest"])
        self.assertEqual(len(by_n), 1000)
        self.assertEqual(by_n[1], {"n": 1, "sign": 1, "abs_n": 1, "is_even": False,
                                   "is_odd": True, "bit_length": 1, "binary_popcount": 1,
                                   "decimal_digit_count": 1})
        self.assertEqual(by_n[2]["is_even"], True)
        self.assertEqual(by_n[7]["binary_popcount"], 3)
        self.assertEqual(by_n[1000]["bit_length"], 10)
        self.assertEqual(by_n[1000]["decimal_digit_count"], 4)

    def test_zero(self):
        res = self._compute("base_zero.json")
        row = _rows(res["shard"], res["manifest"])[0]
        self.assertEqual(row, {"n": 0, "sign": 0, "abs_n": 0, "is_even": True,
                               "is_odd": False, "bit_length": 0, "binary_popcount": 0,
                               "decimal_digit_count": 1})

    def test_negatives(self):
        res = self._compute("base_negatives.json")
        by_n = _rows(res["shard"], res["manifest"])
        self.assertEqual(by_n[-4]["sign"], -1)
        self.assertEqual(by_n[-4]["abs_n"], 4)
        self.assertEqual(by_n[-4]["is_even"], True)
        self.assertEqual(by_n[-4]["bit_length"], 3)
        self.assertEqual(by_n[-5]["binary_popcount"], 2)  # 5 = 101b

    def test_single_row(self):
        res = self._compute("base_single_row.json")
        self.assertEqual(res["row_count"], 1)
        self.assertEqual(_rows(res["shard"], res["manifest"])[7]["is_odd"], True)

    def test_unknown_column_errors_before_writing(self):
        out = os.path.join(self.tmp, "shard.csv")
        with self.assertRaises(UnknownColumnError):
            C.compute(os.path.join(MANIFESTS, "unknown_column.json"), out, fmt="csv")
        self.assertFalse(os.path.exists(out))

    def test_idempotent_rerun_is_noop(self):
        first = self._compute("base_1_1000.json")
        second = self._compute("base_1_1000.json")
        self.assertEqual(first["status"], "ok")
        self.assertEqual(second["status"], "noop")
        self.assertEqual(first["hashes"]["sha256"], second["hashes"]["sha256"])


if __name__ == "__main__":
    unittest.main()
