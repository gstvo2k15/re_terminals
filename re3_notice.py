import sys
import random
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BG_IMAGE = BASE_DIR / "Skycard_hd_0.png"

SND_MAIN = BASE_DIR / "beep_main.mp3"
SND_WAITING = BASE_DIR / "beep_waitting.mp3"

PASSWORD_OPTIONS = ["0131", "0513", "4011", "4312"]

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Resident Evil 3 - STARS Notice")
clock = pygame.time.Clock()

WHITE_DIRTY = (230, 232, 228)
SHADOW = (70, 74, 90)
GREEN_TEXT = (0, 210, 45)
GREEN_DARK = (10, 70, 18)

FRAME_LIGHT = (208, 208, 208)
FRAME_MID = (152, 152, 152)
FRAME_DARK = (54, 54, 54)

BLACK = (0, 0, 0)


def load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))


def load_sound(path: Path):
    if not path.exists():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


bg = load_image(BG_IMAGE)

snd_main = load_sound(SND_MAIN)
snd_waiting = load_sound(SND_WAITING)

type_channel = pygame.mixer.Channel(2)
wait_channel = pygame.mixer.Channel(3)

font_title = pygame.font.SysFont("couriernew", 28, bold=True)
font_term = pygame.font.SysFont("couriernew", 30, bold=True)


def play_sound(sound, loops=0):
    if sound:
        sound.play(loops=loops)


def play_type_sound():
    if snd_main and not type_channel.get_busy():
        type_channel.play(snd_main)


def start_waiting_sound():
    if snd_waiting and not wait_channel.get_busy():
        wait_channel.play(snd_waiting, loops=-1)


def stop_waiting_sound():
    wait_channel.stop()


def draw_shadow_text(surface, font, text, color, shadow_color, pos):
    x, y = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x + 2, y + 2))
    surface.blit(main, (x, y))


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - pow(1 - t, 3)


def draw_scanlines(surface, alpha=18, step=2):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    w, h = surface.get_size()
    for y in range(0, h, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (w, y))
    surface.blit(overlay, (0, 0))


def build_scene_base() -> pygame.Surface:
    base = bg.copy()
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 22))
    base.blit(overlay, (0, 0))
    return base


def make_console_background(scene_base: pygame.Surface, inner_rect: pygame.Rect) -> pygame.Surface:
    """Use the real scene slice as the console background."""
    slice_surface = scene_base.subsurface(inner_rect).copy().convert_alpha()

    darken = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    darken.fill((0, 0, 0, 118))
    slice_surface.blit(darken, (0, 0))

    internal_scan = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    for yy in range(0, inner_rect.h, 3):
        pygame.draw.line(internal_scan, (255, 255, 255, 3), (0, yy), (inner_rect.w, yy))
    slice_surface.blit(internal_scan, (0, 0))

    return slice_surface


def draw_window(surface, rect, scene_base, title="PROGRAM(1:1)"):
    x, y, w, h = rect

    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + w - 2, y + 1))
    pygame.draw.line(surface, WHITE_DIRTY, (x + 1, y + 1), (x + 1, y + h - 2))
    pygame.draw.line(surface, FRAME_DARK, (x, y + h - 1), (x + w - 1, y + h - 1))
    pygame.draw.line(surface, FRAME_DARK, (x + w - 1, y), (x + w - 1, y + h - 1))

    bar_h = max(24, int(h * 0.05))
    title_rect = pygame.Rect(x + 4, y + 4, w - 8, bar_h)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    btn_w = 18
    left_btn = pygame.Rect(x + 8, y + 7, btn_w, bar_h - 6)
    right_btn = pygame.Rect(x + w - 8 - btn_w, y + 7, btn_w, bar_h - 6)
    pygame.draw.rect(surface, FRAME_MID, left_btn)
    pygame.draw.rect(surface, FRAME_MID, right_btn)
    pygame.draw.rect(surface, FRAME_DARK, left_btn, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_btn, 1)
    pygame.draw.line(surface, BLACK, (left_btn.x + 4, left_btn.centery), (left_btn.right - 4, left_btn.centery), 2)
    pygame.draw.line(surface, BLACK, (right_btn.x + 4, right_btn.centery), (right_btn.right - 4, right_btn.centery), 2)

    title_surf = font_title.render(title, True, (80, 80, 80))
    title_pos = title_surf.get_rect(center=(x + w // 2, y + 4 + bar_h // 2))
    surface.blit(title_surf, title_pos)

    pad = 6
    inner = pygame.Rect(x + pad, y + bar_h + pad, w - pad * 2, h - bar_h - pad * 2 - 10)

    console_bg = make_console_background(scene_base, inner)
    surface.blit(console_bg, inner.topleft)

    pygame.draw.rect(surface, BLACK, inner, 2)

    bottom_h = 12
    bottom_rect = pygame.Rect(x + 4, y + h - bottom_h - 4, w - 8, bottom_h)
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(bottom_rect.x + 80, bottom_rect.y + 1, 18, bottom_rect.h - 2)
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner


def build_notice_blocks(password: str):
    block_notice = [
        ("NOTICE TO STARS PERSONNEL", WHITE_DIRTY),
    ]

    block_body = [
        ("Due to the emergency, the", WHITE_DIRTY),
        ("key to the STARS office has", WHITE_DIRTY),
        ("been moved to the evidence", WHITE_DIRTY),
        ("room.", WHITE_DIRTY),
    ]

    block_password = [
        ("", WHITE_DIRTY),
        ("Today's password for the", WHITE_DIRTY),
        ("safe is ", WHITE_DIRTY, password, GREEN_TEXT, ".", WHITE_DIRTY),
        ("-", WHITE_DIRTY),
    ]

    return block_notice, block_body, block_password


class App:
    def __init__(self):
        self.running = True
        self.state = "idle_bg"
        self.state_timer = 0.0

        self.password = random.choice(PASSWORD_OPTIONS)
        self.notice_block, self.body_block, self.password_block = build_notice_blocks(self.password)

        self.target_rect = pygame.Rect(42, 40, 1020, 470)
        self.grow_origin = (120, 120)
        self.grow_start_size = (140, 72)
        self.grow_duration = 0.48
        self.idle_bg_duration = 0.65

        self.pause_after_notice = 1.85
        self.pause_after_dots = 1.10
        self.pause_before_password = 1.95

        self.visible_lines = []
        self.current_block = []
        self.block_index = 0
        self.block_char = 0
        self.block_done = False

        self.typing_speed = 0.040
        self.typing_accum = 0.0

        self.flash_done = False
        self.flash_timer = 0.0

        self.dots_total = 3
        self.dots_done = 0
        self.dot_step_delay = 0.45

    def current_window_rect(self):
        if self.state != "grow":
            return self.target_rect.copy()

        t = ease_out_cubic(min(1.0, self.state_timer / self.grow_duration))
        sw, sh = self.grow_start_size
        tw, th = self.target_rect.size

        w = int(lerp(sw, tw, t))
        h = int(lerp(sh, th, t))
        x = int(lerp(self.grow_origin[0], self.target_rect.x, t))
        y = int(lerp(self.grow_origin[1], self.target_rect.y, t))
        return pygame.Rect(x, y, w, h)

    def begin_block(self, block_lines):
        self.current_block = block_lines
        self.block_index = 0
        self.block_char = 0
        self.block_done = False
        self.typing_accum = 0.0

        if not self.visible_lines:
            self.visible_lines = [""]

    def finalize_current_line(self, line):
        if len(line) in (4, 6):
            self.visible_lines[-1] = line
            play_type_sound()
        else:
            if isinstance(self.visible_lines[-1], str):
                self.visible_lines[-1] = (self.visible_lines[-1], line[1])
            else:
                self.visible_lines[-1] = line

    def update_typing_block(self, dt):
        if self.block_done:
            return

        self.typing_accum += dt
        while self.typing_accum >= self.typing_speed and not self.block_done:
            self.typing_accum -= self.typing_speed

            if self.block_index >= len(self.current_block):
                self.block_done = True
                break

            line = self.current_block[self.block_index]
            text = line[0]

            if self.block_char < len(text):
                ch = text[self.block_char]
                if not isinstance(self.visible_lines[-1], str):
                    self.visible_lines.append("")
                self.visible_lines[-1] += ch
                self.block_char += 1

                if ch != " ":
                    play_type_sound()

            else:
                self.finalize_current_line(line)
                self.block_index += 1
                self.block_char = 0

                if self.block_index < len(self.current_block):
                    self.visible_lines.append("")
                else:
                    self.block_done = True

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing_notice":
            self.visible_lines = [""]
            self.begin_block(self.notice_block)
            stop_waiting_sound()

        elif new_state == "pause_notice":
            stop_waiting_sound()

        elif new_state == "typing_dots":
            if self.visible_lines and self.visible_lines[-1] != "":
                self.visible_lines.append("")
            if not isinstance(self.visible_lines[-1], str):
                self.visible_lines.append("")
            self.visible_lines[-1] = ""
            self.dots_done = 0
            start_waiting_sound()

        elif new_state == "pause_dots":
            stop_waiting_sound()

        elif new_state == "typing_body":
            if self.visible_lines and self.visible_lines[-1] != "":
                self.visible_lines.append("")
            self.begin_block(self.body_block)
            stop_waiting_sound()

        elif new_state == "pause_password":
            stop_waiting_sound()

        elif new_state == "typing_password":
            if self.visible_lines and self.visible_lines[-1] != "":
                self.visible_lines.append("")
            self.begin_block(self.password_block)
            stop_waiting_sound()

        elif new_state == "done":
            self.flash_done = False
            self.flash_timer = 0.0
            stop_waiting_sound()

    def update_dots(self):
        target_count = min(self.dots_total, int(self.state_timer / self.dot_step_delay))
        if target_count > self.dots_done:
            for _ in range(target_count - self.dots_done):
                self.visible_lines[-1] += "."
                self.dots_done += 1
                play_sound(snd_waiting)

    def update(self, dt):
        self.state_timer += dt

        if self.flash_done:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_done = False

        if self.state == "idle_bg":
            if self.state_timer >= self.idle_bg_duration:
                self.set_state("grow")

        elif self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing_notice")

        elif self.state == "typing_notice":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("pause_notice")

        elif self.state == "pause_notice":
            if self.state_timer >= self.pause_after_notice:
                self.set_state("typing_dots")

        elif self.state == "typing_dots":
            self.update_dots()
            if self.dots_done >= self.dots_total and self.state_timer >= (self.dots_total * self.dot_step_delay + 0.15):
                self.set_state("pause_dots")

        elif self.state == "pause_dots":
            if self.state_timer >= self.pause_after_dots:
                self.set_state("typing_body")

        elif self.state == "typing_body":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("pause_password")

        elif self.state == "pause_password":
            if self.state_timer >= self.pause_before_password:
                self.set_state("typing_password")

        elif self.state == "typing_password":
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("done")

    def skip_to_done(self):
        stop_waiting_sound()
        self.visible_lines = []

        for line in self.notice_block:
            if len(line) in (4, 6):
                self.visible_lines.append(line)
            else:
                self.visible_lines.append((line[0], line[1]))

        self.visible_lines.append(("...", WHITE_DIRTY))

        for line in self.body_block:
            if len(line) in (4, 6):
                self.visible_lines.append(line)
            else:
                self.visible_lines.append((line[0], line[1]))

        for line in self.password_block:
            if len(line) in (4, 6):
                self.visible_lines.append(line)
            else:
                self.visible_lines.append((line[0], line[1]))

        self.set_state("done")

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            if self.state in {
                "typing_notice",
                "pause_notice",
                "typing_dots",
                "pause_dots",
                "typing_body",
                "pause_password",
                "typing_password",
            }:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.skip_to_done()

            elif self.state == "done":
                if event.key == pygame.K_r:
                    self.password = random.choice(PASSWORD_OPTIONS)
                    self.notice_block, self.body_block, self.password_block = build_notice_blocks(self.password)
                    self.flash_done = False
                    self.set_state("typing_notice")

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

    def draw_lines(self, inner_rect):
        x = inner_rect.x + 18
        y = inner_rect.y + 2
        line_h = 46

        for item in self.visible_lines:
            if isinstance(item, str):
                draw_shadow_text(screen, font_term, item, WHITE_DIRTY, SHADOW, (x, y))
            else:
                if len(item) == 2:
                    txt, color = item
                    draw_shadow_text(screen, font_term, txt, color, SHADOW, (x, y))
                elif len(item) == 4:
                    left_txt, left_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x, y))
                    left_width = font_term.size(left_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, GREEN_DARK, (x + left_width, y))
                elif len(item) == 6:
                    left_txt, left_col, mid_txt, mid_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x, y))
                    offset = font_term.size(left_txt)[0]
                    draw_shadow_text(screen, font_term, mid_txt, mid_col, GREEN_DARK, (x + offset, y))
                    offset += font_term.size(mid_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, SHADOW, (x + offset, y))
            y += line_h

    def render(self):
        scene_base = build_scene_base()
        screen.blit(scene_base, (0, 0))

        if self.state != "idle_bg":
            rect = self.current_window_rect()
            inner_rect = draw_window(screen, rect, scene_base, "PROGRAM(1:1)")

            if rect.w > 320 and rect.h > 160 and self.state != "grow":
                self.draw_lines(inner_rect)

        draw_scanlines(screen, alpha=18, step=2)

        flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flicker.fill((0, 0, 0, 6))
        screen.blit(flicker, (0, 0))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.render()

        stop_waiting_sound()


if __name__ == "__main__":
    app = App()
    app.run()
    pygame.quit()
    sys.exit()