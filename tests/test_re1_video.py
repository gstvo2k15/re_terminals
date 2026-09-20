"""Exercise video ownership on normal exit, skip and decoder failures."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re1_lab as terminal


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(terminal.pygame.quit)
        terminal.initialize_resources()

    def test_capture_released_when_audio_player_creation_fails(self):
        with patch.object(terminal.cv2, "VideoCapture") as capture:
            with patch.object(terminal, "MediaPlayer", side_effect=RuntimeError("audio failure")):
                with self.assertRaisesRegex(RuntimeError, "audio failure"):
                    terminal.play_intro_video(terminal.VIDEO_INTRO)
            capture.return_value.release.assert_called_once()

    def test_decode_failure_releases_both_players(self):
        with patch.object(terminal.cv2, "VideoCapture") as capture:
            capture.return_value.get.return_value = 30.0
            capture.return_value.read.side_effect = RuntimeError("decode failure")
            with patch.object(terminal, "MediaPlayer") as player:
                with patch.object(terminal.pygame.event, "get", return_value=[]):
                    with self.assertRaisesRegex(RuntimeError, "decode failure"):
                        terminal.play_intro_video(terminal.VIDEO_INTRO)
                player.return_value.close_player.assert_called_once()
            capture.return_value.release.assert_called_once()

    def test_skip_does_not_decode_an_extra_frame(self):
        event = terminal.pygame.event.Event(terminal.pygame.KEYDOWN, key=terminal.pygame.K_SPACE)
        with patch.object(terminal.cv2, "VideoCapture") as capture:
            capture.return_value.get.return_value = float("nan")
            with patch.object(terminal, "MediaPlayer") as player:
                with patch.object(terminal.pygame.event, "get", return_value=[event]):
                    self.assertTrue(terminal.play_intro_video(terminal.VIDEO_INTRO))
                player.return_value.close_player.assert_called_once()
            capture.return_value.read.assert_not_called()
            capture.return_value.release.assert_called_once()

    def test_real_video_frame_renders_and_quit_closes_player(self):
        quit_event = terminal.pygame.event.Event(terminal.pygame.QUIT)
        with patch.object(terminal, "MediaPlayer") as player:
            with patch.object(terminal.pygame.event, "get", side_effect=[[], [quit_event]]):
                self.assertFalse(terminal.play_intro_video(terminal.VIDEO_INTRO))
            player.return_value.get_frame.assert_called_once()
            player.return_value.close_player.assert_called_once()


if __name__ == "__main__":
    unittest.main()
