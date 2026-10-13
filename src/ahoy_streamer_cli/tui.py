import curses

from . import catalog, player


def run(stdscr):
    curses.curs_set(0)
    section, index, query = "music", 0, ""
    message = "Loading catalog…"
    items = []

    def load():
        nonlocal items, index, message
        try:
            items = catalog.catalog(section)
            index = min(index, max(0, len(items) - 1))
            message = f"{len(items)} items · / search"
        except Exception as e:
            items, message = [], str(e)

    load()
    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(0, 0, " AHOY STREAMER  ·  terminal listening room "[:w-1], curses.A_BOLD)
        stdscr.addstr(2, 2, "[ Music ]" if section == "music" else "  Music  ", curses.A_REVERSE if section == "music" else 0)
        stdscr.addstr(2, 14, "[ Videos ]" if section == "video" else "  Videos  ", curses.A_REVERSE if section == "video" else 0)
        if query:
            stdscr.addstr(3, 2, f"Search: {query}"[:w-3])
        for i, item in enumerate(items[:max(0, h-9)]):
            title = f"{item['title']}  —  {item['creator'] or 'AHOY'}"
            stdscr.addstr(5+i, 2, ("› " if i == index else "  ") + title[:max(1,w-5)], curses.A_REVERSE if i == index else 0)
        if items:
            selected = items[index]
            stdscr.addstr(h-4, 2, f"Selected: {selected['title']} · {selected['type']}"[:w-3])
        stdscr.addstr(h-3, 2, message[:max(1,w-3)])
        stdscr.addstr(h-2, 2, "←/→ category   ↑/↓ or j/k select   Enter play   / search   r refresh   q quit"[:w-3])
        stdscr.refresh()
        key = stdscr.getch()
        if key in (ord("q"), 27):
            return
        if key in (curses.KEY_LEFT, curses.KEY_RIGHT, 9):
            section = "video" if section == "music" else "music"
            query = ""
            load()
        elif key in (curses.KEY_UP, ord("k")) and items:
            index = (index - 1) % len(items)
        elif key in (curses.KEY_DOWN, ord("j")) and items:
            index = (index + 1) % len(items)
        elif key == ord("r"):
            load()
        elif key == ord("/"):
            curses.echo()
            stdscr.addstr(h-1, 2, "Search: ")
            query = stdscr.getstr(h-1, 10, max(1,w-12)).decode("utf-8", "replace")
            curses.noecho()
            try:
                items = catalog.search(query, section)
                index, message = 0, f"{len(items)} matches"
            except Exception as e:
                message = str(e)
        elif key in (10, 13, curses.KEY_ENTER) and items:
            try:
                player.play(items[index], "ascii", require_tty=True)
                message = "Playback finished"
            except Exception as e:
                message = str(e)


def main():
    curses.wrapper(run)
