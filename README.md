# AHOY Streamer Terminal

A keyboard-first terminal listening room for discovering and playing independent media from AHOY Streamer, with a small JSON command interface for agents.

**Status: app-like terminal browsing draft. Not published as a package; real device playback has not been manually verified.**

## Start here

Read `AGENTS.md`, `STATUS.md`, then the single assigned task in `docs/TASKS.md`.
The implementation contract is `docs/SPEC.md`; upstream evidence is in `docs/UPSTREAM.md`.

## First release

The terminal app exposes Home, Music, Videos, Podcasts, Artists, Events, Studio, Radio,
AHOY TV channel libraries, and Search in one keyboard-driven interface. It browses public
catalogs and opens item details; miniaudio plays direct MP3, WAV, FLAC, and Vorbis audio
in the background, with pause/stop controls. On Windows/Linux and macOS 13+, OpenCV decodes
video frames in grayscale by default: each terminal cell renders a 2×2 mosaic from four spatial
samples, using two 24-bit gray shades to preserve fine detail. Press `r` to cycle through the Braille hybrid,
shaded ASCII, and pure Braille. A compact seek bar sits under
the image; playback time, state, and controls appear in the window title. Space pauses, Left/Right seek by 10 seconds,
Home/End jump to the beginning or near the end, `v` toggles a subtle soft-focus blend, and q returns.
On macOS and Linux, mpv plays the video soundtrack during the terminal view and follows pause/seek/quit
controls. Without mpv, or on Windows, grayscale video still plays silently. Seeking and duration depend
on the video stream. Window video opens in mpv when available or the system browser. This is a native
terminal companion to the website, not a port of its account,
payment, administration, or synchronized-device features.

A small command interface remains alongside the TUI so agents can search, inspect,
and request playback without navigating screens. JSON is a stable public contract.

Usage:

```sh
git clone --branch codex/streamer-tui-first-draft --single-branch https://github.com/oooAHOYooo/ahoy-streamer-cli.git
cd ahoy-streamer-cli
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ahoy-streamer                         # open the terminal listening room
ahoy-streamer search poets --json
ahoy-streamer show music:song_1 --json
ahoy-streamer play music:song_1
ahoy-streamer watch video:example --video=ascii
ahoy-streamer doctor --json
```

Standalone audio uses the PyPI miniaudio runtime dependency and does not require Homebrew or
system mpv. Audio embedded in a video uses system mpv (`brew install mpv` on macOS) to
play alongside terminal video. Without mpv, terminal video still plays without audio. The Python
package does not install operating-system packages automatically: mpv is distributed separately
for each OS/package manager, and install-time system changes require platform-specific installers.
See the [official mpv installation guide](https://mpv.io/installation/) for Windows, macOS, and Linux.
Direct MP3/WAV/FLAC/Vorbis URLs play inside the TUI; signed URLs without extensions are decoded
using their response content type or format sniffing. Unsupported formats such as AAC/M4A open
in the system browser.
`--video=ascii` decodes through pinned `opencv-python-headless` and resizes frames for the
terminal; it is experimental. The default renderer maps four grayscale samples into 2×2 quadrant-block
patterns per character cell and assigns two 24-bit gray shades to foreground and background. This gives
twice the spatial samples of the previous half-block renderer. `r` cycles through a grayscale/Braille hybrid,
high-contrast shaded ASCII, and Braille only. A compact timeline
remains under the image; playback status and controls are shown in the terminal window title. `v`
toggles a subtle blur blend to soften hard pixel-cell edges (at a small cost to fine detail).
macOS 13+ gets video decoding by default; macOS 12 and older use browser video to keep installation
working. Use `--video=window` to
open mpv or the system browser. If the ASCII decoder cannot open a stream, the TUI opens the
browser and reports the fallback. OpenCV wheels bundle FFmpeg under LGPLv2.1 per the upstream
project; see the [OpenCV-Python third-party license notices](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt)
when using or redistributing its wheel. The dependency is installed as a separate PyPI wheel.
See [dependency and license notes](docs/DEPENDENCIES.md) for platform and redistribution details.
Use number keys 0–9 (Home through
Search), arrow keys or `j`/`k` to browse, Enter for details, `p` to play, and Space to play the
selected item, pause/resume it while it remains selected, or switch to a different selection and
stop TUI-owned playback. Use `x` to stop, `/` to search, `r` to refresh, and `q` to quit. Data sections need a network
connection. AHOY TV currently displays the public channel libraries; the API does not
provide authoritative slot timing, so the CLI does not claim synchronized live-TV parity.

See [the feature map and follow-up phases](docs/TASKS.md) for covered sections and gaps.

## Chosen implementation

Python 3.11+; package: `ahoy_streamer_cli`; installed command: `ahoy-streamer`.
Pinned OpenCV 4.12.0.88 provides cp37-abi3 wheels for Windows x64, Linux x86_64/aarch64, and
macOS 13+; the OpenCV wheel is about 33–57 MB plus NumPy. Earlier macOS versions use browser
video because compatible wheels are unavailable. Miniaudio provides
wheels for macOS, Windows x64, and Linux x86_64; Linux aarch64 uses the browser for audio to
avoid a source build/compiler requirement. Windows installs `windows-curses` conditionally.
Python 3.11–3.14 is the intended range. Device output still depends on the host audio device
and driver. Windows Terminal/PowerShell are intended; legacy console color/resize can vary.
mpv is a separate system dependency for video soundtrack audio; the system browser is the
window-video fallback. OpenCV's upstream wheel
states FFmpeg is LGPLv2.1; keep its bundled third-party notices available as required.

## Build efficiently

Complete one task per session. Preserve the command contract. Use small offline fixtures.
Record results in `STATUS.md` so the next agent can start without reading chat history.
See `docs/HANDOFF.md` for a ready-to-use implementation prompt.

## Publishing

GitHub: https://github.com/oooAHOYooo/ahoy-streamer-cli

The repository is private while planning. Public release, package name availability, and license are
release decisions, not completed work. See `docs/RELEASE.md`.
