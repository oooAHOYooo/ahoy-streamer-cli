# Implementation contract v1

## Scope

v0.1 is a keyboard-first terminal listening room (TUI) for browsing music and video,
with a concise agent-friendly command interface and JSON output. The TUI is the default
when `ahoy` runs interactively with no command. Video playback should stay in the
terminal as ASCII art when supported; window playback is the visible fallback.

Start with music and on-demand videos. Add podcasts and live channels after their
playback and timeline behavior is specified. No accounts, purchases, downloads,
transcript generation, cross-device control, recommendation AI, playlist sync, daemon,
or telemetry in the first release.

The TUI is for settling in and watching/listening, not a dense admin dashboard. Use a
small set of visible destinations (Music, Videos, Podcasts, Channels as they become
supported), a selected-item list, and a now-playing area. Keyboard navigation must
have an always-visible hint and work without a mouse. Search and playback must also
remain usable from commands when no TTY exists.

## Commands

- `ahoy` on an interactive TTY: launch the listening-room TUI.
- `ahoy` without a TTY or `ahoy --help`: help, no network.
- `ahoy --version`: package version, no network.
- `ahoy doctor [--json]`: Python/platform/mpv availability; no network or playback.
- `ahoy search QUERY [--type music|video|all] [--limit N] [--json]`:
  default type all, limit 20; valid limit 1..100; case-insensitive substring search
  over title and creator. Stable ordering by type, casefolded title, then ID.
- `ahoy show TYPE:ID [--json]`: normalized item, unknown IDs exit 4.
- `ahoy play music:ID`: foreground audio through mpv, Ctrl-C cleans up child.
- `ahoy watch video:ID [--video ascii|window]`: default ascii in the TUI;
  command mode defaults to ascii unless `--video=window` is selected. Wrong media type is a usage error.

Data commands accept `--base-url URL` and `--timeout SECONDS` after the subcommand.
Origin precedence: flag > AHOY_BASE_URL > https://app.ahoy.ooo.
Timeout default 10, valid 1..60 seconds; enforce bounded response size (5 MiB).
Allow HTTPS origins, and HTTP only for localhost/127.0.0.1/[::1] development.
Do not support origin credentials. Apply policy to redirects as well.
No automatic retries or disk cache initially. For `all`, either endpoint failing means
an explicit error, not silently incomplete successful results.

## JSON

`--json` is available on search/show/doctor, including their errors. Output exactly one
JSON object plus newline on stdout; diagnostics only on stderr. Help is always text.

Success: `{"schema_version":1,"ok":true,"data":...}`.
Error: `{"schema_version":1,"ok":false,"error":{"code":"NOT_FOUND","message":"..."}}`.
Search data: `{"items":[],"count":0}`; count means returned count after limit.
Show data: normalized media object. Doctor data: platform/Python/mpv diagnostic fields.

Exit codes: 0 success; 2 usage/validation; 3 network/HTTP/invalid upstream schema;
4 media ID not found; 5 missing mpv or unsupported requested rendering;
6 player failure; 130 interrupted. Doctor exits 5 if mpv absent while reporting details.
Argparse failures must honor --json on JSON-capable commands.

## Media model

`id` (namespaced string), `type` (music|video), `source_id` (string), `title`
(string), `creator` (string|null), `duration_seconds` (nonnegative number|null),
`media_url` (HTTPS string|null).

Music ID priority: track_id then id. Video: show_id then id. Reject items without
any nonempty ID or title. Namespace preserves arbitrary source ID text after the
first colon; never create IDs from titles or array indices. Conflicting duplicate
IDs are upstream errors. Missing/invalid optional duration is null. Missing media URL
allows discovery but playback fails with code 6 and a useful message.
Normalize music audio_url, artist; video video_url, host (artist fallback).
Validate these proposed field mappings against owning DB serializers in T02.
Do not invent a playable URL. Only HTTPS media URLs initially; deny local paths,
file URLs and shell-like player options. Recheck redirected media behavior with mpv
before public release. No private API tokens are needed or forwarded to media hosts.

## Modules (create when needed)

src/ahoy_streamer_cli/{cli,output,config,catalog,models,player,tui}.py
Keep screen rendering and keyboard input thin; the TUI calls the same catalog/player
services as the command interface. Prefer a maintained minimal TUI dependency only if
stdlib rendering becomes brittle; document the choice and pin supported versions.
Use dependency injection for HTTP transport and subprocess invocation in tests.
Keep CLI parsing separate from catalog normalization and player invocation.
No network calls at import time. No new runtime dependency without a concrete need.

## Playback

Use shutil.which to find mpv. subprocess with shell=False, explicit argument array,
--no-config, -- before media URL; audio adds --no-video. Suppress child stdout to
preserve future scripting compatibility; actionable player failures go to stderr.
Foreground process lifetime only in v0.1: no misleading `status` or `pause` command
that cannot control another process. Search/doctor must work on headless systems.

T03 is a time-boxed terminal-video experiment using mpv `--vo=caca` for colored
ASCII output. It must not download or transcode media. Probe whether the local mpv build
has the driver and require a TTY; on failure, explain how to select window playback.
Restore terminal state and terminate the player on interruption. Keep window playback as
a user-selectable fallback. Validate one short video on a named terminal/mpv build before
calling the experiment usable; document frame-rate, color, resize, and compatibility
limits. If caca is absent, test whether a small optional renderer is justified before
adding dependencies. Kitty/Sixel are later optional render modes, not ASCII substitutes.

## TUI behavior

- `ahoy` without arguments opens the TUI only when stdin/stdout are TTYs; explicit
  subcommands remain scriptable and never launch a screen.
- Categories are immediately visible in the first view; avoid hidden arrow-only
  discovery or modal navigation for the primary destinations.
- `q` exits, `/` searches, arrows or `j/k` move selection, Enter opens/plays,
  Space pauses only when playback control exists. Show actionable key hints.
- TUI refreshes remain bounded, selection survives refresh when the item still exists,
  and network/player errors appear in the interface without a traceback.
- TUI rendering is testable with a fake terminal; no full-screen UI in unit tests.

## Release acceptance

Offline tests prove output contract, schema validation, network failures, subprocess
arguments and cleanup. Opt-in manual checks prove real media/audio/video on macOS
and Linux; until then report playback as unverified on the unchecked platform.
