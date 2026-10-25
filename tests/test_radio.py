import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, "src")
from ahoy_streamer_cli import player, tui
from test_tui import Screen, Session


class Audio:
    def __init__(self, item):
        self.closed = self.paused = False

    def refresh_state(self):
        pass

    def toggle_pause(self):
        self.paused = not self.paused
        return True

    def stop(self):
        self.closed = True


class RadioTests(unittest.TestCase):
    def setUp(self):
        self.items = [dict(id=f"radio:{i}", type="radio", title=f"Track {i}",
                           media_url=f"https://example.test/{i}.mp3") for i in range(2)]

    def test_radio_advances_wraps_and_stop_cancels(self):
        with patch.object(player, "audio_backend_ready", return_value=True), \
             patch.object(player, "AudioSession", Audio):
            session = player.PlayerSession()
            session.start_radio(self.items)
            self.assertEqual(session.status, "Playing")
            session.toggle_pause()
            session.refresh_state()
            self.assertEqual(session.status, "Paused")
            self.assertEqual(session.current, self.items[0])
            session.toggle_pause()
            for expected in (1, 0):
                session.audio.closed = True
                session.refresh_state()
                self.assertEqual(session.current, self.items[expected])
            session.stop()
            session.refresh_state()
            self.assertIsNone(session.current)
            self.assertEqual(session.radio_items, [])

    def test_failed_rollover_stops_without_retry_loop(self):
        with patch.object(player, "audio_backend_ready", return_value=True), \
             patch.object(player, "AudioSession", side_effect=[Audio({}), OSError("offline")]) as audio:
            session = player.PlayerSession()
            session.start_radio(self.items)
            session.audio.closed = True
            session.refresh_state()
            session.refresh_state()
            self.assertIsNone(session.current)
            self.assertIn("offline", session.notice)
            self.assertEqual(audio.call_count, 2)

    def test_external_radio_has_no_automatic_rollover(self):
        with patch.object(player, "audio_backend_ready", return_value=False), \
             patch.object(player, "play"):
            session = player.PlayerSession()
            session.start_radio(self.items)
            self.assertEqual(session.radio_items, [])
            self.assertIn("External", session.status)

    def test_idle_tui_rolls_radio_while_browsing(self):
        class RadioSession(player.PlayerSession):
            instance = None

            def __init__(self):
                super().__init__()
                self.history = []
                RadioSession.instance = self

            def refresh_state(self):
                if self.audio:
                    self.audio.closed = True
                super().refresh_state()
                if self.current:
                    self.history.append(self.current["id"])

        items = [dict(item, radio_index=i) for i, item in enumerate(self.items)]
        screen = Screen((ord("8"), ord(" "), ord("2"), -1, 27))
        with patch.object(tui.curses, "curs_set"), \
             patch.object(tui.catalog, "section_items", side_effect=lambda section: items if section == "radio" else []), \
             patch.object(tui.player, "PlayerSession", RadioSession), \
             patch.object(player, "AudioSession", Audio), \
             patch.object(player, "audio_backend_ready", return_value=True):
            tui.run(screen)
        self.assertEqual(RadioSession.instance.history[:2], ["radio:1", "radio:0"])
        self.assertEqual(screen.interval, 200)
        self.assertTrue(any("Playing ·" in line for line in screen.lines))

    def test_section_cache_and_explicit_refresh(self):
        screen = Screen((ord("2"), ord("3"), ord("2"), tui.curses.KEY_F5, 27))
        with patch.object(tui.curses, "curs_set"), \
             patch.object(tui.catalog, "section_items", return_value=[]) as fetch, \
             patch.object(tui.player, "PlayerSession", Session):
            tui.run(screen)
        self.assertEqual([call.args[0] for call in fetch.call_args_list],
                         ["home", "music", "video", "music"])
