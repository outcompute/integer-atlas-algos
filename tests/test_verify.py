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

from integer_atlas_algos.executor import cli  # noqa: E402
from integer_atlas_algos.executor import compute as C  # noqa: E402
from integer_atlas_algos.executor import manifest as M  # noqa: E402
from integer_atlas_algos.executor import verify as V  # noqa: E402
from integer_atlas_algos.executor.backends import csv_backend  # noqa: E402


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.shard = os.path.join(self.tmp, "shard.csv")
        self.res = C.compute(os.path.join(MANIFESTS, "base_1_1000.json"), self.shard,
                             chunk_size=137, fmt="csv")
        self.manifest = self.res["manifest"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _schema(self):
        with open(self.manifest) as f:
            cols = json.load(f)["columns"]
        schema, _ = M.resolve_schema(cols)
        return schema

    def test_full_verify_passes(self):
        result = V.verify(self.manifest, self.shard, degree=1.0)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["checked_rows"], 1000)

    def test_sampled_verify_passes(self):
        result = V.verify(self.manifest, self.shard, degree=0.1, seed=0)
        self.assertEqual(result["status"], "pass")

    def test_detects_value_corruption(self):
        schema = self._schema()
        rows = csv_backend.read_table(self.shard, schema)
        rows[500]["binary_popcount"] += 7  # corrupt one cell
        csv_backend.write_table(self.shard, schema, rows)
        result = V.verify(self.manifest, self.shard, degree=1.0)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(f["kind"] == "value" for f in result["failures"]))

    def test_detects_missing_row(self):
        schema = self._schema()
        rows = [r for r in csv_backend.read_table(self.shard, schema) if r["n"] != 250]
        csv_backend.write_table(self.shard, schema, rows)
        result = V.verify(self.manifest, self.shard, degree=1.0)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any(f["kind"] in ("row_count", "missing_row") for f in result["failures"]))

    def test_cli_exit_codes(self):
        self.assertEqual(cli.main(["verify", "--manifest", self.manifest,
                                   "--shard", self.shard, "--degree", "1.0",
                                   "--log-level", "CRITICAL"]), 0)
        # corrupt and expect exit code 3
        schema = self._schema()
        rows = csv_backend.read_table(self.shard, schema)
        rows[0]["is_even"] = not rows[0]["is_even"]
        csv_backend.write_table(self.shard, schema, rows)
        self.assertEqual(cli.main(["verify", "--manifest", self.manifest,
                                   "--shard", self.shard, "--degree", "1.0",
                                   "--log-level", "CRITICAL"]), 3)

    def test_cli_unknown_column_exit_code(self):
        out = os.path.join(self.tmp, "x.csv")
        self.assertEqual(cli.main(["compute", "--manifest",
                                   os.path.join(MANIFESTS, "unknown_column.json"),
                                   "--out", out, "--format", "csv",
                                   "--log-level", "CRITICAL"]), 2)


if __name__ == "__main__":
    unittest.main()
