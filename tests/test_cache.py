import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from worldcup import cache


class CacheTest(unittest.TestCase):
    def test_vercel_writes_to_tmp_runtime_cache(self):
        data = {"metadata": {"refreshed_at": "2026-06-18T00:00:00+00:00"}, "matches": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            runtime_cache = Path(tmpdir) / "matches.json"
            with patch.dict(
                cache.os.environ,
                {"VERCEL": "1", "WORLD_CUP_CACHE_FILE": str(runtime_cache)},
                clear=False,
            ):
                cache._write_cache(data)

            self.assertEqual(json.loads(runtime_cache.read_text(encoding="utf-8")), data)

    def test_read_prefers_runtime_cache_over_bundled_cache(self):
        bundled = {"metadata": {"source": "bundled"}, "matches": []}
        runtime = {"metadata": {"source": "runtime"}, "matches": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            bundled_cache = Path(tmpdir) / "data" / "matches.json"
            runtime_cache = Path(tmpdir) / "runtime" / "matches.json"
            bundled_cache.parent.mkdir()
            runtime_cache.parent.mkdir()
            bundled_cache.write_text(json.dumps(bundled), encoding="utf-8")
            runtime_cache.write_text(json.dumps(runtime), encoding="utf-8")

            with patch.object(cache, "BUNDLED_CACHE_FILE", bundled_cache):
                with patch.dict(cache.os.environ, {"WORLD_CUP_CACHE_FILE": str(runtime_cache)}, clear=False):
                    self.assertEqual(cache._read_cache(), runtime)

    def test_read_falls_back_to_bundled_cache(self):
        bundled = {"metadata": {"source": "bundled"}, "matches": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            bundled_cache = Path(tmpdir) / "data" / "matches.json"
            runtime_cache = Path(tmpdir) / "runtime" / "matches.json"
            bundled_cache.parent.mkdir()
            bundled_cache.write_text(json.dumps(bundled), encoding="utf-8")

            with patch.object(cache, "BUNDLED_CACHE_FILE", bundled_cache):
                with patch.dict(cache.os.environ, {"WORLD_CUP_CACHE_FILE": str(runtime_cache)}, clear=False):
                    self.assertEqual(cache._read_cache(), bundled)


if __name__ == "__main__":
    unittest.main()
