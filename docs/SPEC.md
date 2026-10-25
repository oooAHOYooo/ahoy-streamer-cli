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
No automatic retries or disk cache initially. The TUI may reuse section catalogs in memory
for up to 60 seconds; explicit refresh bypasses this cache and radio opens fetch fresh data. For `all`, either endpoint failing means
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
Supported formats are MP3, WAV, FLAC, and OGG/OGA Vorbis. Signed URLs without file extensions
are identified from their HTTP content type or passed to miniaudio's format sniffer. Known
unsupported formats and playlists fall back to the system browser. Linux aarch64 skips
miniaudio's runtime wheel and falls back to the system browser for audio. Audio seeking is not implemented. In the TUI, native radio audio advances at EOF and
loops the selected manifest locally, beginning each track at zero. Pause holds the sequence;
stop, switching playback, and quit cancel it. Rollover failure stops with an actionable error;
external browser playback cannot auto-advance. This does not promise station synchronization.
The TUI owns audio output and supports pause/stop while it remains open.

ASCII video uses OpenCV VideoCapture to decode/resize frames and a local monochrome luma
renderer. Pin `opencv-python-headless==4.12.0.88`; do not float to OpenCV 5 without a fresh
license audit. Windows/Linux install it normally; macOS uses browser video by default. On
macOS 13+, OpenCV installs by default based on Darwin kernel release 22+. macOS 12 and older
skip OpenCV so a standard install remains usable; if cv2 is missing or cannot decode a stream,
`--video=ascii` launches the browser and reports that fallback. The upstream project says its
wheels bundle LGPLv2.1 FFmpeg. Keep
the upstream license and third-party notices available to users; the dependency is installed
as its own wheel. Frame rate is capped at 30 fps and frames are resized to terminal dimensions.
The terminal renderer defaults to 2×2 grayscale quadrants: each character cell carries four spatial
samples, assigned to a two-tone 24-bit grayscale mosaic. `r` cycles through the optional
grayscale/Braille hybrid, shaded ASCII, and Braille-only rendering.
The image reserves one row for a compact seek timeline; playback state, position, and controls
are displayed in the terminal window title. Left/Right seek by ten seconds and Home/End jump to the start or near
the end when the stream decoder supports seeking. `v` toggles a subtle 3x3 soft-focus blend over
the frame luminance. Position and duration may be approximate or
unavailable for live/extensionless streams; report unsupported seeking in the title. Space
pauses/resumes and `q` returns.
Embedded video audio is played by system mpv in audio-only mode on macOS and Linux;
pause, seek, and exit control that process along with the terminal renderer. Without mpv, the
terminal renderer continues without audio and shows the limitation in the window title. Windows
also displays terminal video without soundtrack because synchronized audio controls are not
implemented there. Window mode prefers mpv and otherwise opens the browser.

mpv is an operating-system dependency installed through platform-specific distribution channels;
the Python package does not run privileged or package-manager commands during `pip install`.

## TUI behavior

- `ahoy-streamer` without arguments opens the TUI only when stdin/stdout are TTYs; explicit
  subcommands remain scriptable and never launch a screen.
- Categories are immediately visible in the first view; avoid hidden arrow-only
  discovery or modal navigation for the primary destinations.
- `q` exits, `/` searches, arrows or `j/k` move selection, Enter opens/plays,
  Space starts the selected item when idle, pauses/resumes it when it is already current, and
  switches to a different selected item by stopping TUI-owned playback first.
  ASCII video accepts Space to pause/resume, Left/Right to seek by ten seconds, Home/End to jump,
  and `q` to return. A bare Escape must not exit video; CSI/SS3 and Windows extended-key arrow
  sequences are normalized into seek/navigation controls. If a selected item is currently
  playing outside the TUI (system browser), explain that playback must be controlled there.
  Show actionable key hints.
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
