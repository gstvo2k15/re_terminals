import sys
from pathlib import Path
from typing import Optional

import pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

SND_INTRO = BASE_DIR / "PC_re1-terminal_FINAL-beta3.mp3"

FRAME_FILES = [
    "RE1_oldPc_0.png",
    "RE1_oldPc_1.png",
    "RE1_oldPc_2.png",
    "RE1_oldPc_3.png",
    "RE1_oldPc_4.png",
    "RE1_oldPc_5.png",
    "RE1_oldPc_6.png",
    "RE1_oldPc_7.png",
]

FRAME_DURATIONS = [
    0.55,
    0.35,
    0.35,
    0.40,
    0.55,
    1.15,
    1.35,
    0.80,
]

FRAME_LOGIN = "RE1_oldPc_8.png"
FRAME_PASSWORD = "RE1_oldPc_9.png"
FRAME_DESKTOP = "RE1_oldPc_10.png"
FRAME_FLOOR = "RE1_oldPc_11.png"
FRAME_ACCESSING = "RE1_oldPc_12.png"
FRAME_MAP_B3 = "RE1_oldPc_13.png"
FRAME_UNLOCKED = "RE1_oldPc_14.png"
FRAME_DENIED = "RE1_oldPc_15.png"
FRAME_QUIT = "RE1_oldPc_16.png"

VALID_LOGIN = "JOHN"
VALID_PASSWORD = "ADA"

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Resident Evil 1 - Umbrella Terminal")
clock = pygame.time.Clock()

WHITE = (245, 245, 245)
BLACK = (0, 0, 0)
BLUE = (42, 54, 205)
BLUE_DARK = (20, 30, 135)
LAVENDER = (176, 178, 230)
GREEN = (0, 135, 75)
SHADOW = (30, 30, 70)

font_big = pygame.font.SysFont("couriernew", 62, bold=True)
font_mid = pygame.font.SysFont("couriernew", 46, bold=True)
font_small = pygame.font.SysFont("couriernew", 34, bold=True)
font_key = pygame.font.SysFont("arial", 34, bold=True)


def load_image(name: str) -> pygame.Surface:
    path = BASE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing image: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))


def load_sound(path: Path) -> Optional[pygame.mixer.Sound]:
    if not path.exists():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


frames = [load_image(name) for name in FRAME_FILES]
img_login = load_image(FRAME_LOGIN)
img_password = load_image(FRAME_PASSWORD)
img_desktop = load_image(FRAME_DESKTOP)
img_floor = load_image(FRAME_FLOOR)
img_accessing = load_image(FRAME_ACCESSING)
img_map_b3 = load_image(FRAME_MAP_B3)
img_unlocked = load_image(FRAME_UNLOCKED)
img_denied = load_image(FRAME_DENIED)
img_quit = load_image(FRAME_QUIT)

snd_intro = load_sound(SND_INTRO)
if snd_intro:
    snd_intro.set_volume(1.0)

intro_channel = pygame.mixer.Channel(0)
ui_channel = pygame.mixer.Channel(1)


def beep(freq: int = 900, duration_ms: int = 45, volume: float = 0.35) -> None:
    sample_rate = 44100
    samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray()

    for i in range(samples):
        value = int(32767 * volume * pygame.math.Vector2(1, 0).rotate(i * freq * 360 / sample_rate).x)
        buf += int(value).to_bytes(2, byteorder="little", signed=True)
        buf += int(value).to_bytes(2, byteorder="little", signed=True)

    sound = pygame.mixer.Sound(buffer=bytes(buf))
    ui_channel.stop()
    ui_channel.play(sound)


def draw_scanlines(surface: pygame.Surface, alpha: int = 18, step: int = 2) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    width, height = surface.get_size()
    for y in range(0, height, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (width, y))
    surface.blit(overlay, (0, 0))


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
        return moved

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
        pygame.draw.rect(screen, (160, 160, 160, 170), panel)
        pygame.draw.rect(screen, BLACK, panel, 3)

        for r, row in enumerate(self.keys):
            for c, label in enumerate(row):
                x = start_x + c * (cell_w + gap)
                y = start_y + r * (cell_h + gap)
                w = cell_w
                h = cell_h

                if label == "ENTER":
                    w = 150
                elif label == "BS":
                    w = 145

                rect = pygame.Rect(x, y, w, h)
                selected = r == self.row and c == self.col

                fill = (245, 245, 210) if selected and self.blink else (145, 145, 125)
                pygame.draw.rect(screen, fill, rect)
                pygame.draw.rect(screen, BLACK, rect, 3)
                pygame.draw.line(screen, WHITE, (rect.x + 2, rect.y + 2), (rect.right - 2, rect.y + 2), 2)
                pygame.draw.line(screen, WHITE, (rect.x + 2, rect.y + 2), (rect.x + 2, rect.bottom - 2), 2)

                txt = font_key.render(label, True, BLACK)
                screen.blit(txt, txt.get_rect(center=rect.center))


class App:
    def __init__(self):
        self.running = True
        self.state = "intro"
        self.state_timer = 0.0

        self.frame_index = 0
        self.frame_timer = 0.0
        self.intro_started = False

        self.keyboard = Keyboard()

        self.login_text = ""
        self.password_text = ""
        self.cursor_timer = 0.0
        self.cursor_on = True

        self.floor_options = ["B2", "B3", "Cancel"]
        self.floor_selected = 1

        self.quit_selected = 1

    def set_state(self, state: str):
        self.state = state
        self.state_timer = 0.0

        if state == "login":
            self.login_text = ""
            self.keyboard = Keyboard()

        elif state == "password":
            self.password_text = ""
            self.keyboard = Keyboard()

        elif state == "floor":
            self.floor_selected = 1

        elif state == "accessing":
            beep(700, 120, 0.40)

        elif state == "unlocked":
            beep(1200, 160, 0.45)

        elif state == "denied":
            beep(220, 220, 0.50)

    def update_intro(self, dt):
        if not self.intro_started:
            self.intro_started = True
            if snd_intro:
                intro_channel.play(snd_intro)

        self.frame_timer += dt

        if self.frame_index < len(frames):
            if self.frame_timer >= FRAME_DURATIONS[self.frame_index]:
                self.frame_timer = 0.0
                self.frame_index += 1

        if self.frame_index >= len(frames):
            self.set_state("login")

    def update_cursor(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.42:
            self.cursor_timer = 0.0
            self.cursor_on = not self.cursor_on

    def update(self, dt):
        self.state_timer += dt

        if self.state == "intro":
            self.update_intro(dt)

        elif self.state in ("login", "password"):
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

        elif self.state == "password":
            if label == "BS":
                self.password_text = self.password_text[:-1]
                beep()
            elif label == "ENTER":
                if self.password_text == VALID_PASSWORD:
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
            if self.state in ("login", "password", "floor"):
                self.set_state("quit")
            else:
                self.running = False
            return

        if self.state in ("login", "password"):
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
                if choice == "B3":
                    self.set_state("accessing")
                elif choice == "Cancel":
                    self.set_state("quit")
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
                    self.set_state("floor")

        elif self.state in ("unlocked", "denied"):
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.set_state("floor")

    def draw_login_overlay(self):
        panel = pygame.Rect(85, 48, 1110, 330)
        draw_blue_panel(panel)

        if self.state == "login":
            draw_text(screen, font_mid, "Umbrella Computer OS ROPLS™", WHITE, (125, 95))
            draw_text(screen, font_mid, "Copyright©  Umbrella Corp.", WHITE, (125, 155))
            txt = f"Login: {self.login_text}"
            if self.cursor_on:
                txt += "_"
            draw_text(screen, font_mid, txt, WHITE, (125, 220))

        else:
            draw_text(screen, font_mid, "Umbrella Computer OS ROPLS™", WHITE, (125, 95))
            draw_text(screen, font_mid, "Copyright©  Umbrella Corp.", WHITE, (125, 155))
            draw_text(screen, font_mid, f"Login: {VALID_LOGIN}", WHITE, (125, 220))
            masked = "*" * len(self.password_text)
            if self.cursor_on:
                masked += "_"
            draw_text(screen, font_mid, f"Password: {masked}", WHITE, (125, 280))

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

        options = ["Yes", "No"]
        for i, txt in enumerate(options):
            y = 445 + i * 78
            if i == self.quit_selected:
                pygame.draw.rect(screen, GREEN, (735, y - 8, 210, 68))
            draw_text(screen, font_mid, txt, WHITE, (760, y))

    def render(self):
        if self.state == "intro":
            idx = min(self.frame_index, len(frames) - 1)
            screen.blit(frames[idx], (0, 0))

        elif self.state == "login":
            screen.blit(img_login, (0, 0))
            self.draw_login_overlay()
            self.keyboard.draw()

        elif self.state == "password":
            screen.blit(img_password, (0, 0))
            self.draw_login_overlay()
            self.keyboard.draw()

        elif self.state == "desktop":
            screen.blit(img_desktop, (0, 0))

        elif self.state == "floor":
            screen.blit(img_floor, (0, 0))
            self.draw_floor_overlay()

        elif self.state == "accessing":
            screen.blit(img_accessing, (0, 0))

        elif self.state == "map_b3":
            screen.blit(img_map_b3, (0, 0))

        elif self.state == "unlocked":
            screen.blit(img_unlocked, (0, 0))

        elif self.state == "denied":
            screen.blit(img_denied, (0, 0))

        elif self.state == "quit":
            self.draw_quit_overlay()

        draw_scanlines(screen, alpha=16, step=2)

        flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flicker.fill((0, 0, 0, 5))
        screen.blit(flicker, (0, 0))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.render()

        intro_channel.stop()
        ui_channel.stop()


if __name__ == "__main__":
    try:
        App().run()
    finally:
        pygame.quit()
        sys.exit()