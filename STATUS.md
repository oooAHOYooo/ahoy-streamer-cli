# Current handoff

- Stage: first runnable draft implemented (T01–T04 scope); not packaged or published.
- Branch: `codex/streamer-tui-first-draft`; pending commit/push.
- Implemented: installable `ahoy` entry point, doctor/search/show/play/watch commands, JSON envelopes, catalog normalization/search, mpv foreground playback, Music/Videos curses TUI, caca probe and window fallback.
- Verification: `python3 -m unittest discover -s tests -v` — 4 tests passed.
- Install smoke: blocked in sandbox. Repository-local venv creation returned EPERM; external venv lacks setuptools and network/build dependencies. No successful editable install claimed.
- Direct package import and fixture normalization tested; no live API, real audio, caca render, terminal resize, or Ctrl-C playback was manually tested.
- Upstream mapping verified read-only at `ahoy-little-platform/services/content_db.py`: track serializer uses `id=t.track_id`; show serializer uses `id=s.show_id`; video rows map video_id to id, host, video_url.
- Limitations: caca availability is inferred from `mpv --vo=help`; terminal video compatibility and actual frame output remain unverified. TUI uses curses and has no manual walkthrough yet. Network redirects must end at HTTPS; HTTP localhost origin is supported.
- Next: run install smoke where build dependencies are available; test live catalog/playback on named macOS terminal/mpv build; resolve any runtime integration issues. Keep account, channels, podcasts, daemon, and saved queue deferred.
