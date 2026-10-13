# Current handoff

- Stage: app-like public browsing draft implemented; not packaged or published.
- Branch: `codex/streamer-tui-first-draft`; pending commit/push.
- Implemented: `ahoy` entry point, doctor/search/show/play/watch commands, JSON envelopes, public catalogs for Home/Music/Videos/Podcasts/Artists/Events/Studio/Radio/AHOY TV channel libraries, cross-catalog search, item details, mpv TUI-owned background audio/window session with pause/stop, caca probe and window fallback.
- Verification: `PYTHONPYCACHEPREFIX=/private/tmp/ahoy-pycache PYTHONPATH=src python3 -m unittest discover -s tests -v` — 5 tests passed; compileall, version/help smoke, and `git diff --check` passed.
- Install smoke: blocked in sandbox. Repository-local venv creation returned EPERM; external venv lacks setuptools and network/build dependencies. No successful editable install claimed.
- Direct package import and fixture normalization tested; no live API, real audio, caca render, terminal resize, or Ctrl-C playback was manually tested.
- Upstream mapping verified read-only at `ahoy-little-platform/services/content_db.py`: track serializer uses `id=t.track_id`; show serializer uses `id=s.show_id`; video rows map video_id to id, host, video_url.
- Limitations: caca availability is inferred from `mpv --vo=help`; terminal video compatibility and actual frame output remain unverified. TUI uses curses and has no manual walkthrough yet. Radio derives the current track from public manifest epoch but plays the current item only; automatic track transitions are not implemented. AHOY TV API gives channel libraries but omits slot timing; terminal view is not synchronized live TV. Item details are limited to list data, not every SPA detail route. Network redirects must end at HTTPS; HTTP localhost origin is supported.
- Out of scope/parity gaps: accounts/login, cross-device sync/cast, payments, downloads, admin, personal saved playlists, persistent playback after app exit.
- Next phases: richer detail routes; authoritative TV schedule API; queue/track rollover and playback lifecycle; optional local bookmarks; clean install/package smoke and named-terminal manual playback checks.
