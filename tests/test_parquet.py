import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = os.path.dirname(HERE)
if ALGOS not in sys.path:
    sys.path.insert(0, ALGOS)

try:
    import pyarrow  # noqa: F401
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from integer_atlas_algos import registry  # noqa: E402
from integer_atlas_algos.executor import compute as C  # noqa: E402
from integer_atlas_algos.executor import manifest as M  # noqa: E402
from integer_atlas_algos.executor import verify as V  # noqa: E402
from integer_atlas_algos.executor.backends import csv_backend, get_backend  # noqa: E402


@unittest.skipUnless(HAS_PYARROW, "pyarrow not installed")
class ParquetTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.columns = sorted(registry.REGISTRY)  # exercises int/bool/string/double/bigint
        self.manifest = os.path.join(self.tmp, "wo.json")
        with open(self.manifest, "w") as f:
            json.dump({"id": "pq", "start": 1, "end": 60, "columns": self.columns,
                       "algorithm_release": "test"}, f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_compute_and_verify_parquet(self):
        out = os.path.join(self.tmp, "shard")
        res = C.compute(self.manifest, out, chunk_size=17, fmt="parquet")
        self.assertEqual(res["status"], "ok")
        self.assertTrue(res["shard"].endswith(".parquet"))
        self.assertEqual(res["row_count"], 60)
        result = V.verify(res["manifest"], res["shard"], degree=1.0)
        self.assertEqual(result["status"], "pass", result.get("failures"))

    def test_parquet_matches_csv(self):
        pq_out = os.path.join(self.tmp, "p")
        csv_out = os.path.join(self.tmp, "c")
        pq_res = C.compute(self.manifest, pq_out, chunk_size=17, fmt="parquet")
        csv_res = C.compute(self.manifest, csv_out, chunk_size=17, fmt="csv")
        schema, _ = M.resolve_schema(self.columns)
        pq_rows = {r["n"]: r for r in get_backend("parquet").read_table(pq_res["shard"], schema)}
        csv_rows = {r["n"]: r for r in csv_backend.read_table(csv_res["shard"], schema)}
        self.assertEqual(pq_rows, csv_rows)


if __name__ == "__main__":
    unittest.main()
