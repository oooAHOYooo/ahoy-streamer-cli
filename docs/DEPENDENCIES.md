# Playback dependency notes

The playback extras are ordinary PyPI dependencies; this project does not embed their
native libraries or FFmpeg binaries in its own wheel.

On Linux, install with `curl -fsSL https://raw.githubusercontent.com/oooAHOYooo/ahoy-streamer-cli/main/install.sh | bash`,
or run `./install.sh` from a checkout. The installer creates an isolated `.venv`, installs
the project so the declared OpenCV decoder is present, and adds a launcher under
`~/.local/bin`. If Git, Python, or the base Python's venv/pip bootstrap is missing, it installs the
required OS package through Omarchy or the detected distribution package manager, after asking
the user. It preflights architecture, network access, and venv/pip support, then runs `doctor`
to summarize playback readiness. Re-running updates a clean managed checkout; local edits stop
the update. `~/.local/bin/ahoy-streamer-uninstall` removes the managed checkout and virtual
environment after confirmation but leaves OS packages installed. This OS bootstrap is separate
from `pip install`. `mpv` remains an optional OS package for video soundtracks.

- `miniaudio>=1.71,<2` (MIT): native audio output and streaming decode of MP3, WAV, FLAC,
  and Vorbis. URLs are identified by extension or HTTP content type; extensionless signed URLs
  are offered to miniaudio's format sniffer. Unsupported containers/codecs fall back to the
  system browser. PyPI publishes wheels for macOS, Windows x64, and Linux x86_64. Linux aarch64
  skips this dependency to avoid requiring a compiler during install; audio opens in the
  system browser there.
- `opencv-python-headless==4.12.0.88`: standard dependency on Windows/Linux and macOS 13+
  (detected from Darwin kernel release 22+); earlier macOS versions skip it so the package
  still installs and use browser video. Its separate PyPI wheel bundles FFmpeg. OpenCV-Python's
  upstream project identifies bundled FFmpeg as LGPLv2.1 and publishes third-party notices
  at [LICENSE-3RD-PARTY.txt](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt)
  with build/license information in the
  [upstream README](https://github.com/opencv/opencv-python/blob/4.x/README.md). Preserve
  these notices if mirroring or redistributing dependency wheels. These wheels are not
  compatible with macOS 12 or older; those systems use browser video.
- `windows-curses>=2.4` is installed on Windows only for the keyboard TUI.

PyAV and imageio-ffmpeg were not selected: inspected wheels included FFmpeg builds with
GPL-enabled components. Recheck the exact artifact and enabled codecs before changing the
OpenCV pin or adding another decoder. This note is a dependency inventory, not legal advice.
