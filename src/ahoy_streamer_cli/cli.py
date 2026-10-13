import argparse
import json
import platform
import sys

from . import __version__, catalog, player, tui
from .config import base_url, timeout
from .output import emit


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse has already written its usage to stderr; keep the stable failure envelope.
        if "--json" in sys.argv:
            emit(None, ok=False, code="USAGE", message=message)
            raise SystemExit(2)
        super().error(message)


def parser():
    p = Parser(prog="ahoy", description="AHOY Streamer terminal listening room")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command")
    for name in ("search", "show", "doctor"):
        q = sub.add_parser(name)
        q.add_argument("--json", action="store_true")
        q.add_argument("--base-url")
        q.add_argument("--timeout", type=float, default=10)
        if name == "search":
            q.add_argument("query")
            q.add_argument("--type", choices=("music", "video", "podcasts", "artists", "events", "studio", "all"), default="all")
            q.add_argument("--limit", type=int, default=20)
        elif name == "show":
            q.add_argument("media_id")
    q = sub.add_parser("play")
    q.add_argument("media_id")
    q.add_argument("--base-url")
    q.add_argument("--timeout", type=float, default=10)
    q = sub.add_parser("watch")
    q.add_argument("media_id")
    q.add_argument("--video", choices=("ascii", "window"), default="ascii")
    q.add_argument("--base-url")
    q.add_argument("--timeout", type=float, default=10)
    return p


def fail(message, code="ERROR", exit_code=3, as_json=False):
    if as_json:
        emit(None, ok=False, code=code, message=str(message))
    else:
        print(f"ahoy: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def main():
    p = parser()
    if len(sys.argv) == 1:
        if sys.stdin.isatty() and sys.stdout.isatty():
            return tui.main()
        p.print_help()
        return 0
    args = p.parse_args()
    if not args.command:
        p.print_help()
        return 0
    as_json = getattr(args, "json", False)
    try:
        if hasattr(args, "base_url"):
            args.base_url = base_url(args.base_url)
            args.timeout = timeout(args.timeout)
        if args.command == "doctor":
            path = player.mpv_path()
            data = {"python": platform.python_version(), "platform": platform.platform(), "mpv_available": bool(path), "mpv_path": path}
            if as_json:
                emit(data)
            else:
                print(json.dumps(data, indent=2))
            return 0 if path else 5
        if args.command == "search":
            if not 1 <= args.limit <= 100:
                raise ValueError("limit must be between 1 and 100")
            items = catalog.search(args.query, args.type, args.limit, args.base_url, args.timeout)
            if as_json:
                emit({"items": items, "count": len(items)})
            else:
                for item in items:
                    print(f"{item['id']}  {item['title']} — {item['creator'] or 'AHOY'}")
            return 0
        if args.command == "show":
            item = catalog.show(args.media_id, args.base_url, args.timeout)
            if as_json:
                emit(item)
            else:
                print(json.dumps(item, indent=2, ensure_ascii=False))
            return 0
        kind, sep, _ = args.media_id.partition(":")
        expected = {"video"} if args.command == "watch" else {"music", "podcast", "radio"}
        if not sep or kind not in expected:
            fail(f"{args.command} expects one of {', '.join(sorted(expected))}:ID", "USAGE", 2)
        item = catalog.show(args.media_id, args.base_url, args.timeout)
        player.play(item, getattr(args, "video", "ascii"), require_tty=args.command == "watch")
        return 0
    except LookupError as e:
        fail(e, "NOT_FOUND", 4, as_json)
    except FileNotFoundError as e:
        fail(e, "MPV_MISSING", 5, as_json)
    except (ValueError, TypeError) as e:
        fail(e, "VALIDATION", 2, as_json)
    except (OSError, RuntimeError) as e:
        if args.command in {"play", "watch"}:
            code = "RENDER_UNAVAILABLE" if isinstance(e, OSError) else "PLAYER_FAILED"
            fail(e, code, 5 if isinstance(e, OSError) else 6, as_json)
        fail(e, "NETWORK", 3, as_json)
    except Exception as e:
        fail(e, "UPSTREAM", 3, as_json)


if __name__ == "__main__":
    main()
