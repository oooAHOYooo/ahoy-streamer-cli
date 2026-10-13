import json
import re
import urllib.error
import urllib.request

from .config import base_url, timeout

MAX_BODY = 5 * 1024 * 1024
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
SECTIONS = {
    "music": ("/api/music", "tracks"), "video": ("/api/shows", "shows"),
    "podcasts": ("/api/podcasts", "shows"), "artists": ("/api/artists", "artists"),
    "events": ("/api/events", "events"), "studio": ("/api/studio", "collections"),
    "radio": ("/api/radio/live", "items"), "tv": ("/api/live-tv/channels", "channels"),
}


def clean(value):
    return CONTROL.sub("", str(value)) if value is not None else None


def fetch(url, seconds):
    req = urllib.request.Request(url, headers={"User-Agent": "ahoy-streamer-terminal/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=seconds) as response:
            final = response.geturl()
            if not final.startswith("https://"):
                raise ValueError("catalog redirect must use HTTPS")
            body = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"catalog returned HTTP {e.code}") from e
    if len(body) > MAX_BODY:
        raise ValueError("catalog response exceeds 5 MiB")
    return json.loads(body)


def normalize(kind, raw, parent=None):
    if not isinstance(raw, dict):
        return None
    if kind == "music":
        source_id = raw.get("track_id") or raw.get("id")
    elif kind in {"video", "tv_program", "event_video"}:
        source_id = raw.get("show_id") or raw.get("id")
    else:
        source_id = raw.get("episode_id") or raw.get("id")
    title = clean(raw.get("title"))
    if source_id is None or not str(source_id).strip() or not title or not title.strip():
        return None
    duration = raw.get("duration_seconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0:
        duration = None
    if kind in {"music", "podcast", "radio"}:
        media_url = clean(raw.get("audio_url") or raw.get("enclosure_url") or raw.get("file_url"))
        creator = clean(raw.get("artist") or raw.get("author") or (parent or {}).get("title"))
    else:
        media_url = clean(raw.get("video_url") or raw.get("mp4_link") or raw.get("trailer_url") or raw.get("url"))
        creator = clean(raw.get("host") or raw.get("artist"))
    namespace = "video" if kind in {"video", "tv_program", "event_video"} else kind
    item = {"id": f"{namespace}:{source_id}", "type": kind, "source_id": str(source_id),
            "title": title.strip(), "creator": creator, "duration_seconds": duration, "media_url": media_url}
    for field in ("description", "date", "published_date", "category", "cover", "cover_art", "thumbnail",
                  "collection_id", "photo_count", "ticket_url", "slug", "tags", "artist_url"):
        if field in raw:
            item[field] = raw[field]
    return item


def catalog(kind, origin=None, seconds=10):
    if kind not in {"music", "video"}:
        raise ValueError(f"unsupported media type: {kind}")
    path, key = SECTIONS[kind]
    data = fetch(base_url(origin) + path, timeout(seconds))
    entries = data.get(key) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"invalid {kind} catalog: expected {key} list")
    result, seen = [], {}
    for raw in entries:
        item = normalize(kind, raw)
        if item is None:
            continue
        if item["id"] in seen and seen[item["id"]] != item:
            raise ValueError(f"conflicting duplicate ID {item['id']}")
        if item["id"] not in seen:
            seen[item["id"]] = item
            result.append(item)
    return result


def section_items(section, origin=None, seconds=10):
    origin, seconds = base_url(origin), timeout(seconds)
    if section == "home":
        combined = []
        for name in ("music", "video", "podcasts", "artists", "events", "studio"):
            try:
                combined.extend(section_items(name, origin, seconds))
            except (ValueError, RuntimeError, OSError):
                continue
        return combined[:80]
    if section not in SECTIONS:
        raise ValueError(f"unsupported section: {section}")
    path, key = SECTIONS[section]
    payload = fetch(origin + path, seconds)
    rows = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"invalid {section} catalog: expected {key} list")
    result = []
    for group in rows:
        if not isinstance(group, dict):
            continue
        if section == "podcasts":
            for episode in group.get("episodes") or []:
                item = normalize("podcast", episode, group)
                if item:
                    result.append(item)
            continue
        if section == "tv":
            # This endpoint exposes channel item libraries. The SPA creates a local
            # rotating grid from them; it does not return authoritative slot times.
            for program in group.get("items") or []:
                item = normalize("tv_program", program)
                if item:
                    item["channel_id"] = str(group.get("id", ""))
                    item["channel_name"] = clean(group.get("name"))
                    result.append(item)
            continue
        kind = {"music": "music", "video": "video", "radio": "radio"}.get(section)
        if kind:
            item = normalize(kind, group)
            if item:
                if section == "radio":
                    item["type"] = "radio"
                    item["radio_epoch_ms"] = (payload.get("station") or {}).get("epoch_ms")
                    item["server_time_ms"] = payload.get("server_time_ms")
                    item["radio_index"] = len(result)
                    item["radio_current_index"] = payload.get("current_index")
                    item["radio_elapsed_seconds"] = (payload.get("current") or {}).get("elapsed_seconds")
                result.append(item)
            continue
        raw_id = (group.get("collection_id") or group.get("id") or group.get("slug")) if section == "studio" else (group.get("id") or group.get("slug"))
        title = clean(group.get("title") or group.get("name"))
        if raw_id is None or not title:
            continue
        kind = {"artists": "artist", "events": "event", "studio": "studio"}[section]
        item = {"id": f"{kind}:{raw_id}", "type": kind, "source_id": str(raw_id), "title": title,
                "creator": clean(group.get("artist") or group.get("host") or group.get("creator")),
                "duration_seconds": None, "media_url": None}
        for field in ("description", "date", "event_date", "published_date", "category", "cover", "cover_art",
                      "thumbnail", "collection_id", "photo_count", "ticket_url", "slug", "tags", "members", "lineup"):
            if field in group:
                item[field] = group[field]
        result.append(item)
    if section == "events":
        for video in payload.get("videos") or []:
            item = normalize("event_video", video)
            if item:
                result.append(item)
    return result


def all_catalog(origin=None, seconds=10):
    return section_items("music", origin, seconds) + section_items("video", origin, seconds)


def search(query, kind="all", limit=20, origin=None, seconds=10):
    sections = ("music", "video", "podcasts", "artists", "events", "studio") if kind == "all" else (kind,)
    items = [item for section in sections for item in section_items(section, origin, seconds)]
    needle = query.casefold()
    items = [x for x in items if needle in x["title"].casefold() or needle in (x["creator"] or "").casefold()]
    items.sort(key=lambda x: (x["type"], x["title"].casefold(), x["id"]))
    return items[:limit]


def show(media_id, origin=None, seconds=10):
    kind, sep, _ = media_id.partition(":")
    section = {"music": "music", "video": "video", "podcast": "podcasts", "artist": "artists",
               "event": "events", "studio": "studio", "radio": "radio"}.get(kind)
    if not sep or not section:
        raise LookupError("media ID must use a supported type prefix")
    for item in section_items(section, origin, seconds):
        if item["id"] == media_id:
            return item
    raise LookupError(f"unknown media ID: {media_id}")
