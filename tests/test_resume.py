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

WORK_ORDER = os.path.join(MANIFESTS, "base_1_1000.json")


def _rows(shard):
    with open(shard + ".manifest.json") as f:
        cols = json.load(f)["columns"]
    schema, _ = M.resolve_schema(cols)
    return csv_backend.read_table(shard, schema)


class ResumeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_crash_then_resume_matches_clean_run(self):
        # clean reference run
        clean = os.path.join(self.tmp, "clean.csv")
        ref = C.compute(WORK_ORDER, clean, chunk_size=100, fmt="csv")

        # interrupted run: crash after chunk index 2 (range 1..1000 / 100 => 10 chunks)
        crashed = os.path.join(self.tmp, "crashed.csv")
        with self.assertRaises(C.SimulatedCrash):
            C.compute(WORK_ORDER, crashed, chunk_size=100, fmt="csv", _fault_after_chunk=2)

        build = crashed + ".build"
        with open(os.path.join(build, "checkpoint.json")) as f:
            ckpt = json.load(f)
        self.assertEqual(ckpt["phase"], "computing")
        self.assertEqual(ckpt["last_completed_chunk"], 2)
        self.assertTrue(os.path.exists(os.path.join(build, "part-000002.csv")))
        self.assertFalse(os.path.exists(os.path.join(build, "part-000003.csv")))
        self.assertFalse(os.path.exists(crashed))  # no final shard yet

        # resume: should finish and produce identical output
        resumed = C.compute(WORK_ORDER, crashed, chunk_size=100, fmt="csv")
        self.assertEqual(resumed["status"], "ok")
        self.assertEqual(resumed["row_count"], 1000)
        self.assertEqual(_rows(crashed), _rows(clean))
        self.assertEqual(resumed["hashes"]["sha256"], ref["hashes"]["sha256"])
        self.assertFalse(os.path.exists(build))  # build dir cleaned on success

    def test_force_rebuilds(self):
        out = os.path.join(self.tmp, "shard.csv")
        C.compute(WORK_ORDER, out, chunk_size=100, fmt="csv")
        res = C.compute(WORK_ORDER, out, chunk_size=100, fmt="csv", force=True)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["row_count"], 1000)


if __name__ == "__main__":
    unittest.main()
