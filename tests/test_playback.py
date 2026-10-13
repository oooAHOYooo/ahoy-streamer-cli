import io
import contextlib
import types
import sys
import unittest
import wave
from unittest.mock import patch

sys.path.insert(0, "src")
from ahoy_streamer_cli import player


class PlaybackTests(unittest.TestCase):
    def test_ascii_luma_mapping(self):
        self.assertEqual(player.luma_to_ascii([[0, 128, 255]], width=3), " +@")
        self.assertEqual(player.luma_to_ascii([[255]], width=0), "")
        self.assertEqual(player.luma_to_ascii([[255, -10, 999]], width=3), "@ @")

    def test_bundled_decoder_decodes_synthetic_wav(self):
        try:
            import miniaudio
        except ImportError:
            self.skipTest("runtime dependency not installed")
        output = io.BytesIO()
        with wave.open(output, "wb") as file:
            file.setnchannels(1)
            file.setsampwidth(2)
            file.setframerate(8000)
            file.writeframes(b"\x00\x00" * 80)
        decoded = miniaudio.decode(output.getvalue(), nchannels=1, sample_rate=8000)
        self.assertEqual(decoded.nchannels, 1)
        self.assertEqual(decoded.sample_rate, 8000)
        self.assertEqual(len(decoded.samples), 80)

    def test_audio_session_adapter_uses_stream_and_native_device(self):
        response = io.BytesIO(b"test-stream")
        class FakeSourceBase:
            def __init__(self): pass
        fake_format = types.SimpleNamespace(MP3="mp3", WAV="wav", FLAC="flac", VORBIS="vorbis")
        fake_audio = types.SimpleNamespace(StreamableSource=FakeSourceBase, FileFormat=fake_format)
        class FakeDevice:
            callback_generator = None
            def start(self, generator):
                self.callback_generator = generator
            def stop(self):
                self.callback_generator = None
            def close(self):
                self.stop()
        class PrimedGenerator:
            closed = False
            def close(self): self.closed = True
        generator = PrimedGenerator()
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.return_value = response
            fake_audio.stream_any = unittest.mock.Mock(return_value=generator)
            fake_audio.PlaybackDevice = unittest.mock.Mock(return_value=FakeDevice())
            with patch.dict(sys.modules, {"miniaudio": fake_audio}):
                with patch.object(fake_audio, "stream_any", return_value=generator) as stream:
                    session = player.AudioSession({"type": "music", "media_url": "https://media.test/song.mp3"})
                    self.assertTrue(session.toggle_pause())
                    self.assertTrue(session.paused)
                    self.assertTrue(session.toggle_pause())
                    self.assertFalse(session.paused)
                    self.assertEqual(stream.call_args.kwargs["source_format"], fake_format.MP3)
                    self.assertIs(session.device.callback_generator, session.generator)
                    session.stop()
                    self.assertTrue(generator.closed)
                    self.assertTrue(response.closed)

    def test_unsupported_audio_extension_is_rejected_before_open(self):
        with patch("ahoy_streamer_cli.player.URLSource") as source:
            with self.assertRaisesRegex(RuntimeError, "direct MP3"):
                player.AudioSession({"type": "music", "media_url": "https://media.test/song.aac"})
        source.assert_not_called()

    def test_ascii_video_decodes_and_renders_synthetic_frame(self):
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        gray = [[0, 128, 255], [255, 128, 0]]
        class Capture:
            released = False
            def isOpened(self): return True
            def get(self, prop): return 1
            def read(self):
                if hasattr(self, "read_once"): return False, None
                self.read_once = True
                return True, frame
            def release(self): self.released = True
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(
            VideoCapture=lambda url: capture, CAP_PROP_FPS=0, INTER_AREA=1, COLOR_BGR2GRAY=2,
            resize=lambda img, size, interpolation: img,
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: gray),
        )
        output = io.StringIO()
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("shutil.get_terminal_size", return_value=types.SimpleNamespace(columns=20, lines=10)), \
             patch("ahoy_streamer_cli.player.time.sleep"), contextlib.redirect_stdout(output):
            player._play_ascii_video("https://media.test/synthetic.mp4")
        self.assertIn(" +@", output.getvalue())
        self.assertTrue(capture.released)

    def test_ascii_missing_decoder_falls_back_to_browser(self):
        video = {"type": "video", "media_url": "https://media.test/clip.mp4"}
        with patch.dict(sys.modules, {"cv2": None}), patch("webbrowser.open", return_value=True) as browser:
            result = player.play(video, "ascii")
        self.assertEqual(result, "browser-fallback")
        browser.assert_called_once_with(video["media_url"])

    def test_ascii_unsupported_stream_falls_back_to_browser(self):
        video = {"type": "video", "media_url": "https://media.test/unsupported.mp4"}
        class Capture:
            def isOpened(self): return False
            def release(self): self.released = True
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(VideoCapture=lambda url: capture)
        with patch.dict(sys.modules, {"cv2": fake_cv2}), patch("webbrowser.open", return_value=True) as browser:
            result = player.play(video, "ascii")
        self.assertEqual(result, "browser-fallback")
        self.assertTrue(capture.released)
        browser.assert_called_once_with(video["media_url"])


if __name__ == "__main__":
    unittest.main()
