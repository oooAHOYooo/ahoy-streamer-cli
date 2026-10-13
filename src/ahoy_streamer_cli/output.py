import json
import sys


def emit(data, *, ok=True, code=None, message=None):
    result = {"schema_version": 1, "ok": ok}
    if ok:
        result["data"] = data
    else:
        result["error"] = {"code": code or "ERROR", "message": message or "Request failed"}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
