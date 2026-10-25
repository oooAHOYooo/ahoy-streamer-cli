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
    typeahead = ""
    typeahead_at = 0.0
    message = "Loading discovery…"
    section = NAV[section_idx][1]
    cache = {}
    stdscr.timeout(200)

    def section_items(name, refresh=False):
        saved = cache.get(name)
        if name == "radio" or refresh or saved is None or time.monotonic() - saved[0] >= 60:
            values = catalog.section_items(name)
            cache[name] = (time.monotonic(), values)
        return [dict(item) for item in cache[name][1]]

    def load(refresh=False):
        nonlocal items, selected, message
        section = NAV[section_idx][1]
        previous_id = items[selected]["id"] if items and selected < len(items) else None
        try:
            if section == "search":
                items = []
                message = "Press / to search the public catalogs"
            elif section == "radio":
                items = section_items("radio", refresh)
                if items:
                    items, elapsed = _radio_now(items)
                    message = f"Station manifest · current item {elapsed}s in; playback starts at track beginning and loops locally"
                else:
                    message = "Radio catalog is empty"
            elif section == "tv":
                items = section_items("tv", refresh)
                message = "Channel libraries only · no authoritative schedule returned by public API"
            elif section == "home":
                items = section_items("home", refresh)
                message = "Explore public catalogs · choose a section at left"
            else:
                items = section_items(section, refresh)
                message = f"{len(items)} items"
            selected = next((i for i, item in enumerate(items) if item["id"] == previous_id),
                            min(selected, max(0, len(items) - 1)))
        except Exception as e:
            items = []
            message = f"Could not load {NAV[section_idx][0]}: {e}"

    def search_now(stdscr, height, width):
        nonlocal items, selected, message, query, section_idx
        try:
            stdscr.timeout(-1)
            curses.echo()
            curses.curs_set(1)
            _line(stdscr, height - 2, 2, "Search AHOY: ", width - 4)
            stdscr.refresh()
            query = stdscr.getstr(height - 2, 15, max(1, width - 18)).decode("utf-8", "replace").strip()
        finally:
            stdscr.timeout(200)
            curses.noecho()
            curses.curs_set(0)
        if not query:
            return
        section_idx = next(i for i, (_, key) in enumerate(NAV) if key == "search")
        found = []
        failures = []
        for name in ("music", "video", "podcasts", "artists", "events", "studio"):
            try:
                found.extend(section_items(name))
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
            result = (session.start_radio(items, selected) if item.get("type") == "radio"
                      else session.start(item, mode="window"))
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
            if getattr(session, "notice", ""):
                message = session.notice
                session.notice = ""
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
            _line(stdscr, 18, 2, "type jump · / search", side - 4)
            _line(stdscr, 19, 2, "Space play/pause · x stop", side - 4)
            _line(stdscr, 20, 2, "Esc clear/quit", side - 4)

            main_x = side + 2
            main_w = max(1, w - main_x - 2)
            header = active.upper() + (f"  ·  {query}" if active == "Search" and query else "")
            if typeahead:
                matches = _typeahead_matches(items, typeahead)
                header += f"  ·  jump: {typeahead}  ({len(matches)})"
            _line(stdscr, 3, main_x, header, main_w, curses.A_BOLD)
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
                    _line(stdscr, h - 7, dx, "Space play · w window video", dw, curses.A_DIM)

            if items and selected < len(items):
                chosen = items[selected]
                _line(stdscr, h - 5, main_x, f"Selected  {chosen['title']} · {chosen['type']}", main_w)
            now = session.current
            player_label = f"NOW PLAYING  {now['title']} · {now.get('creator') or now['type']}" if now else "NOW PLAYING  Nothing yet"
            _line(stdscr, h - 4, 2, f"{getattr(session, 'status', 'Stopped')} · Space selected play/pause · Ctrl-X stop", w - 4)
            _line(stdscr, h - 3, 2, player_label, w - 4, curses.A_BOLD)
            _line(stdscr, h - 2, 2, message, w - 4)
            stdscr.refresh()
            key = stdscr.getch()

            now = time.monotonic()
            if now - typeahead_at > 1.0:
                typeahead = ""
            if 32 <= key <= 126 and (chr(key).isalpha() or (typeahead and key == ord(" "))):
                char = chr(key).casefold()
                candidate = typeahead + char if now - typeahead_at <= 1.0 else char
                matches = _typeahead_matches(items, candidate)
                # Space remains playback; all alphabetic keys build a live jump.
                # q/r/w/x retain their shortcut when no displayed item matches.
                if typeahead or char not in {"q", "r", "w", "x"} or matches:
                    typeahead = candidate
                    typeahead_at = now
                    if matches:
                        selected = matches[0]
                    continue
            if key in (curses.KEY_BACKSPACE, 8, 127) and typeahead:
                typeahead = typeahead[:-1]
                typeahead_at = now
                matches = _typeahead_matches(items, typeahead)
                if matches:
                    selected = matches[0]
            elif key == 27 and typeahead:
                typeahead = ""
            elif key in (ord("q"), 27):
                return
            if key == curses.KEY_UP and items:
                typeahead = ""
                selected = (selected - 1) % len(items)
            elif key == curses.KEY_DOWN and items:
                typeahead = ""
                selected = (selected + 1) % len(items)
            elif key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                section_idx = (section_idx + (1 if key == curses.KEY_RIGHT else -1)) % len(NAV)
                query, detail, selected, typeahead = "", False, 0, ""
                load()
            elif key in map(ord, "1234567890"):
                shortcut = int(chr(key))
                section_idx = 9 if shortcut == 0 else shortcut - 1
                typeahead = ""
                query, detail, selected = "", False, 0
                load()
            elif key in (ord("r"), curses.KEY_F5):
                load(refresh=True)
            elif key == ord("/"):
                search_now(stdscr, h, w)
                detail = False
            elif key in (10, 13, curses.KEY_ENTER) and items:
                detail = not detail
            elif key in (ord("w"), 23) and items:
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
            elif key in (ord("x"), 24):
                was_external = session.external
                session.stop()
                message = "Use the browser/player controls to stop external playback" if was_external else "Playback stopped"
    finally:
        session.stop()


def _typeahead_matches(items, query):
    """Return current-section item indexes matching a title/creator prefix."""
    needle = query.casefold().strip()
    if not needle:
        return list(range(len(items)))
    prefix, word_match = [], []
    for index, item in enumerate(items):
        fields = (item.get("title") or "", item.get("creator") or "")
        if any(field.casefold().startswith(needle) for field in fields):
            prefix.append(index)
        elif any(word.casefold().startswith(needle)
                 for field in fields for word in field.split()):
            word_match.append(index)
    return prefix + word_match


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
