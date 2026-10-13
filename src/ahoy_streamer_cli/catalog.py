import json
import re
import urllib.error
import urllib.request

from .config import base_url, timeout

MAX_BODY = 5 * 1024 * 1024
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")


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


def normalize(kind, raw):
    source_id = raw.get("track_id") or raw.get("id") if kind == "music" else raw.get("show_id") or raw.get("id")
    title = clean(raw.get("title"))
    if source_id is None or not str(source_id).strip() or not title or not title.strip():
        return None
    duration = raw.get("duration_seconds")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration < 0:
        duration = None
    media_url = clean(raw.get("audio_url")) if kind == "music" else clean(raw.get("video_url") or raw.get("mp4_link") or raw.get("trailer_url"))
    creator = clean(raw.get("artist")) if kind == "music" else clean(raw.get("host") or raw.get("artist"))
    return {"id": f"{kind}:{source_id}", "type": kind, "source_id": str(source_id), "title": title.strip(),
            "creator": creator, "duration_seconds": duration, "media_url": media_url}


def catalog(kind, origin=None, seconds=10):
    origin, seconds = base_url(origin), timeout(seconds)
    path, key = ("/api/music", "tracks") if kind == "music" else ("/api/shows", "shows")
    data = fetch(origin + path, seconds)
    entries = data.get(key) if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError(f"invalid {kind} catalog: expected {key} list")
    result, seen = [], {}
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        item = normalize(kind, raw)
        if item is None:
            continue
        if item["id"] in seen and seen[item["id"]] != item:
            raise ValueError(f"conflicting duplicate ID {item['id']}")
        if item["id"] not in seen:
            seen[item["id"]] = item
            result.append(item)
    return result


def all_catalog(origin=None, seconds=10):
    return catalog("music", origin, seconds) + catalog("video", origin, seconds)


def search(query, kind="all", limit=20, origin=None, seconds=10):
    items = all_catalog(origin, seconds) if kind == "all" else catalog(kind, origin, seconds)
    needle = query.casefold()
    items = [x for x in items if needle in x["title"].casefold() or needle in (x["creator"] or "").casefold()]
    items.sort(key=lambda x: (x["type"], x["title"].casefold(), x["id"]))
    return items[:limit]


def show(media_id, origin=None, seconds=10):
    kind, sep, _ = media_id.partition(":")
    if not sep or kind not in {"music", "video"}:
        raise LookupError("media ID must be music:ID or video:ID")
    for item in catalog(kind, origin, seconds):
        if item["id"] == media_id:
            return item
    raise LookupError(f"unknown media ID: {media_id}")
