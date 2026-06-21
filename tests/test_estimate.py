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
from integer_atlas_algos.executor import estimate as E  # noqa: E402


class EstimateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_estimate_shape(self):
        est = E.estimate(os.path.join(MANIFESTS, "base_1_1000.json"), fmt="csv")
        self.assertEqual(est["rows"], 1000)
        self.assertEqual(len(est["columns"]), 7)
        self.assertGreater(est["est_seconds"], 0)
        self.assertTrue(all(c["complexity"] for c in est["columns"]))

    def test_dry_run_writes_nothing(self):
        out = os.path.join(self.tmp, "shard")
        rc = cli.main(["compute", "--manifest", os.path.join(MANIFESTS, "base_1_1000.json"),
                       "--out", out, "--format", "csv", "--dry-run", "--log-level", "CRITICAL"])
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(out + ".csv"))
        self.assertFalse(os.path.exists(out + ".csv.build"))


if __name__ == "__main__":
    unittest.main()
