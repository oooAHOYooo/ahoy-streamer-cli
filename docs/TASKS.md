# Ordered implementation tasks

All tasks begin with AGENTS.md and STATUS.md. Complete one task per session.
Default test command after T01: `python3 -m unittest discover -s tests -v`.
Packaging smoke command: `python3 -m pip install -e .` in a project virtualenv.

## T01 — Scaffold and machine interface
Dependencies: none. Read: SPEC commands/JSON/modules.
Create pyproject.toml with setuptools, package src layout, `ahoy` entry point,
.gitignore additions as needed, output/config modules, help/version/doctor.
Do not implement placeholders that report success for unimplemented commands.
Tests: no-arg help; version without network; doctor missing mpv; clean JSON stdout;
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
Implement foreground audio/video playback, mpv discovery, and the bounded ASCII-video
experiment using `--vo=caca`. Keep window playback available. No daemon or queue.
Tests: arguments, missing executable/driver, URL validation, player failure and cleanup.
Manual: short video, selected terminal/mpv version, resize and Ctrl-C. Record limitations.

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

## Later backlog (do not implement during T01–T05)
- Podcasts, channels, radio and synchronized TV after playback/timeline contracts are clear.
- Local IPC controller + status/pause/queue, with process ownership and stale socket tests.
- Public channels/TV/radio playback only after timeline behavior is specified.
- Browser-based auth and saved collections after dedicated security/API design.
- Kitty/Sixel, Windows support, signed binaries, package-manager formula.

Escalate design questions only if the fixed contract cannot be satisfied. A failed test
or missing executable is normally a task-level fix, not a reason to redesign the tool.
