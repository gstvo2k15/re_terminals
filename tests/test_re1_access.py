"""Exercise terminal access through keyboard events without opening a window."""

import os
import sys
import unittest
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re1_lab as terminal


class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addClassCleanup(terminal.pygame.quit)
        terminal.initialize_resources()

    def setUp(self):
        self.app = terminal.App()

    def press(self, key):
        self.app.handle_event(terminal.pygame.event.Event(
            terminal.pygame.KEYDOWN, key=key
        ))

    def type_on_screen(self, text):
        for label in [*text, "ENTER"]:
            for row, keys in enumerate(self.app.keyboard.keys):
                if label in keys:
                    self.app.keyboard.row = row
                    self.app.keyboard.col = keys.index(label)
                    break
            self.press(terminal.pygame.K_RETURN)

    def test_invalid_user_cannot_unlock_with_valid_password(self):
        for password in ("ADA", "MOLE"):
            with self.subTest(password=password):
                self.app = terminal.App()
                self.type_on_screen("BAD")
                self.type_on_screen(password)
                self.assertNotEqual(self.app.state, "desktop")
                self.assertEqual(self.app.unlocked_floors, set())
                self.assertEqual(self.app.state, "login")

    def test_cancel_quit_restores_each_access_screen(self):
        for state in ("login", "password", "denied"):
            with self.subTest(state=state):
                self.app = terminal.App()
                if state == "password":
                    self.type_on_screen("JOHN")
                elif state == "denied":
                    self.type_on_screen("BAD")
                self.press(terminal.pygame.K_ESCAPE)
                self.press(terminal.pygame.K_DOWN)
                self.press(terminal.pygame.K_RETURN)
                self.assertEqual(self.app.state, state)
                self.assertEqual(self.app.unlocked_floors, set())

    def test_valid_login_retains_game_permissions(self):
        for password in ("ADA", "MOLE"):
            with self.subTest(password=password):
                self.app = terminal.App()
                self.type_on_screen("JOHN")
                self.type_on_screen(password)
                self.assertEqual(self.app.state, "desktop")
                self.assertTrue(self.app.unlocked_floors <= {"B2", "B3"})
                self.assertEqual(len(self.app.unlocked_floors),
                                 1 if password == "ADA" else 2)

    def test_valid_user_can_retry_password(self):
        self.type_on_screen("JOHN")
        self.type_on_screen("BAD")
        self.assertEqual(self.app.state, "denied")
        self.type_on_screen("MOLE")
        self.assertEqual(self.app.state, "desktop")

    def test_cancel_quit_after_login_returns_to_floor(self):
        self.type_on_screen("JOHN")
        self.type_on_screen("MOLE")
        self.app.update(1.0)
        self.press(terminal.pygame.K_ESCAPE)
        self.press(terminal.pygame.K_DOWN)
        self.press(terminal.pygame.K_RETURN)
        self.assertEqual(self.app.state, "floor")
        self.assertEqual(self.app.unlocked_floors, {"B2", "B3"})

    def test_return_to_login_clears_previous_permissions(self):
        self.type_on_screen("JOHN")
        self.type_on_screen("MOLE")
        self.app.set_state("login")
        self.assertEqual(self.app.unlocked_floors, set())


if __name__ == "__main__":
    unittest.main()
