# Playback dependency notes

The playback extras are ordinary PyPI dependencies; this project does not embed their
native libraries or FFmpeg binaries in its own wheel.

On Linux, run `./install.sh` from the checkout. It creates an isolated `.venv` and installs
the project so the declared OpenCV decoder is present for terminal video. If the base Python
cannot create a venv because pip bootstrap support is missing, the installer adds the
distribution's Python pip/venv package; on Omarchy it uses `omarchy pkg add python-pip`.
This OS bootstrap is separate from `pip install` and uses the distro package manager only
when needed. `mpv` remains an optional OS package for video soundtracks.

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
