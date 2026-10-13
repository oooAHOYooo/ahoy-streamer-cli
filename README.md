# AHOY Streamer Terminal

A keyboard-first terminal listening room for discovering and playing independent media from AHOY Streamer, with a small JSON command interface for agents.

**Status: app-like terminal browsing draft. Not published as a package; live playback has not been manually verified.**

## Start here

Read `AGENTS.md`, `STATUS.md`, then the single assigned task in `docs/TASKS.md`.
The implementation contract is `docs/SPEC.md`; upstream evidence is in `docs/UPSTREAM.md`.

## First release

The terminal app exposes Home, Music, Videos, Podcasts, Artists, Events, Studio, Radio,
AHOY TV channel libraries, and Search in one keyboard-driven interface. It browses public
catalogs and opens item details; mpv plays music/podcast/radio audio in the background,
with pause/stop controls, and video in experimental terminal ASCII or a separate player
window. This is a native terminal companion to the website, not a port of its account,
payment, administration, or synchronized-device features.

A small command interface remains alongside the TUI so agents can search, inspect,
and request playback without navigating screens. JSON is a stable public contract.

Usage:

```sh
git clone --branch codex/streamer-tui-first-draft --single-branch https://github.com/oooAHOYooo/ahoy-streamer-cli.git
cd ahoy-streamer-cli
brew install mpv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ahoy-streamer                         # open the terminal listening room
ahoy-streamer search poets --json
ahoy-streamer show music:song_1 --json
ahoy-streamer play music:song_1
ahoy-streamer watch video:example --video=ascii
```

Install mpv separately for playback. Terminal video is experimental and requires an mpv
build with the `caca` output; press `w` on a selected video or use
`ahoy-streamer watch video:ID --video=window` when unavailable. Use number keys 0–9 (Home through
Search), arrow keys or `j`/`k` to browse, Enter for details, `p` to play, Space to pause,
`x` to stop, `/` to search, `r` to refresh, and `q` to quit. Data sections need a network
connection. AHOY TV currently displays the public channel libraries; the API does not
provide authoritative slot timing, so the CLI does not claim synchronized live-TV parity.

See [the feature map and follow-up phases](docs/TASKS.md) for covered sections and gaps.

## Chosen implementation

Python 3.11+, standard library runtime, argparse, urllib, subprocess, unittest.
Package: `ahoy_streamer_cli`; installed command: `ahoy-streamer`.
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
