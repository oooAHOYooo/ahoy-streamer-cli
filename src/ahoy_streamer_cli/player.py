"""Small portable audio adapter plus optional video launchers."""
import shutil
import os
import re
import select
import signal
import subprocess
import sys
import time
import unicodedata
from contextlib import contextmanager
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


class UnsupportedAudioFormat(RuntimeError):
    """The URL advertises a format the terminal decoder cannot play."""


def _audio_format(url, content_type=None):
    suffix = urlparse(url).path.rsplit(".", 1)[-1].lower() if "." in urlparse(url).path else ""
    import miniaudio
    formats = {"mp3": miniaudio.FileFormat.MP3, "wav": miniaudio.FileFormat.WAV,
               "flac": miniaudio.FileFormat.FLAC, "ogg": miniaudio.FileFormat.VORBIS,
               "oga": miniaudio.FileFormat.VORBIS}
    mime_formats = {"audio/mpeg": miniaudio.FileFormat.MP3,
                    "audio/wav": miniaudio.FileFormat.WAV,
                    "audio/x-wav": miniaudio.FileFormat.WAV,
                    "audio/flac": miniaudio.FileFormat.FLAC,
                    "audio/ogg": miniaudio.FileFormat.VORBIS,
                    "application/ogg": miniaudio.FileFormat.VORBIS}
    if suffix in formats:
        return formats[suffix]
    if content_type and content_type.split(";", 1)[0].strip().lower() in mime_formats:
        return mime_formats[content_type.split(";", 1)[0].strip().lower()]
    if suffix in {"aac", "m4a", "mp4", "m3u8", "mpd"}:
        raise UnsupportedAudioFormat("this stream uses a format handled by the system browser")
    # Signed storage URLs often have no extension. Let miniaudio sniff their headers.
    return miniaudio.FileFormat.UNKNOWN


class AudioSession:
    """miniaudio streams common audio formats to the platform's native device."""
    def __init__(self, item):
        url = item.get("media_url")
        if not url or not url.startswith("https://"):
            raise RuntimeError("this item has no safe HTTPS playback URL")
        import miniaudio
        self.source = URLSource(url).source
        self.generator = None
        self.device = None
        self.paused = False
        self.closed = False
        try:
            content_type = getattr(getattr(self.source, "response", None), "headers", {}).get("Content-Type")
            file_format = _audio_format(url, content_type)
            # stream_any starts its decoder generator before returning it. Unknown
            # content types can still fail format sniffing; route those streams to
            # the browser just like explicitly unsupported containers.
            try:
                self.generator = miniaudio.stream_any(self.source, source_format=file_format)
            except Exception as exc:
                raise UnsupportedAudioFormat("miniaudio could not decode this stream") from exc
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


def play(item, mode="ascii", require_tty=False, browse_items=None, browse_index=0):
    url = item.get("media_url")
    if not url or not url.startswith("https://"):
        raise RuntimeError("this item has no safe HTTPS playback URL")
    if item["type"] in {"music", "podcast", "radio"}:
        if not audio_backend_ready():
            if not webbrowser.open(url):
                raise OSError("portable audio output is unavailable and the system browser could not open the media")
            return "browser-fallback"
        try:
            session = AudioSession(item)
        except UnsupportedAudioFormat:
            if not webbrowser.open(url):
                raise OSError("this audio format is unsupported and the system browser could not open the media")
            return "browser-fallback"
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
            choice = _play_ascii_video(url, duration=item.get("duration_seconds"),
                                       audio_url=item.get("audio_url"),
                                       browse_items=browse_items, browse_index=browse_index)
            return ("ascii", choice) if browse_items is not None else "ascii"
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


def _play_ascii_video(url, duration=None, audio_url=None, browse_items=None, browse_index=0):
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
    frame_count = capture.get(getattr(cv2, "CAP_PROP_FRAME_COUNT", 7))
    if not duration and fps and fps > 0 and frame_count and frame_count > 0:
        duration = frame_count / fps
    try:
        duration = float(duration) if duration and float(duration) > 0 else None
    except (TypeError, ValueError):
        duration = None
    try:
        rendered = False
        paused = False
        elapsed = 0.0
        render_mode = "gray"
        soft_focus = False
        soundtrack = MpvAudioTrack(audio_url or url)
        has_audio = soundtrack.start()
        notice = "" if has_audio else soundtrack.status
        last_frame = None
        browse_index = min(max(0, browse_index), len(browse_items) - 1) if browse_items else 0
        playing_index = browse_index
        browse_visible = browse_items is not None
        badge_until = 0.0
        last_terminal = None
        last_badge_active = False
        layout_dirty = False
        sys.stdout.write("\033[2J\033[H\033[?25l")
        sys.stdout.flush()
        with _terminal_keys() as read_keys:
            while True:
                seek_requested = False
                keys = read_keys()
                for key in keys:
                    if key == " ":
                        paused = not paused
                        if has_audio and not soundtrack.toggle_pause():
                            paused = not paused
                    elif key == "q":
                        return ("back", browse_index) if browse_items is not None else None
                    elif key in {"up", "k"} and browse_items:
                        browse_index = max(0, browse_index - 1)
                    elif key in {"down", "j"} and browse_items:
                        browse_index = min(len(browse_items) - 1, browse_index + 1)
                    elif key in {"\r", "\n"} and browse_items and browse_index != playing_index:
                        return ("select", browse_index)
                    elif key in {"f", "\t"} and browse_items is not None:
                        browse_visible = not browse_visible
                        badge_until = time.monotonic() + 1.5
                        layout_dirty = True
                    elif key in {"left", "h", "["}:
                        elapsed = max(0.0, elapsed - 10.0)
                        sought = capture.set(getattr(cv2, "CAP_PROP_POS_MSEC", 0), elapsed * 1000)
                        notice = "seek unavailable" if not sought else ""
                        if sought and has_audio:
                            soundtrack.seek(elapsed, paused)
                        seek_requested = True
                    elif key in {"right", "l", "]"}:
                        elapsed += 10.0
                        if duration:
                            elapsed = min(elapsed, max(0.0, duration - .25))
                        sought = capture.set(getattr(cv2, "CAP_PROP_POS_MSEC", 0), elapsed * 1000)
                        notice = "seek unavailable" if not sought else ""
                        if sought and has_audio:
                            soundtrack.seek(elapsed, paused)
                        seek_requested = True
                    elif key == "home":
                        elapsed = 0.0
                        sought = capture.set(getattr(cv2, "CAP_PROP_POS_MSEC", 0), 0)
                        notice = "seek unavailable" if not sought else ""
                        if sought and has_audio:
                            soundtrack.seek(elapsed, paused)
                        seek_requested = True
                    elif key == "end" and duration:
                        elapsed = max(0.0, duration - 1.0)
                        sought = capture.set(getattr(cv2, "CAP_PROP_POS_MSEC", 0), elapsed * 1000)
                        notice = "seek unavailable" if not sought else ""
                        if sought and has_audio:
                            soundtrack.seek(elapsed, paused)
                        seek_requested = True
                    elif key == "r":
                        render_mode = {"gray": "hybrid", "hybrid": "ascii", "ascii": "braille",
                                       "braille": "gray"}[render_mode]
                        notice = {"gray": "higher-resolution grayscale quadrants", "hybrid": "grayscale blocks + Braille detail",
                                  "ascii": "high-contrast shaded ASCII", "braille": "Braille high detail"}[render_mode]
                    elif key == "v":
                        soft_focus = not soft_focus
                        notice = "soft focus on" if soft_focus else "soft focus off"
                terminal = shutil.get_terminal_size((80, 24))
                terminal_size = (terminal.columns, terminal.lines)
                badge_active = time.monotonic() < badge_until
                if paused and last_frame is not None and not keys and not seek_requested \
                        and terminal_size == last_terminal and badge_active == last_badge_active:
                    time.sleep(0.05)
                    continue
                if paused and last_frame is not None and not seek_requested:
                    frame = last_frame
                else:
                    started = time.monotonic()
                    ok, frame = capture.read()
                    if not ok:
                        break
                    last_frame = frame
                if paused and last_frame is None:
                    time.sleep(0.05)
                    continue
                position_ms = capture.get(getattr(cv2, "CAP_PROP_POS_MSEC", 0))
                if position_ms and position_ms > 0:
                    elapsed = position_ms / 1000.0
                elif not paused and not seek_requested:
                    elapsed += delay
                max_width, max_height = max(1, terminal.columns - 1), max(1, terminal.lines - 1)
                side_width = min(30, max(24, terminal.columns // 3)) if browse_visible and terminal.columns >= 72 else 0
                video_width = max_width - side_width - (2 if side_width else 0)
                browse_rows = min(5, max(2, terminal.lines // 4)) if browse_visible and not side_width else 0
                video_height = max(1, max_height - browse_rows - (1 if browse_visible else 0))
                source_height, source_width = frame.shape[:2]
                cols = min(video_width, source_width)
                rows = min(video_height, max(1, round(cols * source_height / max(1, source_width) * .5)))
                if render_mode == "gray":
                    # Four independently sampled luminance points per character cell
                    # double the spatial detail of a conventional half-block renderer.
                    scaled = cv2.resize(frame, (cols * 2, rows * 2), interpolation=cv2.INTER_AREA)
                    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                    luma = _enhance_luma(gray.tolist())
                    if soft_focus:
                        luma = _soften_luma(luma)
                    picture = luma_to_gray_quadrants(luma, cols, rows)
                elif render_mode in {"braille", "hybrid"}:
                    scaled = cv2.resize(frame, (cols * 2, rows * 4), interpolation=cv2.INTER_AREA)
                    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                    luma = _enhance_luma(gray.tolist())
                    if soft_focus:
                        luma = _soften_luma(luma)
                    picture = (luma_to_hybrid(luma, cols, rows) if render_mode == "hybrid"
                               else luma_to_braille(luma, cols, rows))
                else:
                    scaled = cv2.resize(frame, (cols, rows), interpolation=cv2.INTER_AREA)
                    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
                    enhanced = _enhance_luma(gray.tolist())
                    if soft_focus:
                        enhanced = _soften_luma(enhanced)
                    picture = luma_to_ascii(enhanced, cols, ramp=" .:-=+*#%@")
                state = "PAUSED" if paused else "PLAYING"
                total = _time_label(duration) if duration else "--:--"
                title = (f"AHOY VIDEO · {state} · {_time_label(elapsed)}/{total} · {render_mode} · "
                         f"Space pause · ←/→ seek 10s · Home/End · r style · v focus · " +
                         ("f/Tab full screen · ↑/↓ browse · Enter play · " if browse_visible else
                          "f/Tab show videos · " if browse_items is not None else "") + "q back" +
                         (f" · {notice}" if notice else ""))
                timeline = _video_timeline(elapsed, duration, video_width)
                if browse_visible:
                    picture = _video_browser_view(picture, timeline, browse_items, browse_index,
                                                  side_width, video_width, browse_rows, max_height)
                else:
                    picture += "\n" + timeline
                badge = ""
                if badge_active:
                    label = " BROWSE · ↑↓ choose · Enter play · f full " if browse_visible else \
                            " FULL SCREEN · f show videos "
                    badge = "\033[1;1H\033[7m" + label[:max_width] + "\033[0m"
                # Clear on layout changes; a stable video view overwrites its own cells.
                # Erasing the whole remainder of the screen on every frame makes many
                # terminals repaint much more than the moving picture needs.
                clear = "\033[2J" if (layout_dirty or terminal_size != last_terminal or
                                      badge_active != last_badge_active) else ""
                erase_rest = "\033[J" if browse_items is None else ""
                sys.stdout.write("\033]0;" + title + "\007" + clear + "\033[H" +
                                 picture + erase_rest + badge)
                sys.stdout.flush()
                rendered = True
                layout_dirty = False
                last_terminal = terminal_size
                last_badge_active = badge_active
                if not paused:
                    time.sleep(max(0, delay - (time.monotonic() - started)))
        if not rendered:
            raise AsciiBackendMissing("OpenCV decoded no video frames")
        return ("back", browse_index) if browse_items is not None else None
    except KeyboardInterrupt:
        return ("back", browse_index) if browse_items is not None else None
    finally:
        capture.release()
        if "soundtrack" in locals():
            soundtrack.stop()
        sys.stdout.write("\033[0m\033[?25h\033]0;AHOY STREAMER\007\033[2J\033[H")
        sys.stdout.flush()


@contextmanager
def _terminal_keys():
    """Read playback controls without mistaking arrow escape sequences for Escape."""
    if not sys.stdin.isatty():
        yield lambda: []
        return
    if os.name == "nt":
        import msvcrt
        def read_keys():
            keys = []
            while msvcrt.kbhit():
                value = msvcrt.getwch()
                if value in {"\x00", "\xe0"}:
                    decoded = _decode_key_sequence(value + msvcrt.getwch())
                    if decoded:
                        keys.append(decoded)
                else:
                    keys.append(value)
            return keys
        yield read_keys
        return
    import termios
    import tty
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        def read_keys():
            keys = []
            while select.select([fd], [], [], 0)[0]:
                value = os.read(fd, 1).decode("latin-1")
                if value == "\x1b":
                    sequence = value
                    if select.select([fd], [], [], 0.12)[0]:
                        sequence += os.read(fd, 1).decode("latin-1")
                        if sequence[-1] in "[O":
                            while select.select([fd], [], [], 0.03)[0]:
                                sequence += os.read(fd, 1).decode("latin-1")
                                if len(sequence) >= 3 and "@" <= sequence[-1] <= "~":
                                    break
                    decoded = _decode_key_sequence(sequence)
                    if decoded:
                        keys.append(decoded)
                else:
                    keys.append(value)
            return keys
        yield read_keys
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


class PlayerSession:
    """TUI-owned foreground audio with shared pause/stop state."""
    def __init__(self):
        self.audio = None
        self.process = None
        self.current = None
        self.external = False
        self.video_paused = False

    def start(self, item, mode="window"):
        self.stop()
        url = item.get("media_url")
        if not url or not url.startswith("https://"):
            raise RuntimeError("this item has no safe HTTPS playback URL")
        if item.get("type") in {"music", "podcast", "radio"}:
            if not audio_backend_ready():
                play(item, mode)
                self.current = item
                self.external = True
                return "external"
            try:
                self.audio = AudioSession(item)
            except UnsupportedAudioFormat:
                if not webbrowser.open(url):
                    raise OSError("this audio format is unsupported and the system browser could not open the media")
                self.current = item
                self.external = True
                return "external"
            self.current = item
            return "background"
        if mode == "window":
            exe = mpv_path()
            if exe:
                self.process = subprocess.Popen([exe, "--no-config", "--", url],
                                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
                self.current = item
                self.external = False
            elif webbrowser.open(url):
                self.current = item
                self.external = True
            else:
                raise OSError("could not open the video URL in a browser")
            return "external"
        play(item, mode)
        return "external"

    def command(self, command):
        if command == ["cycle", "pause"]:
            return self.toggle_pause()
        return False

    def toggle_pause(self):
        if self.audio:
            return self.audio.toggle_pause()
        if self.process and os.name != "nt":
            self.process.send_signal(signal.SIGCONT if self.video_paused else signal.SIGSTOP)
            self.video_paused = not self.video_paused
            return True
        return False

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
        self.external = False
        self.video_paused = False


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


def _enhance_luma(rows, contrast=1.3):
    """Stretch midtones for legibility while retaining black and white endpoints."""
    return [[max(0, min(255, round((value - 128) * contrast + 128))) for value in row]
            for row in rows]


def _soften_luma(rows, amount=0.28):
    """Blend a subtle 3x3 low-pass image with the source to soften cell edges."""
    if not rows or not any(rows):
        return rows
    height = len(rows)
    width = max(len(row) for row in rows)
    kernel = ((1, 2, 1), (2, 4, 2), (1, 2, 1))
    softened = []
    for y, row in enumerate(rows):
        output = []
        for x, original in enumerate(row):
            total = weight_total = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    sy, sx = min(height - 1, max(0, y + dy)), min(width - 1, max(0, x + dx))
                    if sx < len(rows[sy]):
                        weight = kernel[dy + 1][dx + 1]
                        total += rows[sy][sx] * weight
                        weight_total += weight
            blurred = total / weight_total if weight_total else original
            output.append(round(original * (1 - amount) + blurred * amount))
        softened.append(output)
    return softened


def _decode_key_sequence(sequence):
    """Normalize common POSIX CSI/SS3 and Windows console arrow sequences."""
    if sequence.startswith("\x1b[") or sequence.startswith("\x1bO"):
        final = sequence[-1:]
        if final in {"A", "B", "D", "C", "H", "F"}:
            return {"A": "up", "B": "down", "D": "left", "C": "right",
                    "H": "home", "F": "end"}[final]
        if sequence.startswith("\x1b[") and final == "~":
            code = sequence[2:-1].split(";", 1)[0]
            return {"1": "home", "7": "home", "4": "end", "8": "end"}.get(code)
        return None
    if sequence.startswith(("\x00", "\xe0")) and len(sequence) > 1:
        return {"H": "up", "P": "down", "K": "left", "M": "right",
                "G": "home", "O": "end"}.get(sequence[-1])
    return None


def luma_to_gray_blocks(rows):
    """Render two full-range grayscale pixels per terminal cell using upper-half blocks."""
    output = []
    foreground = background = None
    for index in range(0, len(rows), 2):
        top_row = rows[index]
        bottom_row = rows[index + 1] if index + 1 < len(rows) else top_row
        chars = []
        for top, bottom in zip(top_row, bottom_row):
            top_gray = max(0, min(255, int(top)))
            bottom_gray = max(0, min(255, int(bottom)))
            if top_gray != foreground:
                chars.append(f"\x1b[38;2;{top_gray};{top_gray};{top_gray}m")
                foreground = top_gray
            if bottom_gray != background:
                chars.append(f"\x1b[48;2;{bottom_gray};{bottom_gray};{bottom_gray}m")
                background = bottom_gray
            chars.append("▀")
        chars.append("\x1b[0m")
        foreground = background = None
        output.append("".join(chars))
    return "\n".join(output)


def luma_to_gray_quadrants(rows, columns, lines):
    """Render four grayscale samples per terminal cell with two-tone 2x2 mosaics."""
    glyphs = (" ", "▘", "▝", "▀", "▖", "▌", "▞", "▛",
              "▗", "▚", "▐", "▜", "▄", "▙", "▟", "█")
    output = []
    for y in range(lines):
        chars = []
        foreground = background = None
        for x in range(columns):
            samples = [max(0, min(255, int(rows[2 * y + dy][2 * x + dx])))
                       for dy in range(2) for dx in range(2)]
            ordered = sorted(samples)
            threshold = (ordered[1] + ordered[2]) / 2
            low = round(sum(value for value in samples if value <= threshold) /
                        max(1, sum(value <= threshold for value in samples)))
            high = round(sum(value for value in samples if value > threshold) /
                         max(1, sum(value > threshold for value in samples)))
            mask = sum(1 << index for index, value in enumerate(samples) if value > threshold)
            if high != foreground:
                chars.append(f"\x1b[38;2;{high};{high};{high}m")
                foreground = high
            if low != background:
                chars.append(f"\x1b[48;2;{low};{low};{low}m")
                background = low
            chars.append(glyphs[mask])
        chars.append("\x1b[0m")
        output.append("".join(chars))
    return "\n".join(output)


def luma_to_braille(rows, columns, lines):
    """Map 2x4 luminance samples to each Unicode Braille cell."""
    bits = ((0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 6),
            (0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 1, 7))
    thresholds = ((16, 144), (208, 80), (48, 176), (240, 112))
    output = []
    for y in range(lines):
        row = []
        for x in range(columns):
            value = 0x2800
            for py, px, bit in bits:
                sample_y, sample_x = y * 4 + py, x * 2 + px
                sample = rows[sample_y][sample_x] if sample_y < len(rows) and sample_x < len(rows[sample_y]) else 0
                if sample >= thresholds[py][px]:
                    value |= 1 << bit
            row.append(chr(value))
        output.append("".join(row))
    return "\n".join(output)


def luma_to_hybrid(rows, columns, lines, detail_threshold=16):
    """Use 24-bit grayscale cell fills and Braille dots for fine local detail."""
    bits = ((0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 6),
            (0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 1, 7))
    output = []
    for y in range(lines):
        chars = []
        for x in range(columns):
            samples = [rows[y * 4 + py][x * 2 + px]
                       if y * 4 + py < len(rows) and x * 2 + px < len(rows[y * 4 + py]) else 0
                       for py, px, _ in bits]
            average = round(sum(samples) / len(samples))
            shade = max(0, min(255, average))
            pattern = 0
            for sample, (_, _, bit) in zip(samples, bits):
                if abs(sample - average) >= detail_threshold:
                    pattern |= 1 << bit
            chars.append(f"\x1b[48;2;{shade};{shade};{shade}m")
            if pattern:
                foreground = 8 if shade >= 128 else 248
                chars.append(f"\x1b[38;2;{foreground};{foreground};{foreground}m")
            chars.append(chr(0x2800 | pattern))
        chars.append("\x1b[0m")
        output.append("".join(chars))
    return "\n".join(output)


def _time_label(seconds):
    if seconds is None:
        return "--:--"
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _video_browser_view(picture, timeline, items, selected, side_width, video_width,
                        browse_rows, height):
    """Keep the catalog visible while frames update, without trusting catalog text as ANSI."""
    frame_lines = picture.split("\n")
    if side_width:
        count = max(1, height - 1)
        start = min(max(0, selected - count // 2), max(0, len(items) - count))
        labels = [_safe_video_label(f"VIDEOS ↑↓ Enter  {selected + 1}/{len(items)}", side_width)]
        for index in range(start, min(len(items), start + count)):
            marker = "▶ " if index == selected else "  "
            title = _safe_video_label(items[index].get("title", ""), side_width - 2)
            labels.append(marker + title)
        lines = frame_lines + [timeline]
        return "\n".join((lines[row] if row < len(lines) else "")
                         + f"\033[{video_width + 3}G" + (labels[row] if row < len(labels) else "") + "\033[K"
                         for row in range(min(height, max(len(lines), len(labels)))))
    count = max(1, browse_rows - 1)
    start = min(max(0, selected - count // 2), max(0, len(items) - count))
    labels = [_safe_video_label(f"VIDEOS ↑↓ Enter  {selected + 1}/{len(items)}", video_width)]
    for index in range(start, min(len(items), start + count)):
        marker = "▶ " if index == selected else "  "
        labels.append(marker + _safe_video_label(items[index].get("title", ""), video_width - 2))
    return "\n".join(frame_lines + [timeline] + [label + "\033[K" for label in labels])


def _safe_video_label(value, width):
    without_csi = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", str(value))
    clean = "".join(ch for ch in without_csi if unicodedata.category(ch)[0] != "C")
    return clean[:max(0, width)]


def _video_timeline(position, duration, width):
    width = max(8, width)
    if not duration or duration <= 0:
        return "[" + "─" * (width - 2) + "]"
    inner = width - 2
    progress = min(1.0, max(0.0, position / duration))
    marker = min(inner - 1, int(progress * (inner - 1)))
    bar = "".join("●" if i == marker else "━" if i < marker else "─" for i in range(inner))
    return "[" + bar + "]"


class MpvAudioTrack:
    """Optional audio-only MPV process for soundtracks in video containers."""
    def __init__(self, url):
        self.url = url
        self.executable = mpv_path()
        self.process = None
        self.paused = False
        self.status = ""

    def start(self, position=0.0, paused=False):
        if not self.executable:
            self.status = "silent · install mpv for video audio"
            return False
        if os.name == "nt":
            self.status = "silent · synchronized video audio controls are unavailable on Windows"
            return False
        if not self.url or not self.url.startswith("https://"):
            self.status = "silent · no safe audio URL for this video"
            return False
        self.stop()
        try:
            self.process = subprocess.Popen(
                [self.executable, "--no-config", "--really-quiet", "--no-video",
                 "--force-window=no", f"--start={max(0.0, position):.3f}", "--", self.url],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            self.process = None
            self.status = "silent · mpv could not open the video soundtrack"
            return False
        self.paused = False
        self.status = "mpv audio"
        if paused:
            return self.toggle_pause()
        return True

    def toggle_pause(self):
        if not self.process or self.process.poll() is not None or os.name == "nt":
            return False
        try:
            self.process.send_signal(signal.SIGCONT if self.paused else signal.SIGSTOP)
        except OSError:
            return False
        self.paused = not self.paused
        return True

    def seek(self, position, paused=False):
        return self.start(position, paused)

    def stop(self):
        if not self.process:
            return
        if self.process.poll() is None:
            if self.paused and os.name != "nt":
                try:
                    self.process.send_signal(signal.SIGCONT)
                except OSError:
                    pass
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=1)
        self.process = None
        self.paused = False
