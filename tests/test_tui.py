import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "src")
from ahoy_streamer_cli import tui


class Screen:
    def __init__(self, keys):
        self.keys = iter(keys)

    def erase(self):
        pass

    def getmaxyx(self):
        return (48, 111)

    def addnstr(self, *args):
        pass

    def refresh(self):
        pass

    def getch(self):
        return next(self.keys)


class Session:
    instance = None

    def __init__(self):
        self.current = None
        self.external = False
        self.started = []
        self.toggles = 0
        self.stopped = False
        Session.instance = self

    def refresh_state(self):
        pass

    def start(self, item, mode="window"):
        self.current = item
        self.started.append(item)
        return "background"

    def toggle_pause(self):
        self.toggles += 1
        return True

    def stop(self):
        self.stopped = True


class TuiPlaybackTests(unittest.TestCase):
    def test_space_starts_selected_audio_then_toggles_pause(self):
        item = {"id": "music:1", "type": "music", "title": "Sample", "creator": "Artist"}
        screen = Screen((ord(" "), ord(" "), ord("q")))
        with patch.object(tui.curses, "curs_set"), \
             patch.object(tui.catalog, "section_items", return_value=[item]), \
             patch.object(tui.player, "PlayerSession", Session):
            tui.run(screen)

        self.assertEqual(Session.instance.started, [item])
        self.assertEqual(Session.instance.toggles, 1)
        self.assertTrue(Session.instance.stopped)


if __name__ == "__main__":
    unittest.main()
