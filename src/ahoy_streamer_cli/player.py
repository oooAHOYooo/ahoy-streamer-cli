"""Small portable audio adapter plus optional video launchers."""
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
import webbrowser
from urllib.parse import urlparse


def mpv_path():
    return shutil.which("mpv")


def audio_backend_ready():
    try:
        import miniaudio  # noqa: F401
        return True
    except ImportError:
        return False


def video_backend_ready():
    try:
        import cv2  # noqa: F401
        return True
    except Exception:
        return False


class URLSource:
    """Non-seekable bounded-network source for miniaudio's decoder."""
    def __init__(self, url):
        from miniaudio import StreamableSource
        # Keep the third-party callback contract in a tiny concrete subclass.
        class _Source(StreamableSource):
            def __init__(self, address):
                super().__init__()
                request = urllib.request.Request(address, headers={"User-Agent": "AHOY-Streamer/0.1"})
                class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
                    def redirect_request(self, req, fp, code, msg, headers, new_url):
                        if not new_url.startswith("https://"):
                            raise urllib.error.HTTPError(new_url, code, "HTTPS downgrade blocked", headers, fp)
                        return super().redirect_request(req, fp, code, msg, headers, new_url)
                self.response = urllib.request.build_opener(HTTPSRedirect).open(request, timeout=20)
            def read(self, num_bytes):
                return self.response.read(num_bytes)
            def close(self):
                self.response.close()
        self.source = _Source(url)


def _audio_format(url):
    suffix = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
    if suffix not in {"mp3", "wav", "flac", "ogg", "oga"}:
        raise RuntimeError("portable audio supports direct MP3, WAV, FLAC, or Vorbis URLs")
    import miniaudio
    formats = {"mp3": miniaudio.FileFormat.MP3, "wav": miniaudio.FileFormat.WAV,
               "flac": miniaudio.FileFormat.FLAC, "ogg": miniaudio.FileFormat.VORBIS,
               "oga": miniaudio.FileFormat.VORBIS}
    return formats[suffix]


class AudioSession:
    """miniaudio streams common audio formats to the platform's native device."""
    def __init__(self, item):
        url = item.get("media_url")
        if not url or not url.startswith("https://"):
            raise RuntimeError("this item has no safe HTTPS playback URL")
        file_format = _audio_format(url)
        import miniaudio
        self.source = URLSource(url).source
        self.generator = None
        self.device = None
        self.paused = False
        self.closed = False
        try:
            # stream_any primes its generator internally; don't advance it and discard audio.
            self.generator = miniaudio.stream_any(self.source, source_format=file_format)
            self.device = miniaudio.PlaybackDevice(app_name="AHOY Streamer")
            self.device.start(self.generator)
            self.current = item
        except Exception:
            if self.device:
                self.device.close()
            if self.generator:
                self.generator.close()
            self.source.close()
            raise

    def toggle_pause(self):
        if self.closed:
            return False
        if self.paused:
            self.device.start(self.generator)
        else:
            self.device.stop()
        self.paused = not self.paused
        return True

    def refresh_state(self):
        # miniaudio callbacks clear this reference at end-of-stream.
        if self.device.callback_generator is None and not self.paused:
            self.stop()

    def stop(self):
        if not self.closed:
            self.device.close()
            self.generator.close()
            self.source.close()
            self.closed = True


def play(item, mode="ascii", require_tty=False):
    url = item.get("media_url")
    if not url or not url.startswith("https://"):
        raise RuntimeError("this item has no safe HTTPS playback URL")
    if item["type"] in {"music", "podcast", "radio"}:
        if not audio_backend_ready():
            if not webbrowser.open(url):
                raise OSError("portable audio output is unavailable and the system browser could not open the media")
            return
        session = AudioSession(item)
        try:
            while session.device.callback_generator is not None:
                time.sleep(.1)
        except KeyboardInterrupt:
            pass
        finally:
            session.stop()
        return
    if mode == "ascii":
        if not video_backend_ready():
            if not webbrowser.open(url):
                raise OSError("ASCII decoder is unavailable and the system browser could not open the media")
            return "browser-fallback"
        if require_tty and not sys.stdout.isatty():
            raise OSError("ASCII video needs a terminal; use --video=window")
        try:
            _play_ascii_video(url)
            return "ascii"
        except AsciiBackendMissing:
            if not webbrowser.open(url):
                raise OSError("ASCII decoder is unavailable and the system browser could not open the media")
            return "browser-fallback"
    if mode != "window":
        raise ValueError("video mode must be ascii or window")
    # Prefer a local player when installed; browser is the zero-setup fallback.
    _open_video_window(url)


def _open_video_window(url):
    exe = mpv_path()
    if exe:
        result = subprocess.run([exe, "--no-config", "--", url], check=False)
        if result.returncode:
            raise RuntimeError(f"mpv exited with status {result.returncode}")
    elif not webbrowser.open(url):
        raise OSError("could not open the video URL in a browser")


class AsciiBackendMissing(OSError):
    pass


def _play_ascii_video(url):
    try:
        import cv2
    except Exception as exc:
        raise AsciiBackendMissing("OpenCV video decoder is unavailable") from exc
    capture = cv2.VideoCapture(url)
    if not capture.isOpened():
        capture.release()
        raise AsciiBackendMissing("OpenCV could not decode this video URL")
    fps = capture.get(cv2.CAP_PROP_FPS)
    delay = 1.0 / max(4.0, min(30.0, fps if fps and fps > 0 else 20.0))
    try:
        rendered = False
        while True:
            started = time.monotonic()
            ok, frame = capture.read()
            if not ok:
                break
            terminal = shutil.get_terminal_size((80, 24))
            max_width, max_height = max(1, terminal.columns - 1), max(1, terminal.lines - 2)
            source_height, source_width = frame.shape[:2]
            cols = min(max_width, source_width)
            rows = min(max_height, max(1, round(cols * source_height / max(1, source_width) * .5)))
            scaled = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
            print("\033[H" + luma_to_ascii(gray.tolist(), cols), end="\033[J", flush=True)
            rendered = True
            time.sleep(max(0, delay - (time.monotonic() - started)))
        if not rendered:
            raise AsciiBackendMissing("OpenCV decoded no video frames")
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
        print("\033[0m\n", flush=True)


class PlayerSession:
    """TUI-owned foreground audio with shared pause/stop state."""
    def __init__(self):
        self.audio = None
        self.process = None
        self.current = None

    def start(self, item, mode="window"):
        self.stop()
        url = item.get("media_url")
        if not url or not url.startswith("https://"):
            raise RuntimeError("this item has no safe HTTPS playback URL")
        if item.get("type") in {"music", "podcast", "radio"}:
            if not audio_backend_ready():
                play(item, mode)
                self.current = None
                return "external"
            self.audio = AudioSession(item)
            self.current = item
            return "background"
        if mode == "window":
            exe = mpv_path()
            if exe:
                self.process = subprocess.Popen([exe, "--no-config", "--", url],
                                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
                self.current = item
            elif not webbrowser.open(url):
                raise OSError("could not open the video URL in a browser")
            return "external"
        play(item, mode)
        return "external"

    def command(self, command):
        if command == ["cycle", "pause"]:
            return self.toggle_pause()
        return False

    def toggle_pause(self):
        return self.audio.toggle_pause() if self.audio else False

    def refresh_state(self):
        if self.process and self.process.poll() is not None:
            self.process = None
            self.current = None
        if self.audio:
            self.audio.refresh_state()
            if self.audio.closed:
                self.audio = None
                self.current = None

    def stop(self):
        if self.audio:
            self.audio.stop()
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        self.process = None
        self.audio = None
        self.current = None


def luma_to_ascii(rows, width=80, ramp=" .:-=+*#%@"):
    """Map rectangular 0..255 luma rows to printable monochrome ASCII."""
    if not rows or not ramp or width < 1:
        return ""
    source_width = max((len(row) for row in rows), default=0)
    if not source_width:
        return ""
    step = max(1, source_width // width)
    output = []
    for row in rows:
        chars = []
        for value in row[::step][:width]:
            index = round(max(0, min(255, value)) * (len(ramp) - 1) / 255)
            chars.append(ramp[index])
        output.append("".join(chars))
    return "\n".join(output)
