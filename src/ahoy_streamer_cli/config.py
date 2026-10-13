import os
from urllib.parse import urlsplit

DEFAULT_BASE_URL = "https://app.ahoy.ooo"


def base_url(value=None):
    value = value or os.environ.get("AHOY_BASE_URL") or DEFAULT_BASE_URL
    p = urlsplit(value)
    local = p.hostname in {"localhost", "127.0.0.1", "::1"}
    if p.scheme != "https" and not (p.scheme == "http" and local):
        raise ValueError("base URL must use HTTPS (HTTP is allowed for localhost)")
    if not p.hostname or p.username or p.password or p.query or p.fragment or p.path not in ("", "/"):
        raise ValueError("base URL must be an origin without credentials, query, or fragment")
    return value.rstrip("/")


def timeout(value):
    value = float(value)
    if not 1 <= value <= 60:
        raise ValueError("timeout must be between 1 and 60 seconds")
    return value
