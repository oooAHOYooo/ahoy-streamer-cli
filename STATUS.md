# Current handoff

- Stage: public standalone preview; Python package is not published to PyPI.
- Branch: `codex/continuous-radio`; implementation changes are uncommitted.
- Task: continuous local radio, persistent playback status, and faster repeat browsing.
- Radio now advances on native audio EOF and loops the selected manifest while the
  TUI runs. Pause holds playback; stop/switch/quit cancels the station sequence.
  A failed next track stops with an error instead of retrying indefinitely.
- Playback area shows title/creator plus Playing, Paused, Stopped, or External and
  control hints across sections. External playback remains controlled externally.
- TUI checks playback every 200ms while idle. Catalogs are cached only in memory for
  60 seconds and reused by search; F5/r bypasses cache. Radio opens fetch fresh data.
  Refresh preserves selection by ID when the item remains available.
- Radio is a local manifest loop from track beginnings, not synchronized station audio.
  Browser fallback cannot auto-advance. Blocking catalog fetches/search input can delay
  rollover until the main loop resumes; no background daemon/thread was introduced.
- Changed files: `src/ahoy_streamer_cli/player.py`, `src/ahoy_streamer_cli/tui.py`,
  `tests/test_radio.py`, `tests/test_tui.py`, `README.md`, `docs/SPEC.md`,
  `docs/TASKS.md`, `STATUS.md`.
- Check: `python3 -m unittest discover -s tests -v` — 38 tests run, 37 pass,
  1 skipped (miniaudio runtime dependency absent). All playback/network uses mocks.
- Check: `git diff --check` — pass.
- Not run: live API/audio, interactive terminal walkthrough, packaging/install checks.
  Real device playback remains unverified; no release artifacts were rebuilt/published.
- Next task: opt-in native radio and terminal walkthrough on target systems, then
  consider nonblocking loading/search so network waits cannot delay station rollover.
- Latest published release remains `v0.1.0-standalone-preview.2` (main `5091e8e`),
  with Windows x64, macOS Intel/Apple Silicon, and Linux x64 ZIPs. Third-party Homebrew
  tap: `oooAHOYooo/ahoy-streamer/ahoy-streamer`; macOS preview is unsigned/unnotarized.
- Stable release still needs clean-device playback validation and a project license
  decision. Keep releases marked prerelease until those checks are complete.
