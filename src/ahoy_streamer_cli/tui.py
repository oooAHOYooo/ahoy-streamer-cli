import curses
import re
import time

from . import catalog, player

NAV = (("Home", "home"), ("Music", "music"), ("Videos", "video"), ("Podcasts", "podcasts"),
       ("Artists", "artists"), ("Events", "events"), ("Studio", "studio"), ("Radio", "radio"),
       ("AHOY TV", "tv"), ("Search", "search"))
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _line(stdscr, y, x, text, width, attr=0):
    if width > 0:
        try:
            safe = ANSI.sub("", str(text))
            safe = "".join(ch if ch >= " " and ch != "\x7f" else " " for ch in safe)
            stdscr.addnstr(y, x, safe, width, attr)
        except curses.error:
            pass


def run(stdscr):
    curses.curs_set(0)
    session = player.PlayerSession()
    section_idx, selected, detail = 0, 0, False
    items, query = [], ""
    message = "Loading discovery…"
    section = NAV[section_idx][1]

    def load():
        nonlocal items, selected, message
        section = NAV[section_idx][1]
        try:
            if section == "search":
                items = []
                message = "Press / to search the public catalogs"
            elif section == "radio":
                items = catalog.section_items("radio")
                if items:
                    items, elapsed = _radio_now(items)
                    message = f"Live station · current item started {elapsed}s ago; station order/epoch from API"
                else:
                    message = "Radio catalog is empty"
            elif section == "tv":
                items = catalog.section_items("tv")
                message = "Channel libraries only · no authoritative schedule returned by public API"
            elif section == "home":
                items = catalog.section_items("home")
                message = "Explore public catalogs · choose a section at left"
            else:
                items = catalog.section_items(section)
                message = f"{len(items)} items"
            selected = min(selected, max(0, len(items) - 1))
        except Exception as e:
            items = []
            message = f"Could not load {NAV[section_idx][0]}: {e}"

    def search_now(stdscr, height, width):
        nonlocal items, selected, message, query, section_idx
        try:
            curses.echo()
            curses.curs_set(1)
            _line(stdscr, height - 2, 2, "Search AHOY: ", width - 4)
            stdscr.refresh()
            query = stdscr.getstr(height - 2, 15, max(1, width - 18)).decode("utf-8", "replace").strip()
        finally:
            curses.noecho()
            curses.curs_set(0)
        if not query:
            return
        section_idx = next(i for i, (_, key) in enumerate(NAV) if key == "search")
        found = []
        failures = []
        for name in ("music", "video", "podcasts", "artists", "events", "studio"):
            try:
                found.extend(catalog.section_items(name))
            except Exception as e:
                failures.append(name)
        needle = query.casefold()
        items = [item for item in found if needle in item["title"].casefold()
                 or needle in (item.get("creator") or "").casefold()]
        items.sort(key=lambda item: (item["type"], item["title"].casefold(), item["id"]))
        selected = 0
        message = f"{len(items)} matches for “{query}”" + (f" · unavailable: {', '.join(failures)}" if failures else "")

    def play_selected(stdscr, force_window=False):
        nonlocal message
        if not items:
            return
        item = items[selected]
        is_video = item.get("type") in {"video", "tv_program", "event_video"}
        if is_video and not force_window:
            try:
                curses.def_prog_mode()
                curses.endwin()
                playback = player.play(item, "ascii", require_tty=True)
                curses.reset_prog_mode()
                stdscr.refresh()
                message = ("ASCII video ended · Space pauses/resumes in the player · q returns"
                           if playback == "ascii" else
                           "ASCII decoding unavailable for this stream · opened it in your browser")
            except Exception as e:
                try:
                    curses.reset_prog_mode()
                    stdscr.refresh()
                except curses.error:
                    pass
                message = str(e)
            return
        try:
            result = session.start(item, mode="window")
            if result == "background":
                message = "Playing · Space pauses/resumes, x stops"
            elif session.external:
                message = "Opened outside the TUI · use the browser/player controls"
            else:
                message = "Playback started"
        except Exception as e:
            message = str(e)

    load()
    try:
        while True:
            session.refresh_state()
            stdscr.erase()
            h, w = stdscr.getmaxyx()
            side = min(21, max(14, w // 4))
            _line(stdscr, 0, 2, "AHOY STREAMER", w - 4, curses.A_BOLD)
            _line(stdscr, 1, 2, "A terminal for independent music, shows and radio", w - 4)
            _line(stdscr, 3, 2, "LIBRARY", side - 4, curses.A_DIM)
            active = NAV[section_idx][0]
            for row, (label, key) in enumerate(NAV):
                attr = curses.A_REVERSE if key == NAV[section_idx][1] else curses.A_NORMAL
                shortcut = str((row + 1) % 10)
                _line(stdscr, 4 + row, 2, f"{shortcut}  {label}", side - 4, attr)
            _line(stdscr, 15, 2, "──────────────────", side - 4, curses.A_DIM)
            _line(stdscr, 16, 2, "↑/↓ browse", side - 4)
            _line(stdscr, 17, 2, "Enter details", side - 4)
            _line(stdscr, 18, 2, "p play · / search", side - 4)
            _line(stdscr, 19, 2, "Space play/pause · x stop", side - 4)
            _line(stdscr, 20, 2, "q quit", side - 4)

            main_x = side + 2
            main_w = max(1, w - main_x - 2)
            _line(stdscr, 3, main_x, active.upper() + (f"  ·  {query}" if active == "Search" and query else ""), main_w, curses.A_BOLD)
            list_w = max(1, min(56, main_w // 2 if main_w > 88 else main_w))
            visible = max(0, h - 10)
            start = max(0, selected - visible + 1)
            for offset, item in enumerate(items[start:start + visible]):
                idx = start + offset
                creator = f" — {item['creator']}" if item.get("creator") else ""
                label = ("› " if idx == selected else "  ") + item["title"] + creator
                attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                _line(stdscr, 5 + offset, main_x, label, list_w - 2, attr)

            if detail and items:
                chosen = items[selected]
                dx = main_x + list_w
                dw = w - dx - 2
                if dw >= 22:
                    _line(stdscr, 4, dx, "NOW EXPLORING", dw, curses.A_BOLD)
                    _line(stdscr, 6, dx, chosen["title"], dw, curses.A_BOLD)
                    _line(stdscr, 7, dx, chosen.get("creator") or chosen.get("channel_name") or chosen["type"], dw)
                    _line(stdscr, 9, dx, chosen.get("description") or "No description in public catalog.", dw)
                    _line(stdscr, 12, dx, f"ID  {chosen['id']}", dw)
                    duration = chosen.get("duration_seconds")
                    _line(stdscr, 13, dx, f"Length  {duration}s" if duration else "Length  not provided", dw)
                    for n, field in enumerate(("date", "event_date", "category", "photo_count", "channel_name"), start=15):
                        if chosen.get(field) is not None:
                            _line(stdscr, n, dx, f"{field.replace('_', ' ').title()}  {chosen[field]}", dw)
                    _line(stdscr, h - 7, dx, "p play · w window video", dw, curses.A_DIM)

            if items and selected < len(items):
                chosen = items[selected]
                _line(stdscr, h - 5, main_x, f"Selected  {chosen['title']} · {chosen['type']}", main_w)
            now = session.current
            player_label = f"NOW PLAYING  {now['title']} · {now.get('creator') or now['type']}" if now else "NOW PLAYING  Nothing yet"
            _line(stdscr, h - 3, 2, player_label, w - 4, curses.A_BOLD)
            _line(stdscr, h - 2, 2, message, w - 4)
            stdscr.refresh()
            key = stdscr.getch()

            if key in (ord("q"), 27):
                return
            if key in (curses.KEY_UP, ord("k")) and items:
                selected = (selected - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord("j")) and items:
                selected = (selected + 1) % len(items)
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                section_idx = (section_idx + (1 if key == curses.KEY_RIGHT else -1)) % len(NAV)
                query, detail, selected = "", False, 0
                load()
            elif key in map(ord, "1234567890"):
                section_idx = (int(chr(key)) % 10)
                query, detail, selected = "", False, 0
                load()
            elif key == ord("r"):
                load()
            elif key == ord("/"):
                search_now(stdscr, h, w)
                detail = False
            elif key in (10, 13, curses.KEY_ENTER) and items:
                detail = not detail
            elif key == ord("p") and items:
                play_selected(stdscr)
            elif key == ord("w") and items:
                item = items[selected]
                if item["type"] in {"video", "tv_program", "event_video"}:
                    play_selected(stdscr, force_window=True)
            elif key == ord(" ") and items:
                chosen = items[selected]
                if session.current and session.current.get("id") == chosen.get("id"):
                    if session.external:
                        message = "Playback is outside the TUI · use its controls"
                    else:
                        message = "Playback paused/resumed" if session.toggle_pause() else "This player has no pause control"
                elif session.current and session.external:
                    message = "Close the external player before starting another item"
                else:
                    # Space on a different selection means switch playback. Stop the old
                    # owned audio session before handing the terminal to ASCII video.
                    session.stop()
                    play_selected(stdscr)
            elif key == ord("x"):
                was_external = session.external
                session.stop()
                message = "Use the browser/player controls to stop external playback" if was_external else "Playback stopped"
    finally:
        session.stop()


def _radio_now(items):
    if not items:
        return items, 0
    ordered = sorted(items, key=lambda item: item["radio_index"])
    current_index = ordered[0].get("radio_current_index")
    if isinstance(current_index, int) and 0 <= current_index < len(ordered):
        item = ordered[current_index]
        elapsed = int(item.get("radio_elapsed_seconds") or 0)
        item["elapsed_seconds"] = elapsed
        return ordered[current_index:] + ordered[:current_index], elapsed
    total = sum(max(1, item.get("duration_seconds") or 180) for item in ordered)
    epoch = ordered[0].get("radio_epoch_ms") or 0
    server_ms = ordered[0].get("server_time_ms") or int(time.time() * 1000)
    elapsed_station = ((server_ms - epoch) / 1000) % total if epoch else 0
    cursor = 0
    for item in ordered:
        duration = max(1, item.get("duration_seconds") or 180)
        if elapsed_station < cursor + duration:
            item["elapsed_seconds"] = int(elapsed_station - cursor)
            start = ordered.index(item)
            return ordered[start:] + ordered[:start], item["elapsed_seconds"]
        cursor += duration
    return ordered, 0


def main():
    curses.wrapper(run)
