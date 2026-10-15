# Current handoff

- Stage: public-catalog TUI draft with local audio and terminal video; package not published.
- Branch: `codex/video-browse-during-playback`, based on `origin/main` at `ca55098` after successful `git fetch origin` and `git pull --ff-only origin main` in the preceding turn.
- Task: terminal video launched from the TUI keeps a scrollable video list beside the picture (below it on narrow terminals). Up/Down browse while playback continues, Enter switches video, and `q` returns with the browsed item selected. `f` or Tab toggles instantly between browse and full-picture views, with a brief on-screen cue; playback and selection persist. CLI `watch` keeps its existing full-picture view.
- Speed: paused video no longer decodes or redraws the same frame repeatedly when idle; stable TUI video layouts overwrite their cells without a full erase each frame. Layout/terminal-size/mode-cue changes still clear the screen. Live performance has not been measured.
- Playback limits: terminal grayscale video and optional mpv soundtrack on macOS/Linux; Windows terminal video remains silent. Browser/window fallback remains available. Live device/media behavior is unverified.
- Verification: `python3 -m unittest discover -s tests -v` — 37 tests passed, one skipped because the runtime decoder dependency is not installed. New checks cover safe browse rendering, arrow decoding, Enter switching, full-screen toggling while paused, and TUI selection handoff. `git diff --check` — passed. No live API, audio, or video playback check was run.
- Changed files: `src/ahoy_streamer_cli/player.py`, `src/ahoy_streamer_cli/tui.py`, `tests/test_playback.py`, `tests/test_tui.py`, `README.md`, `docs/SPEC.md`, `STATUS.md`.
- Unrelated state: pre-existing untracked nested `ahoy-streamer-cli/` directory was left untouched.
- Remaining blocker: verify actual video layout, controls, and audio synchronization in an interactive terminal with OpenCV/mpv installed. Next task: complete T05 clean-install/package checks and release documentation separately.
