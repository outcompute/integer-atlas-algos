import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = os.path.dirname(HERE)
if ALGOS not in sys.path:
    sys.path.insert(0, ALGOS)

from integer_atlas_algos._lib.blake3_py import Blake3, blake3_hexdigest  # noqa: E402

# Official BLAKE3 test vectors. Input of length n is the bytes (i % 251).
# Values are the first 64 hex chars (the standard 32-byte digest).
# Covers: empty, sub-block, exact block (64), multi-block single chunk (1023),
# and multi-chunk tree merges (1025, 2048, 3072).
VECTORS = {
    0: "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262",
    1: "2d3adedff11b61f14c886e35afa036736dcd87a74d27b5c1510225d0f592e213",
    2: "7b7015bb92cf0b318037702a6cdd81dee41224f734684c2c122cd6359cb1ee63",
    3: "e1be4d7a8ab5560aa4199eea339849ba8e293d55ca0a81006726d184519e647f",
    64: "4eed7141ea4a5cd4b788606bd23f46e212af9cacebacdc7d1f4c6dc7f2511b98",
    1023: "10108970eeda3eb932baac1428c7a2163b0e924c9a9e25b35bba72b28f70bd11",
    1024: "42214739f095a406f3fc83deb889744ac00df831c10daa55189b5d121c855af7",
    1025: "d00278ae47eb27b34faecf67b4fe263f82d5412916c1ffd97c8cb7fb814b8444",
    2048: "e776b6028c7cd22a4d0ba182a8bf62205d2ef576467e838ed6f2529b85fba24a",
    3072: "b98cb0ff3623be03326b373de6b9095218513e64f1ee2edd2525c7ad1e5cffd2",
}


def _make_input(n):
    return bytes(i % 251 for i in range(n))


class Blake3Test(unittest.TestCase):
    def test_official_vectors(self):
        for n, expected in VECTORS.items():
            self.assertEqual(blake3_hexdigest(_make_input(n)), expected, f"input_len={n}")

    def test_streaming_matches_oneshot(self):
        data = _make_input(5000)
        oneshot = Blake3().update(data).hexdigest()
        chunked = Blake3()
        for i in range(0, len(data), 7):
            chunked.update(data[i:i + 7])
        self.assertEqual(chunked.hexdigest(), oneshot)

    def test_matches_native_if_installed(self):
        try:
            import blake3
        except ImportError:
            self.skipTest("native blake3 not installed")
        for n in (0, 1, 100, 1024, 1025, 4096):
            data = _make_input(n)
            self.assertEqual(blake3_hexdigest(data), blake3.blake3(data).hexdigest())


if __name__ == "__main__":
    unittest.main()
