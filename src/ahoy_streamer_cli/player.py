import shutil
import socket
import subprocess
import sys
import tempfile
import time
import json


def mpv_path():
    return shutil.which("mpv")


class PlayerSession:
    """Small foreground-owned mpv session for TUI audio/window playback."""
    def __init__(self):
        self.process = None
        self.socket_path = None
        self._directory = None
        self.current = None

    def start(self, item, mode="window"):
        exe = mpv_path()
        if not exe:
            raise FileNotFoundError("mpv is required; install mpv and try again")
        url = item.get("media_url")
        if not url or not url.startswith("https://"):
            raise RuntimeError("this item has no safe HTTPS playback URL")
        self.stop()
        self._directory = tempfile.TemporaryDirectory(prefix="ahoy-")
        self.socket_path = self._directory.name + "/mpv.sock"
        args = [exe, "--no-config", f"--input-ipc-server={self.socket_path}"]
        if item["type"] in {"music", "podcast", "radio"}:
            args.append("--no-video")
            if item.get("start_seconds"):
                args.append(f"--start={int(item['start_seconds'])}")
        elif mode == "ascii":
            probe = subprocess.run([exe, "--no-config", "--vo=help"], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)
            if "caca" not in probe.stdout.casefold():
                raise OSError("this mpv build has no caca output; use window playback")
            if not sys.stdout.isatty():
                raise OSError("ASCII video needs a terminal; use window playback")
            args.extend(["--vo=caca", "--really-quiet"])
        elif mode == "window":
            pass
        else:
            raise ValueError("video mode must be ascii or window")
        args.extend(["--", url])
        self.process = subprocess.Popen(args, stdin=subprocess.DEVNULL,
                                        stdout=None if item["type"] == "video" and mode == "ascii" else subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
        self.current = item
        if mode == "ascii" and item["type"] == "video":
            # caca owns the terminal while rendering; the TUI suspends around it.
            return "foreground"
        for _ in range(30):
            if self.process.poll() is not None:
                raise RuntimeError("mpv exited while opening playback")
            if self.socket_path and __import__("os").path.exists(self.socket_path):
                return "background"
            time.sleep(0.05)
        raise RuntimeError("mpv IPC did not become ready")

    def command(self, command):
        if not self.process or self.process.poll() is not None:
            self.current = None
            return False
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.25)
                client.connect(self.socket_path)
                client.sendall((json.dumps({"command": command}) + "\n").encode())
            return True
        except OSError:
            return False

    def toggle_pause(self):
        return self.command(["cycle", "pause"])

    def refresh_state(self):
        if self.process and self.process.poll() is not None:
            self.process = self.socket_path = self.current = None
            if self._directory:
                self._directory.cleanup()
                self._directory = None

    def stop(self):
        self.command(["quit"])
        if self.process:
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=1)
        self.process = self.socket_path = self.current = None
        if self._directory:
            self._directory.cleanup()
            self._directory = None


def play(item, mode="ascii", require_tty=False):
    exe = mpv_path()
    if not exe:
        raise FileNotFoundError("mpv is required; install mpv and try again")
    url = item.get("media_url")
    if not url or not url.startswith("https://"):
        raise RuntimeError("this item has no safe HTTPS playback URL")
    args = [exe, "--no-config"]
    if item["type"] in {"music", "podcast", "radio"}:
        args.append("--no-video")
    elif mode == "ascii":
        if require_tty and not sys.stdout.isatty():
            raise OSError("ASCII video needs a terminal; select --video=window")
        probe = subprocess.run([exe, "--no-config", "--vo=help"], stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=False)
        if probe.returncode or "caca" not in probe.stdout.casefold():
            raise OSError("this mpv build has no caca video output; retry with --video=window")
        args.extend(["--vo=caca", "--really-quiet"])
    elif mode != "window":
        raise ValueError("video mode must be ascii or window")
    args.extend(["--", url])
    # caca renders its terminal frames through stdout; other modes keep stdout clean.
    result = subprocess.run(args, stdin=None, stdout=None if item["type"] == "video" and mode == "ascii" else subprocess.DEVNULL, check=False)
    if result.returncode:
        raise RuntimeError(f"mpv exited with status {result.returncode}; try --video=window")
