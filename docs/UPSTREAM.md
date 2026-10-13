# Upstream source map

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

Verified in the local platform checkout during the terminal implementation:

- `services/content_db.py::_serialize_track` returns `id = track_id`, `audio_url`,
  `artist`, and `duration_seconds`.
- `_serialize_show` returns `id = show_id`, `video_url`, `host`, and duration;
  `_video_as_show` returns `id = video_id`, video URL, and optional host metadata.
- `/api/podcasts` returns `shows[]` with nested `episodes[]`; fallback episode audio
  uses `audio_url` and IDs are stringified.
- `/api/artists` returns `artists[]`; artist identity is `id` and display is `name`.
- `/api/events` returns both `events[]` and `videos[]`; the terminal includes both in
  its Events browse section.
- `/api/studio` returns visible `collections[]` summaries; a detail endpoint exists at
  `/api/studio/<collection_id>`.
- `/api/radio/live` returns an ordered normalized `items[]` manifest, `station.epoch_ms`,
  `server_time_ms`, and server-computed current/up-next state. `services/radio_station.py`
  deterministically hashes/sorts IDs and computes track offset from elapsed station time.
  The terminal can identify the current manifest item and seek to its approximate offset,
  but does not yet auto-advance when that item finishes.
- `/api/live-tv/channels` returns channel `items[]` and a `scheduled` flag, but no slot
  times or current-program boundaries. The SPA `useLiveTvSchedule.js` locally builds a
  rotation by cycling each channel's items and durations from a half-hour anchor. This
  is an app-side approximation; the terminal therefore calls its view a channel-library
  browse and does not claim authoritative schedule or synchronized live-TV parity.
- `/api/search?q=...` is available, but this draft searches normalized public catalog
  payloads locally so CLI/TUI results share one simple data model.

These are source observations, not proof of current production responses. Tests use
synthetic data and do not copy the live catalog or media.

Deferred endpoints: /api/podcasts, /api/radio/live, /api/live-tv/channels.
Radio manifests and TV schedules need timeline/offset semantics; channel item lists
alone do not establish synchronized live playback. Do not sell simple video playback
as live-TV parity. Existing /api/search need not be adopted for v0.1.

Player references:
- https://mpv.io/manual/stable/ (video outputs and JSON IPC)
- https://sw.kovidgoyal.net/kitty/graphics-protocol.html

Do not port the separate AHOY Player library model or assume pairing/sync exists.
