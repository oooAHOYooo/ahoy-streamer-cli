# Playback dependency notes

The playback extras are ordinary PyPI dependencies; this project does not embed their
native libraries or FFmpeg binaries in its own wheel.

- `miniaudio>=1.71,<2` (MIT): native audio output and streaming decode of MP3, WAV, FLAC,
  and Vorbis. PyPI publishes wheels for macOS, Windows x64, and Linux x86_64. Linux aarch64
  skips this dependency to avoid requiring a compiler during install; audio opens in the
  system browser there.
- `opencv-python-headless==4.12.0.88`: standard dependency on Windows/Linux; optional
  `ascii-video` extra on macOS 13+. Its separate PyPI wheel bundles FFmpeg. OpenCV-Python's
  upstream project identifies bundled FFmpeg as LGPLv2.1 and publishes third-party notices
  at [LICENSE-3RD-PARTY.txt](https://github.com/opencv/opencv-python/blob/4.x/LICENSE-3RD-PARTY.txt)
  with build/license information in the
  [upstream README](https://github.com/opencv/opencv-python/blob/4.x/README.md). Preserve
  these notices if mirroring or redistributing dependency wheels. These wheels are not
  compatible with macOS 12 or older; the default macOS playback path is the browser.
- `windows-curses>=2.4` is installed on Windows only for the keyboard TUI.

PyAV and imageio-ffmpeg were not selected: inspected wheels included FFmpeg builds with
GPL-enabled components. Recheck the exact artifact and enabled codecs before changing the
OpenCV pin or adding another decoder. This note is a dependency inventory, not legal advice.
