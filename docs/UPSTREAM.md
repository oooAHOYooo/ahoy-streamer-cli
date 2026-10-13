# Source map (read only when implementing T02)

Inspected 2026-10-13 at platform commit 47e4b48ba6c61ccffb82bc3b9e406677b3aa63af.
Repository: https://github.com/oooAHOYooo/ahoy-little-platform
Local checkout: /Users/agworkywork/ahoy-little-platform (optional convenience only).
These are source observations, not proof of current production responses.

| Source | Observed behavior |
|---|---|
| app.py, api_music around line 1602 | GET /api/music; DB get_all_tracks, fallback music.json; tracks wrapper |
| app.py, api_shows around line 1722 | GET /api/shows; DB get_all_shows, fallback shows.json; shows wrapper |
| static/data/music.json | track_id, title, artist, duration_seconds, audio_url |
| spa/src/composables/useSearch.js | Client loads and normalizes catalogs; useful shape reference |
| README.md around line 151 | Blueprint origin documented as https://app.ahoy.ooo |

T02: inspect get_all_tracks/get_all_shows owning serializers only as needed to verify
DB ID precedence and video creator fields. One bounded read-only endpoint smoke
check may confirm live shape, but tests must not depend on live data. Keep fixtures
synthetic; never copy the full production catalog or large media files.

Deferred endpoints: /api/podcasts, /api/radio/live, /api/live-tv/channels.
Radio manifests and TV schedules need timeline/offset semantics; channel item lists
alone do not establish synchronized live playback. Do not sell simple video playback
as live-TV parity. Existing /api/search need not be adopted for v0.1.

Player references:
- https://mpv.io/manual/stable/ (video outputs and JSON IPC)
- https://sw.kovidgoyal.net/kitty/graphics-protocol.html

Do not port the separate AHOY Player library model or assume pairing/sync exists.
