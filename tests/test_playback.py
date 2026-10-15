import io
import contextlib
import types
import sys
import unittest
import wave
from contextlib import contextmanager
from unittest.mock import patch

sys.path.insert(0, "src")
from ahoy_streamer_cli import player


class PlaybackTests(unittest.TestCase):
    def test_ascii_luma_mapping(self):
        self.assertEqual(player.luma_to_ascii([[0, 128, 255]], width=3), " +@")
        self.assertEqual(player.luma_to_ascii([[255]], width=0), "")
        self.assertEqual(player.luma_to_ascii([[255, -10, 999]], width=3), "@ @")

    def test_braille_rendering_uses_two_by_four_detail_and_timeline(self):
        dark = [[0, 0] for _ in range(4)]
        bright = [[255, 255] for _ in range(4)]
        self.assertEqual(player.luma_to_braille(dark, 1, 1), "\u2800")
        self.assertEqual(player.luma_to_braille(bright, 1, 1), "\u28ff")
        self.assertEqual(len(player._video_timeline(5, 10, 12)), 12)
        self.assertEqual(player._time_label(65), "01:05")

    def test_hybrid_renderer_uses_grayscale_cell_fills_and_braille_detail(self):
        flat = player.luma_to_hybrid([[128, 128] for _ in range(4)], 1, 1)
        self.assertIn("\x1b[48;2;128;128;128m", flat)
        self.assertIn("\u2800", flat)
        self.assertNotIn("\x1b[38;5;", flat)

        detailed = player.luma_to_hybrid([[0, 255] for _ in range(4)], 1, 1)
        self.assertIn("\x1b[48;2;128;128;128m", detailed)
        self.assertIn("\x1b[38;2;8;8;8m", detailed)
        self.assertTrue(any(0x2800 < ord(ch) <= 0x28ff for ch in detailed))

    def test_contrast_and_full_range_two_pixel_grayscale_cells(self):
        self.assertEqual(player._enhance_luma([[64, 128, 192]]), [[45, 128, 211]])
        rendered = player.luma_to_gray_blocks([[0, 64], [192, 255]])
        self.assertEqual(rendered.count("▀"), 2)
        self.assertIn("\x1b[38;2;0;0;0m", rendered)
        self.assertIn("\x1b[48;2;192;192;192m", rendered)
        self.assertIn("\x1b[48;2;255;255;255m", rendered)
        self.assertIn("\x1b[0m", rendered)

    def test_quadrant_renderer_uses_four_gray_samples_per_terminal_cell(self):
        rendered = player.luma_to_gray_quadrants([[0, 255, 0, 255],
                                                   [0, 255, 0, 255]], 2, 1)
        self.assertIn("▐", rendered)
        self.assertIn("\x1b[38;2;255;255;255m", rendered)
        self.assertIn("\x1b[48;2;0;0;0m", rendered)

    def test_soft_focus_blends_neighbors_without_changing_image_dimensions(self):
        source = [[0, 0, 255], [0, 255, 255], [0, 0, 255]]
        softened = player._soften_luma(source)
        self.assertEqual([len(row) for row in softened], [3, 3, 3])
        self.assertGreater(softened[1][0], 0)
        self.assertLess(softened[1][1], 255)
        self.assertEqual(source[1][0], 0)

    def test_video_key_sequences_decode_arrows_and_do_not_decode_escape_as_quit(self):
        cases = {
            "\x1b[A": "up", "\x1b[B": "down", "\xe0H": "up", "\xe0P": "down",
            "\x1b[D": "left", "\x1b[C": "right", "\x1b[1;5D": "left",
            "\x1b[H": "home", "\x1bOF": "end", "\x1b[1~": "home",
            "\x1b[4~": "end", "\xe0K": "left",
            "\xe0M": "right", "\x00G": "home", "\x00O": "end",
            "\x1b": None, "\x1b[Z": None,
        }
        for sequence, expected in cases.items():
            with self.subTest(sequence=sequence):
                self.assertEqual(player._decode_key_sequence(sequence), expected)

    def test_video_browser_renders_safe_scrolling_list(self):
        items = [{"title": f"Video {n}"} for n in range(12)]
        items[8]["title"] = "Unsafe\x1b[2J\x07 title"
        view = player._video_browser_view("frame", "[timeline]", items, 8, 26, 50, 0, 6)
        self.assertIn("VIDEOS ↑↓ Enter  9/12", view)
        self.assertIn("▶ Unsafe title", view)
        self.assertNotIn("\x1b[2J", view)
        self.assertIn("[timeline]", view)

    def test_video_browser_selects_another_video_while_playing(self):
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        class Capture:
            released = False
            def isOpened(self): return True
            def get(self, prop): return 20
            def read(self): return True, frame
            def release(self): self.released = True
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(
            VideoCapture=lambda url: capture, CAP_PROP_FPS=0, INTER_AREA=1, COLOR_BGR2GRAY=2,
            resize=lambda img, size, interpolation: img,
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: [[0] * 6 for _ in range(2)]))
        keys = iter(([], ["down"], ["\r"]))
        @contextmanager
        def key_reader():
            yield lambda: next(keys, [])
        soundtrack = unittest.mock.Mock()
        soundtrack.start.return_value = True
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack", return_value=soundtrack), \
             patch("ahoy_streamer_cli.player._terminal_keys", return_value=key_reader()), \
             patch("ahoy_streamer_cli.player.time.sleep"), contextlib.redirect_stdout(io.StringIO()):
            result = player._play_ascii_video("https://media.test/1.mp4",
                                              browse_items=[{"title": "One"}, {"title": "Two"}])
        self.assertEqual(result, ("select", 1))
        self.assertTrue(capture.released)
        soundtrack.stop.assert_called_once()

    def test_full_screen_toggle_keeps_paused_frame_and_browse_selection(self):
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        class Capture:
            reads = 0
            def isOpened(self): return True
            def get(self, prop): return 20
            def read(self):
                self.reads += 1
                return True, frame
            def release(self): pass
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(
            VideoCapture=lambda url: capture, CAP_PROP_FPS=0, INTER_AREA=1, COLOR_BGR2GRAY=2,
            resize=lambda img, size, interpolation: img,
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: [[0] * 6 for _ in range(2)]))
        keys = iter(([], [" "], [], ["f"], [], ["\t"], ["q"]))
        @contextmanager
        def key_reader():
            yield lambda: next(keys, ["q"])
        soundtrack = unittest.mock.Mock()
        soundtrack.start.return_value = True
        soundtrack.toggle_pause.return_value = True
        output = io.StringIO()
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack", return_value=soundtrack), \
             patch("ahoy_streamer_cli.player._terminal_keys", return_value=key_reader()), \
             patch("ahoy_streamer_cli.player.time.sleep"), \
             patch("shutil.get_terminal_size", return_value=types.SimpleNamespace(columns=80, lines=24)), \
             contextlib.redirect_stdout(output):
            result = player._play_ascii_video("https://media.test/1.mp4",
                                              browse_items=[{"title": "One"}, {"title": "Two"}],
                                              browse_index=1)
        self.assertEqual(result, ("back", 1))
        self.assertEqual(capture.reads, 1)
        self.assertIn("FULL SCREEN", output.getvalue())
        self.assertIn("BROWSE", output.getvalue())
        soundtrack.toggle_pause.assert_called_once()

    @unittest.skipIf(sys.platform == "win32", "uses a POSIX pseudo-terminal")
    def test_terminal_reader_consumes_complete_csi_arrow_sequences(self):
        import os
        import pty

        master, slave = pty.openpty()
        class TerminalInput:
            def isatty(self): return True
            def fileno(self): return slave
        try:
            with patch.object(player.sys, "stdin", TerminalInput()):
                with player._terminal_keys() as read_keys:
                    os.write(master, b"\x1b[D\x1b[C\x1b[1;5D")
                    self.assertEqual(read_keys(), ["left", "right", "left"])
        finally:
            os.close(master)
            os.close(slave)

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

    def test_unsupported_audio_extension_is_rejected_and_source_closed(self):
        fake_audio = types.SimpleNamespace(FileFormat=types.SimpleNamespace(
            MP3=1, WAV=2, FLAC=3, VORBIS=4, UNKNOWN=0))
        source = types.SimpleNamespace(response=types.SimpleNamespace(headers={}), close=unittest.mock.Mock())
        with patch.dict(sys.modules, {"miniaudio": fake_audio}), \
             patch("ahoy_streamer_cli.player.URLSource", return_value=types.SimpleNamespace(source=source)):
            with self.assertRaises(player.UnsupportedAudioFormat):
                player.AudioSession({"type": "music", "media_url": "https://media.test/song.aac"})
        source.close.assert_called_once()

    def test_signed_audio_url_uses_header_format_or_sniffing(self):
        fake_audio = types.SimpleNamespace(FileFormat=types.SimpleNamespace(
            MP3=1, WAV=2, FLAC=3, VORBIS=4, UNKNOWN=0))
        with patch.dict(sys.modules, {"miniaudio": fake_audio}):
            self.assertEqual(player._audio_format("https://media.test/stream?token=abc", "audio/mpeg"), 1)
            self.assertEqual(player._audio_format("https://media.test/stream?token=abc"), 0)

    def test_undetected_audio_decoder_failure_uses_browser_fallback(self):
        fake_audio = types.SimpleNamespace(
            FileFormat=types.SimpleNamespace(MP3=1, WAV=2, FLAC=3, VORBIS=4, UNKNOWN=0),
            stream_any=lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("unknown container")),
        )
        source = types.SimpleNamespace(response=types.SimpleNamespace(headers={}), close=unittest.mock.Mock())
        audio = {"type": "podcast", "media_url": "https://media.test/stream?token=abc"}
        with patch.dict(sys.modules, {"miniaudio": fake_audio}), \
             patch("ahoy_streamer_cli.player.audio_backend_ready", return_value=True), \
             patch("ahoy_streamer_cli.player.URLSource", return_value=types.SimpleNamespace(source=source)), \
             patch("webbrowser.open", return_value=True) as browser:
            self.assertEqual(player.play(audio), "browser-fallback")
        source.close.assert_called_once()
        browser.assert_called_once_with(audio["media_url"])

    def test_unsupported_native_audio_opens_browser(self):
        audio = {"type": "podcast", "media_url": "https://media.test/episode.m4a"}
        with patch("ahoy_streamer_cli.player.audio_backend_ready", return_value=True), \
             patch("ahoy_streamer_cli.player.AudioSession", side_effect=player.UnsupportedAudioFormat), \
             patch("webbrowser.open", return_value=True) as browser:
            self.assertEqual(player.play(audio), "browser-fallback")
        browser.assert_called_once_with(audio["media_url"])

    @unittest.skipIf(sys.platform == "win32", "SIGSTOP is unavailable on Windows")
    def test_window_player_space_pause_sends_stop_and_continue(self):
        import signal
        session = player.PlayerSession()
        session.process = unittest.mock.Mock()
        session.current = {"type": "video", "title": "Sample"}
        self.assertTrue(session.toggle_pause())
        self.assertTrue(session.toggle_pause())
        self.assertEqual(session.process.send_signal.call_args_list,
                         [unittest.mock.call(signal.SIGSTOP), unittest.mock.call(signal.SIGCONT)])

    def test_ascii_video_space_pauses_and_q_exits(self):
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        class Capture:
            released = False
            def isOpened(self): return True
            def get(self, prop): return 20
            def read(self):
                if hasattr(self, "read_once"):
                    raise AssertionError("paused video should not decode another frame")
                self.read_once = True
                return True, frame
            def release(self): self.released = True
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(
            VideoCapture=lambda url: capture, CAP_PROP_FPS=0, INTER_AREA=1, COLOR_BGR2GRAY=2,
            resize=lambda img, size, interpolation: img,
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: [[0] * 6 for _ in range(2)]))
        @contextmanager
        def keys():
            yield iter((" ", "q")).__next__
        soundtrack = unittest.mock.Mock()
        soundtrack.start.return_value = True
        soundtrack.toggle_pause.return_value = True
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack", return_value=soundtrack), \
             patch("ahoy_streamer_cli.player._terminal_keys", return_value=keys()), \
             patch("ahoy_streamer_cli.player.time.sleep"), contextlib.redirect_stdout(io.StringIO()):
            player._play_ascii_video("https://media.test/synthetic.mp4")
        self.assertTrue(capture.released)
        soundtrack.toggle_pause.assert_called_once()
        soundtrack.stop.assert_called_once()

    def test_ascii_video_seek_keys_update_decoder_position(self):
        class Capture:
            def __init__(self): self.positions = []
            def isOpened(self): return True
            def get(self, prop): return 20
            def set(self, prop, value):
                self.positions.append((prop, value))
                return True
            def read(self): raise AssertionError("q should exit before decoding")
            def release(self): pass
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(VideoCapture=lambda url: capture,
            CAP_PROP_FPS=5, CAP_PROP_FRAME_COUNT=7, CAP_PROP_POS_MSEC=0)
        keys = iter(("left", "right", "home", "end", "q"))
        @contextmanager
        def key_reader():
            yield lambda: list(keys)
        soundtrack = unittest.mock.Mock()
        soundtrack.start.return_value = True
        soundtrack.seek.return_value = True
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack", return_value=soundtrack), \
             patch("ahoy_streamer_cli.player._terminal_keys", return_value=key_reader()), \
             patch("ahoy_streamer_cli.player.time.sleep"), \
             contextlib.redirect_stdout(io.StringIO()):
            player._play_ascii_video("https://media.test/seek.mp4", duration=20)
        self.assertEqual(capture.positions, [(0, 0.0), (0, 10000.0), (0, 0), (0, 19000.0)])
        self.assertEqual(soundtrack.seek.call_count, 4)

    def test_mpv_audio_track_starts_pauses_seeks_and_stops(self):
        class Process:
            def __init__(self): self.signals, self.terminated = [], False
            def poll(self): return None if not self.terminated else 0
            def send_signal(self, value): self.signals.append(value)
            def terminate(self): self.terminated = True
            def wait(self, timeout=None): return 0
        processes = [Process(), Process()]
        with patch("ahoy_streamer_cli.player.mpv_path", return_value="/usr/bin/mpv"), \
             patch("ahoy_streamer_cli.player.subprocess.Popen", side_effect=processes) as popen:
            track = player.MpvAudioTrack("https://media.test/clip.mp4")
            self.assertTrue(track.start())
            self.assertIn("--no-video", popen.call_args.args[0])
            self.assertTrue(track.toggle_pause())
            self.assertTrue(track.seek(12.5, paused=True))
            self.assertTrue(processes[0].terminated)
            self.assertEqual(processes[1].signals, [player.signal.SIGSTOP])
            track.stop()
            self.assertTrue(processes[1].terminated)
        self.assertIn("--start=12.500", popen.call_args.args[0])

    def test_mpv_audio_track_is_optional_when_mpv_is_missing(self):
        with patch("ahoy_streamer_cli.player.mpv_path", return_value=None):
            track = player.MpvAudioTrack("https://media.test/clip.mp4")
            self.assertFalse(track.start())
            self.assertIn("install mpv", track.status)

    def test_mpv_audio_stays_off_on_windows_without_sync_control(self):
        with patch("ahoy_streamer_cli.player.mpv_path", return_value="mpv"), \
             patch.object(player.os, "name", "nt"), \
             patch("ahoy_streamer_cli.player.subprocess.Popen") as popen:
            track = player.MpvAudioTrack("https://media.test/clip.mp4")
            self.assertFalse(track.start())
            self.assertIn("Windows", track.status)
        popen.assert_not_called()

    def test_ascii_video_defaults_to_full_range_grayscale_without_status_rows(self):
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        gray = [[0, 0, 128, 255, 255, 128], [0, 0, 128, 255, 255, 128]]
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
            resize=unittest.mock.Mock(side_effect=lambda img, size, interpolation: img),
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: gray),
        )
        soundtrack = unittest.mock.Mock()
        soundtrack.start.return_value = True
        output = io.StringIO()
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack", return_value=soundtrack), \
             patch("shutil.get_terminal_size", return_value=types.SimpleNamespace(columns=20, lines=10)), \
             patch("ahoy_streamer_cli.player.time.sleep"), contextlib.redirect_stdout(output):
            player._play_ascii_video("https://media.test/synthetic.mp4")
        rendered = output.getvalue()
        self.assertIn("▌", rendered)
        self.assertIn("\x1b[48;2;", rendered)
        fake_cv2.resize.assert_called_once_with(frame, (6, 2), interpolation=1)
        self.assertNotIn("\nPLAYING", rendered)
        self.assertIn("\n[", rendered)  # Keep the compact seek timeline.
        self.assertNotIn("install mpv", rendered)
        self.assertIn("AHOY VIDEO", rendered)  # Playback details live in the window title.
        self.assertIn("gray", rendered)
        self.assertIn("v focus", rendered)
        self.assertTrue(capture.released)

    def test_video_without_native_sound_still_plays_grayscale(self):
        video = {"type": "video", "media_url": "https://media.test/clip.mp4"}
        frame = types.SimpleNamespace(shape=(2, 3, 3))
        class Capture:
            released = False
            def isOpened(self): return True
            def get(self, prop): return 20
            def read(self):
                if hasattr(self, "read_once"): return False, None
                self.read_once = True
                return True, frame
            def release(self): self.released = True
        capture = Capture()
        fake_cv2 = types.SimpleNamespace(
            VideoCapture=lambda url: capture, CAP_PROP_FPS=0, INTER_AREA=1, COLOR_BGR2GRAY=2,
            resize=lambda img, size, interpolation: img,
            cvtColor=lambda img, code: types.SimpleNamespace(tolist=lambda: [[0] * 6 for _ in range(2)]))
        key_calls = iter(([], ["q"]))
        @contextmanager
        def key_reader():
            yield lambda: next(key_calls, [])
        output = io.StringIO()
        with patch.dict(sys.modules, {"cv2": fake_cv2}), \
             patch("ahoy_streamer_cli.player.MpvAudioTrack") as track_type, \
             patch("ahoy_streamer_cli.player._terminal_keys", return_value=key_reader()), \
             patch("ahoy_streamer_cli.player.time.sleep"), \
             patch("webbrowser.open") as browser, contextlib.redirect_stdout(output):
            track_type.return_value.start.return_value = False
            track_type.return_value.status = "silent · install mpv"
            result = player.play(video, "ascii")
        self.assertEqual(result, "ascii")
        self.assertTrue(capture.released)
        browser.assert_not_called()
        self.assertIn("\x1b[48;2;0;0;0m", output.getvalue())
        self.assertIn("\x1b[48;2;", output.getvalue())
        self.assertIn("silent", output.getvalue())

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
