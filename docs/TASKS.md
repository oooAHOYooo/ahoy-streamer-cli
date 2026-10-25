# Ordered implementation tasks

All tasks begin with AGENTS.md and STATUS.md. Complete one task per session.
Default test command after T01: `python3 -m unittest discover -s tests -v`.
Packaging smoke command: `python3 -m pip install -e .` in a project virtualenv.

## T01 — Scaffold and machine interface
Dependencies: none. Read: SPEC commands/JSON/modules.
Create pyproject.toml with setuptools, package src layout, `ahoy-streamer` entry point,
.gitignore additions as needed, output/config modules, help/version/doctor.
Do not implement placeholders that report success for unimplemented commands.
Tests: no-arg help; version without network; doctor bundled playback readiness; clean JSON stdout;
invalid option exit 2 in JSON mode; origin/timeout validation.
Done: editable install works and tests pass with mocked executable discovery.

## T02 — Catalog discovery
Dependencies: T01. Read: SPEC media/network contract and UPSTREAM.md.
Implement HTTP adapter, normalization, search and show for music/video. Validate
upstream DB mappings. Extend synthetic fixtures only for meaningful edge cases.
Tests: track_id and legacy id, video IDs, missing fields, duplicate ID conflicts,
empty catalogs, search order/limit, 404/500/timeouts, invalid JSON, oversized body,
unsafe origins/redirects, control-sequence stripping and unknown media ID.
Done: search/show pass offline; optional live smoke is separately recorded.

## T03 — Playback and ASCII video experiment
Dependencies: T02. Read: SPEC playback.
Implement portable audio with miniaudio, OpenCV grayscale ASCII video, optional mpv/browser
window fallback. Pin the LGPL FFmpeg wheel and preserve its license notices. No daemon/queue.
Tests: synthetic audio decode and luma frame mapping, backend adapter, URL validation, errors.
Manual: short audio/video, selected terminal, resize and Ctrl-C. Record platform limitations.

## T04 — Listening-room TUI
Dependencies: T01–T03. Read: SPEC TUI behavior.
Build the keyboard-first browsing and now-playing interface on existing services. Keep
Music and Videos visible immediately; show future sections only once implemented.
Tests: input/navigation/rendering with fake terminal; non-TTY invocation does not hang.
Done: an interactive local walkthrough can search, select, play, exit and recover from errors.

## T05 — Distribution and onboarding
Dependencies: T01–T04. Read: RELEASE.md.
Add clean-install instructions, supported-platform table, short agent command guide,
CI for offline tests, and reproducible package-build checks. Keep publishing manual.
Done: clean virtualenv install and CLI invocation; sdist/wheel contents verified;
no secrets, media, local state or caches packaged. Public licensing remains a decision.

## App-parity follow-up phases

- P1 — Detail coverage: add richer artist/event/podcast/studio detail fetches and
  keyboard back/forward navigation. Current selection details use public list payloads.
- P2 — TV guide fidelity: API `/api/live-tv/channels` currently returns each channel's
  item library plus `scheduled`; slot IDs/times and show schedule metadata are discarded
  in the response. SPA `useLiveTvSchedule.js` builds a local rotation from item durations,
  anchored to the current half-hour. CLI labels these as channel libraries and does not
  claim server-scheduled/live parity. Add authoritative schedule API before mirroring a
  real guide or synchronized playback.
- P3 — Persistent playback lifecycle: current TUI owns its local audio device and offers
  pause/stop while open; quit ends playback. Cross-session daemon/control is deferred.
- P4 — User features: accounts, cross-device sync/casting, purchases, downloads, admin,
  saved playlists, likes/follows, and notifications stay out of scope. Consider local-only
  bookmarks/queues only after playback ownership and storage contracts are designed.
- P5 — Wider media: poems, What's New, games, and live TV guide interaction are future
  navigation candidates after the core catalog/detail experience stabilizes.

## Remaining release backlog

- Finish P1–P5 above; podcasts, artists, events, studio, and radio browsing are already
  implemented in the current draft. Radio playback starts at the manifest's current item
  but does not yet advance automatically. AHOY TV shows channel libraries, not a verified
  synchronized schedule.
- T05: clean-install/package checks, CI, supported-platform documentation, and licensing.
- A third-party Homebrew tap now installs the macOS preview. Optional later work: Kitty/Sixel
  renderers, expanded Windows terminal checks, Apple signing/notarization, and other package
  manager distribution.

Escalate design questions only if the fixed contract cannot be satisfied. A failed test
or missing executable is normally a task-level fix, not a reason to redesign the tool.
