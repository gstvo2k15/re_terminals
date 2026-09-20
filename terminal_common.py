"""Audio fallback and reusable rendering helpers for the terminal simulations."""

from functools import lru_cache
import logging
from pathlib import Path

import pygame

logger = logging.getLogger(__name__)


class SilentSound:
    """Keep animation code usable when audio is unavailable."""

    def play(self, loops=0):
        return None

    def set_volume(self, volume):
        pass

    def get_length(self):
        return 0.0


class SilentChannel:
    def play(self, sound, loops=0):
        pass

    def stop(self):
        pass

    def get_busy(self):
        return False


def initialize_pygame():
    """Initialize graphics and fonts; a missing audio device is nonfatal."""
    pygame.display.init()
    pygame.font.init()
    try:
        pygame.mixer.init(44100, -16, 2, 512)
    except pygame.error as exc:
        logger.warning("Audio unavailable; continuing without sound: %s", exc)


def audio_channel(index):
    if pygame.mixer.get_init() is None:
        return SilentChannel()
    return pygame.mixer.Channel(index)


def load_sound(path: Path):
    if pygame.mixer.get_init() is None:
        return SilentSound()
    try:
        return pygame.mixer.Sound(str(path))
    except (pygame.error, OSError) as exc:
        logger.warning("Cannot load sound %s; continuing without it: %s", path, exc)
        return SilentSound()


@lru_cache(maxsize=16)
def _scanline_overlay(size, alpha, step):
    if step <= 0:
        raise ValueError("Scanline step must be positive")
    overlay = pygame.Surface(size, pygame.SRCALPHA)
    width, height = size
    for y in range(0, height, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (width, y))
    return overlay


def draw_scanlines(surface, alpha=18, step=2):
    surface.blit(_scanline_overlay(surface.get_size(), alpha, step), (0, 0))
