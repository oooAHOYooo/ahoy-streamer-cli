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
in the background, with pause/stop controls. On Windows/Linux, OpenCV decodes video frames
into monochrome ASCII in the terminal; video is silent in ASCII mode. Window video opens in mpv
when available or the system browser. This is a native terminal companion to the website, not a port of its account,
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

Audio uses the PyPI miniaudio runtime dependency and does not require Homebrew or system mpv.
`--video=ascii` decodes through pinned `opencv-python-headless` and resizes frames for the
terminal; it is experimental, monochrome, and silent. On macOS, standard install opens video
in the browser; on macOS 13+ you can opt into ASCII with `python -m pip install -e '.[ascii-video]'`.
That extra is unsupported on macOS 12 and older, including Big Sur. Use `--video=window` to
open mpv or the system browser. If the ASCII decoder is unavailable, ASCII mode opens the
browser and reports the fallback. OpenCV wheels bundle FFmpeg under LGPLv2.1 per the upstream
project; see the [OpenCV-Python third-party license notices](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt)
when using or redistributing its wheel. The dependency is installed as a separate PyPI wheel.
See [dependency and license notes](docs/DEPENDENCIES.md) for platform and redistribution details.
Use number keys 0–9 (Home through
Search), arrow keys or `j`/`k` to browse, Enter for details, `p` to play, Space to pause,
`x` to stop, `/` to search, `r` to refresh, and `q` to quit. Data sections need a network
connection. AHOY TV currently displays the public channel libraries; the API does not
provide authoritative slot timing, so the CLI does not claim synchronized live-TV parity.

See [the feature map and follow-up phases](docs/TASKS.md) for covered sections and gaps.

## Chosen implementation

Python 3.11+; package: `ahoy_streamer_cli`; installed command: `ahoy-streamer`.
Pinned OpenCV 4.12.0.88 provides cp37-abi3 wheels for Windows x64 and Linux x86_64/aarch64;
the OpenCV wheel is about 33–54 MB plus NumPy. macOS has no compatible OpenCV 4.12 wheel before
macOS 13, so ASCII decoding is optional there on macOS 13+ only. Miniaudio provides
wheels for macOS, Windows x64, and Linux x86_64; Linux aarch64 uses the browser for audio to
avoid a source build/compiler requirement. Windows installs `windows-curses` conditionally.
Python 3.11–3.14 is the intended range. Device output still depends on the host audio device
and driver. Windows Terminal/PowerShell are intended; legacy console color/resize can vary.
mpv is optional; the system browser is the window-video fallback. OpenCV's upstream wheel
states FFmpeg is LGPLv2.1; keep its bundled third-party notices available as required.

## Build efficiently

Complete one task per session. Preserve the command contract. Use small offline fixtures.
Record results in `STATUS.md` so the next agent can start without reading chat history.
See `docs/HANDOFF.md` for a ready-to-use implementation prompt.

## Publishing

GitHub: https://github.com/oooAHOYooo/ahoy-streamer-cli

The repository is private while planning. Public release, package name availability, and license are
release decisions, not completed work. See `docs/RELEASE.md`.
