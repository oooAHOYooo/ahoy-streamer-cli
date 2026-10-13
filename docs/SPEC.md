# Implementation contract v1

## Scope

v0.1: help/version, doctor, music/video search, media inspection, foreground audio
playback and ordinary video-window playback. v0.2: experimental colored-character
terminal video. Later: interactive interface and local player control.

No accounts, purchases, downloads, transcripts generation, cross-device control,
recommendation AI, playlists sync, daemon, or telemetry in v0.1.

## Commands

- `ahoy` or `ahoy --help`: help, no network.
- `ahoy --version`: package version, no network.
- `ahoy doctor [--json]`: Python/platform/mpv availability; no network or playback.
- `ahoy search QUERY [--type music|video|all] [--limit N] [--json]`:
  default type all, limit 20; valid limit 1..100; case-insensitive substring search
  over title and creator. Stable ordering by type, casefolded title, then ID.
- `ahoy show TYPE:ID [--json]`: normalized item, unknown IDs exit 4.
- `ahoy play music:ID`: foreground audio through mpv, Ctrl-C cleans up child.
- `ahoy watch video:ID [--video window|terminal]`: default window;
  terminal mode added in T04. Wrong media type is a usage error.

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

src/ahoy_streamer_cli/{cli,output,config,catalog,models,player}.py
Use dependency injection for HTTP transport and subprocess invocation in tests.
Keep CLI parsing separate from catalog normalization and player invocation.
No network calls at import time. No new runtime dependency without a concrete need.

## Playback

Use shutil.which to find mpv. subprocess with shell=False, explicit argument array,
--no-config, -- before media URL; audio adds --no-video. Suppress child stdout to
preserve future scripting compatibility; actionable player failures go to stderr.
Foreground process lifetime only in v0.1: no misleading `status` or `pause` command
that cannot control another process. Search/doctor must work on headless systems.

T04 terminal uses mpv --vo=tct (colored Unicode, not literal ASCII). Require a TTY;
probe available drivers; fail clearly rather than silently opening a window. Restore
terminal and terminate the child on interruption. Kitty/Sixel and literal ASCII are
optional follow-ups; support varies with terminal and mpv build.

## Release acceptance

Offline tests prove output contract, schema validation, network failures, subprocess
arguments and cleanup. Opt-in manual checks prove real media/audio/video on macOS
and Linux; until then report playback as unverified on the unchecked platform.
