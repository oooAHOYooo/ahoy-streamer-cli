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

## Quick install

For the fewest prerequisites, download the [standalone preview release](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/tag/v0.1.0-standalone-preview.2):

| System | Download |
| --- | --- |
| macOS Apple Silicon | [ZIP](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/download/v0.1.0-standalone-preview.2/ahoy-streamer-macos-apple-silicon-preview.zip) |
| macOS Intel | [ZIP](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/download/v0.1.0-standalone-preview.2/ahoy-streamer-macos-intel-preview.zip) |
| Linux x64 | [ZIP](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/download/v0.1.0-standalone-preview.2/ahoy-streamer-linux-x64-preview.zip) |
| Windows x64 | [ZIP](https://github.com/oooAHOYooo/ahoy-streamer-cli/releases/download/v0.1.0-standalone-preview.2/ahoy-streamer-windows-x64-preview.zip) |

Extract the ZIP and read `START_HERE.txt`. Run `./ahoy-streamer` from a terminal on
macOS/Linux, or `./ahoy-streamer.exe` in Windows PowerShell. Python and the app's Python
packages are included. The builds passed offline tests and startup/backend checks on
their build machines; real playback has not been verified on every system. macOS builds
are unsigned and may require approval in Privacy & Security to open. Linux was built
on Ubuntu 22.04; older distributions are unverified. Video soundtracks on macOS/Linux
still use separately installed `mpv`; Windows terminal video is silent.

The source-install options below remain available if you prefer to update from `main`.

### Windows 10/11 (PowerShell)

Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/windows/)
if `py -3 --version` does not work. Then paste this into PowerShell:

```powershell
$app = Join-Path $env:LOCALAPPDATA 'AHOY Streamer'
py -3 -m venv $app
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ with venv is required.' }
& (Join-Path $app 'Scripts\python.exe') -m pip install --disable-pip-version-check --upgrade 'https://github.com/oooAHOYooo/ahoy-streamer-cli/archive/refs/heads/main.zip'
if ($LASTEXITCODE -ne 0) { throw 'Install failed; check the error above.' }
& (Join-Path $app 'Scripts\ahoy-streamer.exe')
```

This installs into your user profile without Git, administrator access, `PATH` edits, or
PowerShell activation. Paste the same block again to update. Later, start it with
`& (Join-Path $env:LOCALAPPDATA 'AHOY Streamer\Scripts\ahoy-streamer.exe')` and check
readiness with the same path followed by `doctor`. To remove this install, close the app
and run `Remove-Item -LiteralPath (Join-Path $env:LOCALAPPDATA 'AHOY Streamer') -Recurse -Force`.
The installer downloads Python dependencies from PyPI; an internet connection is required.
Windows terminal video currently has no synchronized soundtrack, even if `mpv` is installed.
Standalone supported audio can play through the Python dependency.

### macOS or Linux

Run this in a terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/oooAHOYooo/ahoy-streamer-cli/main/install.sh | bash
~/.local/bin/ahoy-streamer
```

The installer fetches the latest `main`, creates an isolated Python environment with the
OpenCV video decoder on supported systems, and adds `ahoy-streamer` to `~/.local/bin`.
It checks internet access, reports video/audio readiness,
and prints the exact launch and uninstall commands. Rerun the installer to update; it stops
without changing a managed install that has local edits. Once `~/.local/bin` is on `PATH`, you
can use the shorter `ahoy-streamer` command.

**Before installing:** You need an internet connection, Git, and Python 3.11 or newer with
`venv` and `pip`. Check with `git --version` and `python3 --version`. On Linux, the installer
offers to install missing Git/Python/venv packages through Omarchy or a supported distribution
package manager. On macOS, install missing tools first: run `xcode-select --install` for Git,
and install Python 3.11+ from [python.org](https://www.python.org/downloads/macos/) or with
Homebrew (`brew install python@3.13`). If `python3` still points to an older Python, use
`curl -fsSL https://raw.githubusercontent.com/oooAHOYooo/ahoy-streamer-cli/main/install.sh | PYTHON=python3.13 bash`.
macOS 13+ supports terminal video; older versions open video in the browser.

**If video has no sound:** Install optional `mpv` (`brew install mpv` on macOS; on Linux use
your distribution's package manager, for example `sudo apt install mpv` or
`sudo pacman -S mpv`). Then run `~/.local/bin/ahoy-streamer doctor` to check readiness.
Terminal video works silently without `mpv`; regular supported audio uses the Python
dependency installed by the script. On Linux aarch64, regular audio opens in the browser.

To remove a one-command install later, run `~/.local/bin/ahoy-streamer-uninstall`. It confirms
before deleting the app and its virtual environment; operating-system packages are left alone.
For automated installs, run `curl -fsSL https://raw.githubusercontent.com/oooAHOYooo/ahoy-streamer-cli/main/install.sh | AHOY_INSTALL_ALLOW_SYSTEM_PACKAGES=1 bash` to allow required system prerequisites without the interactive prompt. The package manager may still require sudo access.

To install from a checkout instead:

```sh
git clone --branch main --single-branch https://github.com/oooAHOYooo/ahoy-streamer-cli.git
cd ahoy-streamer-cli
./install.sh                         # macOS/Linux: installs into .venv
.venv/bin/ahoy-streamer              # open the terminal listening room
.venv/bin/ahoy-streamer search poets --json
.venv/bin/ahoy-streamer show music:song_1 --json
.venv/bin/ahoy-streamer play music:song_1
.venv/bin/ahoy-streamer watch video:example --video=ascii
.venv/bin/ahoy-streamer doctor --json
```

To install manually on macOS into a Python virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ahoy-streamer
```

From an existing checkout on Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
ahoy-streamer                         # open the terminal listening room
ahoy-streamer search poets --json
ahoy-streamer show music:song_1 --json
ahoy-streamer play music:song_1
ahoy-streamer watch video:example --video=ascii
ahoy-streamer doctor --json
```

On Linux, `install.sh` creates an isolated `.venv` and installs the project dependencies,
including the pinned OpenCV video decoder. It does not install `mpv`; that remains optional
for video soundtracks. On macOS and Windows, create the virtual environment and install as
shown above.

Standalone audio uses the PyPI miniaudio runtime dependency and does not require Homebrew or
system mpv. Audio embedded in a video uses system mpv (`brew install mpv` on macOS) to
play alongside terminal video. Without mpv, terminal video still plays without audio. The Python
package itself does not install operating-system packages. The Linux installer only bootstraps
Git and Python venv/pip support when needed; `mpv` is distributed separately through each OS/package manager.
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
Search), arrow keys to browse, Enter for details, and Space to play the selected item,
pause/resume it while it remains selected, or switch to a different selection and stop TUI-owned
playback. Type a title or creator prefix to jump to its first match in the current section; press
Backspace to edit. Escape clears the jump; press it again to quit. Use `x` or Ctrl-X to stop, `/` to
search all catalogs, `r` or F5 to refresh, and `q` to quit when no displayed title/creator starts
with q. Data sections need a network
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

The repository is public for early testing; the Python package is not published. No project license
has been selected yet, so choose one before accepting contributions or redistributing the code.
See `docs/RELEASE.md`.
