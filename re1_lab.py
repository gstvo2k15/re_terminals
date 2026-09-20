import time
import math
import random
from pathlib import Path

import cv2
import pygame
from ffpyplayer.player import MediaPlayer

from terminal_common import audio_channel, draw_scanlines, initialize_pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

VIDEO_INTRO = BASE_DIR / "RE1_umbrella_intro.mp4"

FRAME_LOGIN = "RE1_oldPc_8.png"
FRAME_PASSWORD = "RE1_oldPc_9.png"
FRAME_DESKTOP = "RE1_oldPc_10.png"
FRAME_FLOOR = "RE1_oldPc_11.png"
FRAME_ACCESSING = "RE1_oldPc_12.png"
FRAME_MAP_B2 = "RE1_oldPc_13b.png"
FRAME_MAP_B3 = "RE1_oldPc_13.png"
FRAME_UNLOCKED_B2 = "RE1_oldPc_13c.png"
FRAME_UNLOCKED = "RE1_oldPc_14.png"
FRAME_DENIED = "RE1_oldPc_15.png"
FRAME_QUIT = "RE1_oldPc_16.png"

VALID_LOGIN = "JOHN"
PASSWORD_ADA = "ADA"
PASSWORD_MOLE = "MOLE"


WHITE = (245, 245, 245)
BLACK = (0, 0, 0)
BLUE = (42, 54, 205)
BLUE_DARK = (20, 30, 135)
LAVENDER = (176, 178, 230)
GREEN = (0, 135, 75)
SHADOW = (30, 30, 70)


def load_image(name: str) -> pygame.Surface:
    path = BASE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing image: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))


def beep(freq: int = 900, duration_ms: int = 45, volume: float = 0.35) -> None:
    if pygame.mixer.get_init() is None:
        return
    sample_rate = 44100
    samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray()

    for i in range(samples):
        t = i / sample_rate
        value = int(32767 * volume * math.sin(2 * math.pi * freq * t))
        buf += value.to_bytes(2, byteorder="little", signed=True)
        buf += value.to_bytes(2, byteorder="little", signed=True)

    sound = pygame.mixer.Sound(buffer=bytes(buf))
    ui_channel.stop()
    ui_channel.play(sound)


def play_intro_video(path: Path) -> bool:
    if not path.exists():
        raise FileNotFoundError(f"Missing video: {path}")

    cap = cv2.VideoCapture(str(path))
    player = None
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {path}")
        if pygame.mixer.get_init() is not None:
            player = MediaPlayer(str(path))

        start_time = time.monotonic()
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(video_fps) or video_fps <= 0:
            video_fps = 30.0
        frame_index = 0

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE
                ):
                    return True

            target_time = frame_index / video_fps
            if time.monotonic() - start_time < target_time:
                clock.tick(FPS)
                continue

            ok, frame = cap.read()
            if not ok:
                return True
            if player is not None:
                player.get_frame()

            frame_index += 1
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (SCREEN_W, SCREEN_H))
            surface = pygame.image.frombuffer(
                frame.tobytes(), (SCREEN_W, SCREEN_H), "RGB"
            )
            screen.blit(surface, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        try:
            cap.release()
        finally:
            if player is not None:
                player.close_player()


def draw_text(surface, font, text, color, pos):
    x, y = pos
    shadow = font.render(text, True, SHADOW)
    main = font.render(text, True, color)
    surface.blit(shadow, (x + 3, y + 3))
    surface.blit(main, (x, y))


def draw_blue_panel(rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, LAVENDER, rect)
    pygame.draw.rect(screen, BLACK, rect, 3)

    inner = rect.inflate(-34, -34)
    pygame.draw.rect(screen, BLUE, inner)
    pygame.draw.rect(screen, BLUE_DARK, inner, 4)
    pygame.draw.rect(screen, WHITE, inner, 2)


class Keyboard:
    def __init__(self):
        self.keys = [
            ["ESC", "A", "B", "C", "D", "E", "F", "G"],
            ["H", "I", "J", "K", "L", "M", "N", "O"],
            ["P", "Q", "R", "S", "T", "U", "V", "ENTER"],
            ["W", "X", "Y", "Z", ".", "BS"],
        ]
        self.row = 0
        self.col = 1
        self.blink = True
        self.blink_timer = 0.0

    def update(self, dt):
        self.blink_timer += dt
        if self.blink_timer >= 0.16:
            self.blink_timer = 0.0
            self.blink = not self.blink

    def move(self, dx, dy):
        old = (self.row, self.col)

        self.row = max(0, min(len(self.keys) - 1, self.row + dy))
        self.col = max(0, min(len(self.keys[self.row]) - 1, self.col + dx))

        moved = old != (self.row, self.col)

        if moved:
            self.blink = True
            self.blink_timer = 0.0
            beep(1100, 35, 0.25)

    def current(self):
        return self.keys[self.row][self.col]

    def draw(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        screen.blit(overlay, (0, 0))

        start_x = 305
        start_y = 370
        cell_w = 95
        cell_h = 72
        gap = 4

        panel = pygame.Rect(start_x - 35, start_y - 35, 860, 380)
        pygame.draw.rect(screen, (160, 160, 160), panel)
        pygame.draw.rect(screen, BLACK, panel, 3)

        for r, row in enumerate(self.keys):
            for c, label in enumerate(row):
                x = start_x + c * (cell_w + gap)
                y = start_y + r * (cell_h + gap)

                if label == "ENTER":
                    w = 124
                elif label == "BS":
                    w = 145
                else:
                    w = cell_w

                h = cell_h
                rect = pygame.Rect(x, y, w, h)
                selected = r == self.row and c == self.col

                fill = (245, 245, 210) if selected and self.blink else (145, 145, 125)

                pygame.draw.rect(screen, fill, rect)
                pygame.draw.rect(screen, BLACK, rect, 3)
                pygame.draw.line(
                    screen,
                    WHITE,
                    (rect.x + 2, rect.y + 2),
                    (rect.right - 2, rect.y + 2),
                    2,
                )
                pygame.draw.line(
                    screen,
                    WHITE,
                    (rect.x + 2, rect.y + 2),
                    (rect.x + 2, rect.bottom - 2),
                    2,
                )

                txt = font_key.render(label, True, BLACK)
                screen.blit(txt, txt.get_rect(center=rect.center))


class App:
    def __init__(self):
        self.running = True
        self.state = "login"
        self.state_timer = 0.0

        self.keyboard = Keyboard()

        self.login_text = ""
        self.password_text = ""

        self.cursor_timer = 0.0
        self.cursor_on = True

        self.floor_options = ["B2", "B3", "Cancel"]
        self.floor_selected = 1
        self.quit_selected = 1
        self.quit_return_state = ("login", 0.0)

        self.unlocked_floors = set()
        self.last_floor = "B3"

    def set_state(self, state: str):
        if state == "quit":
            self.quit_return_state = (self.state, self.state_timer)
            self.quit_selected = 1
        self.state = state
        self.state_timer = 0.0

        if state == "login":
            self.unlocked_floors.clear()
            self.login_text = ""
            self.password_text = ""
            self.keyboard = Keyboard()
            self.cursor_on = True
            self.cursor_timer = 0.0

        elif state == "password":
            self.password_text = ""
            self.keyboard = Keyboard()
            self.cursor_on = True
            self.cursor_timer = 0.0

        elif state == "denied":
            self.password_text = ""
            self.keyboard = Keyboard()
            self.cursor_on = True
            self.cursor_timer = 0.0
            beep(220, 220, 0.50)

        elif state == "floor":
            self.floor_selected = 1

        elif state == "accessing":
            beep(700, 120, 0.40)

        elif state == "unlocked":
            beep(1200, 160, 0.45)

    def update_cursor(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.42:
            self.cursor_timer = 0.0
            self.cursor_on = not self.cursor_on

    def update(self, dt):
        self.state_timer += dt

        if self.state in ("login", "password", "denied"):
            self.update_cursor(dt)
            self.keyboard.update(dt)

        elif self.state == "desktop":
            if self.state_timer >= 0.75:
                self.set_state("floor")

        elif self.state == "accessing":
            if self.state_timer >= 1.45:
                self.set_state("map_b3")

        elif self.state == "map_b3":
            if self.state_timer >= 1.35:
                self.set_state("unlocked")

    def submit_key(self):
        label = self.keyboard.current()

        if label == "ESC":
            self.set_state("quit")
            return

        if self.state == "login":
            if label == "BS":
                self.login_text = self.login_text[:-1]
                beep()

            elif label == "ENTER":
                if self.login_text == VALID_LOGIN:
                    beep(1000, 60, 0.35)
                    self.set_state("password")
                else:
                    self.set_state("denied")

            elif len(label) == 1 and len(self.login_text) < 8:
                self.login_text += label
                beep()

        elif self.state in ("password", "denied"):
            if label == "BS":
                self.password_text = self.password_text[:-1]
                beep()

            elif label == "ENTER":
                if self.login_text != VALID_LOGIN:
                    self.set_state("login")
                    return
                if self.password_text == PASSWORD_ADA:
                    self.unlocked_floors = {random.choice(["B2", "B3"])}
                    beep(1000, 70, 0.40)
                    self.set_state("desktop")

                elif self.password_text == PASSWORD_MOLE:
                    self.unlocked_floors = {"B2", "B3"}
                    beep(1000, 70, 0.40)
                    self.set_state("desktop")

                else:
                    self.set_state("denied")

            elif len(label) == 1 and len(self.password_text) < 8:
                self.password_text += label
                beep()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_ESCAPE:
            if self.state in ("login", "password", "denied", "floor"):
                self.set_state("quit")
            else:
                self.running = False
            return

        if self.state in ("login", "password", "denied"):
            if event.key == pygame.K_LEFT:
                self.keyboard.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                self.keyboard.move(1, 0)
            elif event.key == pygame.K_UP:
                self.keyboard.move(0, -1)
            elif event.key == pygame.K_DOWN:
                self.keyboard.move(0, 1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.submit_key()

        elif self.state == "floor":
            if event.key == pygame.K_UP:
                self.floor_selected = max(0, self.floor_selected - 1)
                beep()

            elif event.key == pygame.K_DOWN:
                self.floor_selected = min(len(self.floor_options) - 1, self.floor_selected + 1)
                beep()

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = self.floor_options[self.floor_selected]

                if choice == "Cancel":
                    self.set_state("quit")

                elif choice in self.unlocked_floors:
                    self.last_floor = choice
                    self.set_state("accessing")

                else:
                    self.set_state("denied")

        elif self.state == "quit":
            if event.key == pygame.K_UP:
                self.quit_selected = 0
                beep()

            elif event.key == pygame.K_DOWN:
                self.quit_selected = 1
                beep()

            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.quit_selected == 0:
                    self.running = False
                else:
                    self.state, self.state_timer = self.quit_return_state

        elif self.state == "unlocked":
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.set_state("floor")

    def draw_login_overlay(self):
        panel = pygame.Rect(85, 48, 1110, 330)
        draw_blue_panel(panel)

        draw_text(screen, font_mid, "Umbrella Computer OS ROPLS™", WHITE, (125, 95))
        draw_text(screen, font_mid, "Copyright©  Umbrella Corp.", WHITE, (125, 155))

        if self.state == "login":
            txt = f"Login: {self.login_text}"
            if self.cursor_on:
                txt += "_"
            draw_text(screen, font_mid, txt, WHITE, (125, 220))

        else:
            draw_text(screen, font_mid, f"Login: {VALID_LOGIN}", WHITE, (125, 220))

            masked = "*" * len(self.password_text)
            if self.cursor_on:
                masked += "_"

            draw_text(screen, font_mid, f"Password: {masked}", WHITE, (125, 280))

    def draw_denied_password_overlay(self):
        screen.blit(img_denied, (0, 0))

        masked = "*" * len(self.password_text)
        if self.cursor_on:
            masked += "_"

        draw_text(screen, font_mid, masked, WHITE, (475, 225))

    def draw_floor_overlay(self):
        panel = pygame.Rect(80, 50, 1120, 320)
        draw_blue_panel(panel)

        draw_text(screen, font_mid, "Basement Doorlock Operation", WHITE, (120, 105))
        draw_text(screen, font_mid, "Select Floor", WHITE, (120, 230))

        menu = pygame.Rect(635, 255, 330, 285)
        pygame.draw.rect(screen, LAVENDER, menu)
        pygame.draw.rect(screen, BLACK, menu, 3)

        inner = menu.inflate(-28, -28)
        pygame.draw.rect(screen, BLUE, inner)
        pygame.draw.rect(screen, BLACK, inner, 2)

        for i, option in enumerate(self.floor_options):
            y = inner.y + 28 + i * 72

            if i == self.floor_selected:
                pygame.draw.rect(screen, GREEN, (inner.x, y - 4, inner.w, 64))

            draw_text(screen, font_mid, option, WHITE, (inner.x + 28, y))

    def draw_quit_overlay(self):
        screen.blit(img_quit, (0, 0))

        panel = pygame.Rect(690, 250, 330, 390)
        draw_blue_panel(panel)

        draw_text(screen, font_mid, "Quit?", WHITE, (760, 315))

        for i, txt in enumerate(["Yes", "No"]):
            y = 445 + i * 78

            if i == self.quit_selected:
                pygame.draw.rect(screen, GREEN, (735, y - 8, 210, 68))

            draw_text(screen, font_mid, txt, WHITE, (760, y))

    def render(self):
        if self.state == "login":
            screen.blit(img_login, (0, 0))
            self.draw_login_overlay()
            self.keyboard.draw()

        elif self.state == "password":
            screen.blit(img_password, (0, 0))
            self.draw_login_overlay()
            self.keyboard.draw()

        elif self.state == "denied":
            self.draw_denied_password_overlay()
            self.keyboard.draw()

        elif self.state == "desktop":
            screen.blit(img_desktop, (0, 0))

        elif self.state == "floor":
            screen.blit(img_floor, (0, 0))
            self.draw_floor_overlay()

        elif self.state == "accessing":
            screen.blit(img_accessing, (0, 0))

        elif self.state == "map_b3":
            screen.blit(img_map_b2 if self.last_floor == "B2" else img_map_b3, (0, 0))

        elif self.state == "unlocked":
            screen.blit(img_unlocked_b2 if self.last_floor == "B2" else img_unlocked, (0, 0))

        elif self.state == "quit":
            self.draw_quit_overlay()

        draw_scanlines(screen, alpha=16)

        flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flicker.fill((0, 0, 0, 5))
        screen.blit(flicker, (0, 0))

        pygame.display.flip()

    def run(self):
        if not play_intro_video(VIDEO_INTRO):
            return

        while self.running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            if not self.running:
                break
            self.update(dt)
            self.render()

        ui_channel.stop()


def initialize_resources():
    """Load resources explicitly, once per application run."""
    global screen
    global clock
    global font_mid
    global font_key
    global ui_channel
    global img_login
    global img_password
    global img_desktop
    global img_floor
    global img_accessing
    global img_map_b2
    global img_map_b3
    global img_unlocked_b2
    global img_unlocked
    global img_denied
    global img_quit

    initialize_pygame()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Resident Evil 1 - Umbrella Terminal")
    clock = pygame.time.Clock()
    font_mid = pygame.font.SysFont("couriernew", 46, bold=True)
    font_key = pygame.font.SysFont("arial", 34, bold=True)
    ui_channel = audio_channel(1)
    img_login = load_image(FRAME_LOGIN)
    img_password = load_image(FRAME_PASSWORD)
    img_desktop = load_image(FRAME_DESKTOP)
    img_floor = load_image(FRAME_FLOOR)
    img_accessing = load_image(FRAME_ACCESSING)
    img_map_b2 = load_image(FRAME_MAP_B2)
    img_map_b3 = load_image(FRAME_MAP_B3)
    img_unlocked_b2 = load_image(FRAME_UNLOCKED_B2)
    img_unlocked = load_image(FRAME_UNLOCKED)
    img_denied = load_image(FRAME_DENIED)
    img_quit = load_image(FRAME_QUIT)


def main():
    try:
        initialize_resources()
        App().run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
