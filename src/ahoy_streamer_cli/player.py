import shutil
import subprocess
import sys


def mpv_path():
    return shutil.which("mpv")


def play(item, mode="ascii", require_tty=False):
    exe = mpv_path()
    if not exe:
        raise FileNotFoundError("mpv is required; install mpv and try again")
    url = item.get("media_url")
    if not url or not url.startswith("https://"):
        raise RuntimeError("this item has no safe HTTPS playback URL")
    args = [exe, "--no-config"]
    if item["type"] == "music":
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
