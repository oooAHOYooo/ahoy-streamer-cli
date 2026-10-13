import json
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ahoy_streamer_cli import catalog
from ahoy_streamer_cli.config import base_url


class CoreTests(unittest.TestCase):
    def test_normalization_id_precedence_and_video(self):
        music = catalog.normalize("music", {"id": "legacy", "track_id": "preferred", "title": "Song", "audio_url": "https://x.test/a"})
        video = catalog.normalize("video", {"show_id": "film", "title": "Film", "video_url": "https://x.test/v", "host": "Host"})
        self.assertEqual(music["id"], "music:preferred")
        self.assertEqual(video["creator"], "Host")

    def test_unsafe_origin_rejected(self):
        with self.assertRaises(ValueError):
            base_url("http://example.com")
        self.assertEqual(base_url("http://localhost:9000/"), "http://localhost:9000")

    def test_duplicate_conflicts_rejected(self):
        payload = {"tracks": [{"track_id": "1", "title": "A"}, {"track_id": "1", "title": "B"}]}
        with patch.object(catalog, "fetch", return_value=payload):
            with self.assertRaisesRegex(ValueError, "conflicting duplicate"):
                catalog.catalog("music", "https://example.test")

    def test_fixture_shapes_are_valid(self):
        for path, kind, key in (("fixtures/music.json", "music", "tracks"), ("fixtures/shows.json", "video", "shows")):
            with open(path, encoding="utf-8") as f:
                rows = json.load(f)[key]
            self.assertTrue(all(catalog.normalize(kind, row) for row in rows))


if __name__ == "__main__":
    unittest.main()
