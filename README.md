# AHOY Streamer Terminal

A keyboard-first terminal listening room for discovering and playing independent media from AHOY Streamer, with a small JSON command interface for agents.

**Status: planning repository. No CLI is implemented or published yet.**

## Start here

Read `AGENTS.md`, `STATUS.md`, then the single assigned task in `docs/TASKS.md`.
The implementation contract is `docs/SPEC.md`; upstream evidence is in `docs/UPSTREAM.md`.

## First release

The first usable release is a keyboard-driven TUI for browsing music and videos and
playing them through mpv. Video should be viewable inside the terminal in ASCII art,
with window playback available when ASCII output is unavailable or unsuitable. Podcasts
and live channels follow after their playback behavior is understood.

A small command interface remains alongside the TUI so agents can search, inspect,
and request playback without navigating screens. JSON is a stable public contract.

Planned usage (these commands do not exist yet):

```sh
ahoy                         # open the terminal listening room
ahoy search poets --json
ahoy show music:song_1 --json
ahoy play music:song_1
ahoy watch video:example --video=ascii
```

## Chosen implementation

Python 3.11+, standard library runtime, argparse, urllib, subprocess, unittest.
Package: `ahoy_streamer_cli`; installed command: `ahoy`.
Use mpv as an optional external player; catalog operations must work without it.
Initial supported playback platforms: macOS and Linux. Windows is deferred.
No server, database, account system, custom decoder, or framework in the first release.

## Build efficiently

Complete one task per session. Preserve the command contract. Use small offline fixtures.
Record results in `STATUS.md` so the next agent can start without reading chat history.
See `docs/HANDOFF.md` for a ready-to-use implementation prompt.

## Publishing

GitHub: https://github.com/oooAHOYooo/ahoy-streamer-cli

The repository is private while planning. Public release, package name availability, and license are
release decisions, not completed work. See `docs/RELEASE.md`.
