# AHOY Streamer CLI

An agent-friendly command line for discovering and playing independent media from AHOY Streamer.

**Status: planning repository. No CLI is implemented or published yet.**

## Start here

Read `AGENTS.md`, `STATUS.md`, then the single assigned task in `docs/TASKS.md`.
The implementation contract is `docs/SPEC.md`; upstream evidence is in `docs/UPSTREAM.md`.

## First release

Search music and videos, inspect a stable media ID, and play through a locally installed mpv.
Machine-readable JSON is a first-class interface. Terminal video is the next milestone;
a full-screen interface comes later.

Planned usage (these commands do not exist yet):

```sh
ahoy search poets --json
ahoy show music:song_1 --json
ahoy play music:song_1
ahoy watch video:example --video=terminal
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

A local Git repository is initialized. GitHub creation is pending authentication.
Intended repository name: `ahoy-streamer-cli`; proposed owner: `oooAHOYooo`.
Start private while planning. Public release, package name availability, and license are
release decisions, not completed work. See `docs/RELEASE.md`.
