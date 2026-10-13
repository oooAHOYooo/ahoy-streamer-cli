# Implementation contract v1

## Scope

v0.1 is a keyboard-first terminal listening room (TUI) for browsing music and video,
with a concise agent-friendly command interface and JSON output. The TUI is the default
when `ahoy-streamer` runs interactively with no command. Video playback should stay in the
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

- `ahoy-streamer` on an interactive TTY: launch the listening-room TUI.
- `ahoy-streamer` without a TTY or `ahoy-streamer --help`: help, no network.
- `ahoy-streamer --version`: package version, no network.
- `ahoy-streamer doctor [--json]`: Python/platform/audio/video backend and optional mpv availability; no network or playback.
- `ahoy-streamer search QUERY [--type music|video|all] [--limit N] [--json]`:
  default type all, limit 20; valid limit 1..100; case-insensitive substring search
  over title and creator. Stable ordering by type, casefolded title, then ID.
- `ahoy-streamer show TYPE:ID [--json]`: normalized item, unknown IDs exit 4.
- `ahoy-streamer play music:ID`: foreground audio through miniaudio (or system browser fallback), Ctrl-C cleans up playback.
- `ahoy-streamer watch video:ID [--video ascii|window]`: default ascii in the TUI;
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
Show data: normalized media object. Doctor data: platform/Python/backend diagnostic fields.

Exit codes: 0 success; 2 usage/validation; 3 network/HTTP/invalid upstream schema;
4 media ID not found; 5 missing playback backend or unsupported requested rendering;
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

Audio uses miniaudio's bundled native library and a streaming HTTPS response adapter.
Supported direct suffixes are MP3, WAV, FLAC, OGG/OGA Vorbis. HLS/playlists and unknown
suffixes fail explicitly. Linux aarch64 skips miniaudio's runtime wheel and falls back to
the system browser for audio. Seeking and radio track rollover are not implemented.
The TUI owns audio output and supports pause/stop while it remains open.

ASCII video uses OpenCV VideoCapture to decode/resize frames and a local monochrome luma
renderer. Pin `opencv-python-headless==4.12.0.88`; do not float to OpenCV 5 without a fresh
license audit. Windows/Linux install it normally; macOS uses browser video by default. On
macOS 13+, the `ascii-video` extra enables ASCII. Do not install that extra on macOS 12 or
earlier (including Big Sur): the PyPI wheel requires macOS 13 and older OpenCV wheel tags hid
incompatible system-library minimums. If cv2 is missing, `--video=ascii` launches the browser
and reports that fallback. The upstream project says its wheels bundle LGPLv2.1 FFmpeg. Keep
the upstream license and third-party notices available to users; the dependency is installed
as its own wheel. Frame rate is capped at 30 fps and frames are resized to terminal dimensions.
ASCII mode is silent. Window mode prefers mpv and otherwise opens the browser, including audio.

## TUI behavior

- `ahoy-streamer` without arguments opens the TUI only when stdin/stdout are TTYs; explicit
  subcommands remain scriptable and never launch a screen.
- Categories are immediately visible in the first view; avoid hidden arrow-only
  discovery or modal navigation for the primary destinations.
- `q` exits, `/` searches, arrows or `j/k` move selection, Enter opens/plays,
  Space pauses only when playback control exists. Show actionable key hints.
- TUI refreshes remain bounded, selection survives refresh when the item still exists,
  and network/player errors appear in the interface without a traceback.
- TUI rendering is testable with a fake terminal; no full-screen UI in unit tests.

## Release acceptance

Offline tests prove output contract, schema validation, network failures, ASCII luma mapping,
and the miniaudio adapter. Opt-in manual checks prove device audio and URL video decode on
macOS Intel/Apple Silicon, Windows x64, and Linux x86_64/aarch64. OpenCV 4.12 wheels exist for
Windows x64/Linux x86_64/aarch64; macOS 13+ uses the optional extra and older macOS uses
browser video. Miniaudio publishes no Linux aarch64 wheel, so that platform gets browser audio
fallback. The miniaudio sdist can require a compiler and is intentionally not selected there.
Until manually checked, report real device playback unverified on each platform.
