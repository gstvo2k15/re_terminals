"""Regression checks for startup, shutdown and audio-driven transitions."""

import importlib
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MODULES = ("re1_lab", "re2_guest", "re2_skycard", "re3_notice", "re3_safsprin")


class RuntimeTests(unittest.TestCase):
    def test_startup_and_runtime_failures_propagate_and_release_resources(self):
        for name in MODULES:
            module = importlib.import_module(name)
            for target in ("load_image", "App.run"):
                with self.subTest(module=name, failure=target):
                    with patch(f"{name}.{target}", side_effect=RuntimeError("test failure")):
                        with self.assertRaisesRegex(RuntimeError, "test failure"):
                            module.main()
                    self.assertFalse(module.pygame.display.get_init())
                    self.assertFalse(module.pygame.font.get_init())
                    self.assertIsNone(module.pygame.mixer.get_init())

    def test_all_terminals_render_and_close_without_audio(self):
        import terminal_common

        for name in MODULES:
            with self.subTest(module=name):
                module = importlib.import_module(name)
                module.pygame.quit()
                self.addCleanup(module.pygame.quit)
                with patch.object(module.pygame.mixer, "init", side_effect=module.pygame.error("no device")):
                    with self.assertLogs(terminal_common.logger, level="WARNING"):
                        module.initialize_resources()
                app = module.App()
                app.render()
                if name == "re1_lab":
                    for value, attr in (("JOHN", "login_text"), ("MOLE", "password_text")):
                        setattr(app, attr, value)
                        app.keyboard.row, app.keyboard.col = 2, 7
                        app.submit_key()
                        app.render()
                    app.update(1.0)
                    app.render()
                    app.handle_event(module.pygame.event.Event(
                        module.pygame.KEYDOWN, key=module.pygame.K_RETURN
                    ))
                    for _ in range(4):
                        app.update(1.5)
                        app.render()
                    self.assertEqual(app.state, "unlocked")
                else:
                    entry = {"re2_guest": "name_entry", "re3_safsprin": "password_entry",
                             "re2_skycard": "question", "re3_notice": "done"}[name]
                    self.advance_to(app, entry)
                    if name == "re2_guest":
                        app.input_text = "GUEST"
                        app.submit_username()
                    elif name == "re3_safsprin":
                        app.input_text = "SAFSPRIN"
                        app.submit_password()
                    elif name == "re2_skycard":
                        app.handle_event(module.pygame.event.Event(
                            module.pygame.KEYDOWN, key=module.pygame.K_RETURN
                        ))
                    self.advance_to(app, "done")
                app.handle_event(module.pygame.event.Event(module.pygame.QUIT))
                self.assertFalse(app.running)

    def advance_to(self, app, expected):
        for _ in range(2000):
            previous = app.state
            if previous == expected:
                app.render()
                return
            app.update(0.1)
            if app.state != previous:
                app.render()
        self.fail(f"Expected {expected}; stuck in {app.state}")

    def test_missing_or_invalid_sound_is_nonfatal(self):
        import terminal_common

        terminal_common.initialize_pygame()
        self.addCleanup(terminal_common.pygame.quit)
        for filename in ("missing-sound.mp3", "README.md"):
            with self.subTest(filename=filename):
                with self.assertLogs(terminal_common.logger, level="WARNING"):
                    sound = terminal_common.load_sound(ROOT / filename)
                self.assertIsInstance(sound, terminal_common.SilentSound)

    def test_skycard_closing_remains_responsive(self):
        module = importlib.import_module("re2_skycard")
        self.addCleanup(module.pygame.quit)
        module.initialize_resources()
        app = module.App()
        app.skip_typing_to_question()
        app.selected = 1
        with patch.object(module.pygame.time, "delay") as delay:
            app.handle_event(module.pygame.event.Event(
                module.pygame.KEYDOWN, key=module.pygame.K_RETURN
            ))
            delay.assert_not_called()
        self.assertTrue(app.running)
        app.render()
        app.handle_event(module.pygame.event.Event(module.pygame.QUIT))
        self.assertFalse(app.running)

    def test_guest_backspace_is_reachable_with_arrow_keys(self):
        module = importlib.import_module("re2_guest")
        self.addCleanup(module.pygame.quit)
        module.initialize_resources()
        app = module.App()
        app.set_state("name_entry")
        app.input_text = "GUEST"
        for _ in range(9):
            app.handle_event(module.pygame.event.Event(
                module.pygame.KEYDOWN, key=module.pygame.K_RIGHT
            ))
        app.handle_event(module.pygame.event.Event(
            module.pygame.KEYDOWN, key=module.pygame.K_RETURN
        ))
        self.assertEqual(app.input_text, "GUES")

    def test_imports_do_not_initialize_pygame(self):
        for name in MODULES:
            with self.subTest(module=name):
                result = subprocess.run(
                    [sys.executable, "-B", "-c",
                     f"import {name}; import pygame; "
                     "assert not pygame.get_init(); "
                     "assert not pygame.display.get_init(); "
                     "assert pygame.mixer.get_init() is None"],
                    cwd=ROOT, capture_output=True, text=True, timeout=30,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_submission_completes_when_sound_finishes_before_first_update(self):
        for name, entry, value, submit, expected in (
            ("re2_guest", "name_entry", "GUEST", "submit_username", "typing_result"),
            ("re3_safsprin", "password_entry", "SAFSPRIN", "submit_password", "typing_success"),
        ):
            with self.subTest(module=name):
                module = importlib.import_module(name)
                self.addCleanup(module.pygame.quit)
                module.initialize_resources()
                app = module.App()
                app.set_state(entry)
                app.input_text = value
                with patch.object(module, "finish_channel") as channel:
                    channel.get_busy.return_value = False
                    getattr(app, submit)()
                    app.update(0.1)
                self.assertEqual(app.state, expected)


if __name__ == "__main__":
    unittest.main()
