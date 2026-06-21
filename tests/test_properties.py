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

logging.getLogger("executor").addHandler(logging.NullHandler())
logging.getLogger("executor").setLevel(logging.WARNING)

from integer_atlas_algos import registry  # noqa: E402
from integer_atlas_algos.context import Context  # noqa: E402
from integer_atlas_algos.executor import compute as C  # noqa: E402
from integer_atlas_algos.executor import manifest as M  # noqa: E402  (import registers all methods)
from integer_atlas_algos.executor import verify as V  # noqa: E402
from integer_atlas_algos.executor.backends import csv_backend  # noqa: E402


def _all_columns_work_order(tmp, start, end):
    columns = sorted(registry.REGISTRY)
    wo = {"id": f"all_{start}_{end}", "start": start, "end": end,
          "columns": columns, "algorithm_release": "test"}
    path = os.path.join(tmp, "wo.json")
    with open(path, "w") as f:
        json.dump(wo, f)
    return path, columns


def _read(shard, manifest_path):
    with open(manifest_path) as f:
        schema, _ = M.resolve_schema(json.load(f)["columns"])
    return {r["n"]: r for r in csv_backend.read_table(shard, schema)}


class PropertyTest(unittest.TestCase):
    def test_every_method_has_complexity_and_passes_its_vectors(self):
        self.assertTrue(registry.REGISTRY, "no methods registered")
        for name, m in registry.REGISTRY.items():
            self.assertIsNotNone(m.complexity, f"{name} missing complexity")
            for n, expected in m.test_vectors.items():
                got = m.fn(n, Context(n))
                self.assertEqual(got, expected, f"{name}({n}) = {got!r}, expected {expected!r}")

    def test_full_pack_compute_and_verify(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        columns = sorted(registry.REGISTRY)
        wo = {"id": "all", "start": 1, "end": 30, "columns": columns,
              "algorithm_release": "test"}
        manifest = os.path.join(tmp, "wo.json")
        with open(manifest, "w") as f:
            json.dump(wo, f)
        out = os.path.join(tmp, "shard.csv")

        res = C.compute(manifest, out, chunk_size=7, fmt="csv")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["row_count"], 30)

        result = V.verify(res["manifest"], res["shard"], degree=1.0)
        self.assertEqual(result["status"], "pass", result.get("failures"))

    def test_first_100_all_properties(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        manifest, columns = _all_columns_work_order(tmp, 1, 100)
        out = os.path.join(tmp, "first100.csv")

        res = C.compute(manifest, out, chunk_size=32, fmt="csv")
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["row_count"], 100)

        result = V.verify(res["manifest"], res["shard"], degree=1.0)
        self.assertEqual(result["status"], "pass", result.get("failures"))

        rows = _read(res["shard"], res["manifest"])
        self.assertEqual(set(rows), set(range(1, 101)))
        r100 = rows[100]
        self.assertEqual(r100["integer_sqrt"], 10)
        self.assertEqual(r100["is_square"], True)
        self.assertEqual(r100["binary_repr"], "1100100")
        self.assertEqual(r100["octal_repr"], "144")
        self.assertEqual(r100["hex_repr"], "64")
        self.assertEqual(r100["is_happy"], True)
        self.assertEqual(r100["gcd_sum_pillai"], 520)
        self.assertEqual(r100["von_mangoldt"], 0.0)
        self.assertEqual(r100["partition_count"], 190569292)
        self.assertEqual(r100["omega_distinct"], 2)
        self.assertEqual(r100["divisor_count"], 9)
        self.assertEqual(r100["divisor_sum"], 217)
        self.assertEqual(r100["euler_phi"], 40)
        self.assertEqual(r100["mobius"], 0)
        self.assertEqual(rows[89]["is_fibonacci"], True)
        self.assertEqual(rows[91]["is_triangular"], True)  # T13 = 91
        self.assertEqual(rows[97]["is_prime"], True)
        self.assertEqual(rows[28]["is_perfect"], True)
        self.assertEqual(rows[12]["abundance_class"], "abundant")


if __name__ == "__main__":
    unittest.main()
