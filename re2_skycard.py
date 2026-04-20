import sys
from pathlib import Path
from typing import Optional

import pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BG_IMAGE = BASE_DIR / "Skycard_hd_0.png"

SND_ACCEPT = BASE_DIR / "accept.mp3"
SND_WAITING = BASE_DIR / "beep_waitting.mp3"
SND_MAIN = BASE_DIR / "beep_main.mp3"

pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Door Lock Service")
clock = pygame.time.Clock()

WHITE_DIRTY = (230, 232, 228)
WHITE_SOFT = (200, 202, 198)
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


def load_sound(path: Path) -> Optional[pygame.mixer.Sound]:
    if not path.exists():
        return None
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error:
        return None


bg = load_image(BG_IMAGE)

snd_accept = load_sound(SND_ACCEPT)
snd_waiting = load_sound(SND_WAITING)
snd_main = load_sound(SND_MAIN)

wait_channel = pygame.mixer.Channel(1)
type_channel = pygame.mixer.Channel(2)

font_title = pygame.font.SysFont("couriernew", 28, bold=True)
font_term = pygame.font.SysFont("couriernew", 30, bold=True)
font_prompt = pygame.font.SysFont("couriernew", 26, bold=True)
font_choice = pygame.font.SysFont("couriernew", 34, bold=True)


def play_sound(sound: Optional[pygame.mixer.Sound], loops: int = 0) -> None:
    if sound:
        sound.play(loops=loops)


def play_type_sound() -> None:
    if snd_main and not type_channel.get_busy():
        type_channel.play(snd_main)


def draw_shadow_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    shadow_color: tuple[int, int, int],
    pos: tuple[int, int],
) -> None:
    x_pos, y_pos = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x_pos + 2, y_pos + 2))
    surface.blit(main, (x_pos, y_pos))


def lerp(a_val: float, b_val: float, factor: float) -> float:
    return a_val + (b_val - a_val) * factor


def ease_out_cubic(factor: float) -> float:
    factor = max(0.0, min(1.0, factor))
    return 1 - pow(1 - factor, 3)


def draw_arrow(surface: pygame.Surface, x_pos: int, y_pos: int) -> None:
    points = [(x_pos, y_pos), (x_pos + 14, y_pos + 8), (x_pos, y_pos + 16)]
    pygame.draw.polygon(surface, WHITE_DIRTY, points)
    pygame.draw.polygon(surface, SHADOW, points, 1)


def draw_scanlines(
    surface: pygame.Surface,
    alpha: int = 18,
    step: int = 2,
) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    width, height = surface.get_size()
    for y_pos in range(0, height, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y_pos), (width, y_pos))
    surface.blit(overlay, (0, 0))


def build_scene_base() -> pygame.Surface:
    base = bg.copy()
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 24))
    base.blit(overlay, (0, 0))
    return base


def make_terminal_background(
    scene_base: pygame.Surface,
    inner_rect: pygame.Rect,
) -> pygame.Surface:
    slice_surface = scene_base.subsurface(inner_rect).copy().convert_alpha()

    darken = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    darken.fill((0, 0, 0, 118))
    slice_surface.blit(darken, (0, 0))

    internal_scan = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    for y_pos in range(0, inner_rect.h, 3):
        pygame.draw.line(
            internal_scan,
            (255, 255, 255, 3),
            (0, y_pos),
            (inner_rect.w, y_pos),
        )
    slice_surface.blit(internal_scan, (0, 0))

    return slice_surface


def draw_window(
    surface: pygame.Surface,
    rect: pygame.Rect,
    scene_base: pygame.Surface,
    title: str = "PROGRAM(011)",
) -> pygame.Rect:
    x_pos, y_pos, width, height = rect

    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(
        surface,
        WHITE_DIRTY,
        (x_pos + 1, y_pos + 1),
        (x_pos + width - 2, y_pos + 1),
    )
    pygame.draw.line(
        surface,
        WHITE_DIRTY,
        (x_pos + 1, y_pos + 1),
        (x_pos + 1, y_pos + height - 2),
    )
    pygame.draw.line(
        surface,
        FRAME_DARK,
        (x_pos, y_pos + height - 1),
        (x_pos + width - 1, y_pos + height - 1),
    )
    pygame.draw.line(
        surface,
        FRAME_DARK,
        (x_pos + width - 1, y_pos),
        (x_pos + width - 1, y_pos + height - 1),
    )

    bar_height = max(24, int(height * 0.05))
    title_rect = pygame.Rect(x_pos + 4, y_pos + 4, width - 8, bar_height)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    button_width = 18
    left_button = pygame.Rect(x_pos + 8, y_pos + 7, button_width, bar_height - 6)
    right_button = pygame.Rect(
        x_pos + width - 8 - button_width,
        y_pos + 7,
        button_width,
        bar_height - 6,
    )
    pygame.draw.rect(surface, FRAME_MID, left_button)
    pygame.draw.rect(surface, FRAME_MID, right_button)
    pygame.draw.rect(surface, FRAME_DARK, left_button, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_button, 1)

    pygame.draw.line(
        surface,
        BLACK,
        (left_button.x + 4, left_button.centery),
        (left_button.right - 4, left_button.centery),
        2,
    )
    pygame.draw.line(
        surface,
        BLACK,
        (right_button.x + 4, right_button.centery),
        (right_button.right - 4, right_button.centery),
        2,
    )

    title_surface = font_title.render(title, True, (80, 80, 80))
    title_pos = title_surface.get_rect(
        center=(x_pos + width // 2, y_pos + 4 + bar_height // 2)
    )
    surface.blit(title_surface, title_pos)

    pad = 6
    inner = pygame.Rect(
        x_pos + pad,
        y_pos + bar_height + pad,
        width - pad * 2,
        height - bar_height - pad * 2 - 10,
    )

    inner_surface = make_terminal_background(scene_base, inner)
    surface.blit(inner_surface, inner.topleft)
    pygame.draw.rect(surface, BLACK, inner, 2)

    bottom_height = 12
    bottom_rect = pygame.Rect(
        x_pos + 4,
        y_pos + height - bottom_height - 4,
        width - 8,
        bottom_height,
    )
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(
        bottom_rect.x + 80,
        bottom_rect.y + 1,
        18,
        bottom_rect.h - 2,
    )
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner


INFO_LINES = [
    ("DOOR LOCK SERVICE", WHITE_DIRTY),
    ("--------------------------------", WHITE_DIRTY),
    ("Hall side doors: ", WHITE_DIRTY, "LOCKED", GREEN_TEXT),
    ("", WHITE_DIRTY),
    ("The doors can be unlocked", WHITE_DIRTY),
    ("by a ", WHITE_DIRTY, "CARD KEY", GREEN_TEXT, ".", WHITE_DIRTY),
    ("-", WHITE_DIRTY),
]

CHECKING_REPLACEMENT_LINES = [
    ("Checking up ID-CARD....", WHITE_DIRTY),
]

DONE_LINES = [
    ("OK!", WHITE_DIRTY),
    ("Hall side doors lock released.", WHITE_DIRTY),
    ("-", WHITE_DIRTY),
]

QUESTION_1 = "Will you use the"
QUESTION_2 = "Blue Card Key?"


class App:
    def __init__(self) -> None:
        self.running = True
        self.state = "idle_bg"
        self.state_timer = 0.0

        self.target_rect = pygame.Rect(26, 30, 820, 390)
        self.grow_origin = (96, 110)
        self.grow_start_size = (120, 64)
        self.grow_duration = 0.55
        self.idle_bg_duration = 0.65

        self.visible_lines = []
        self.line_index = 0
        self.char_index = 0
        self.typing_speed = 0.060
        self.typing_accum = 0.0

        self.question_char_index_1 = 0
        self.question_char_index_2 = 0
        self.question_speed = 0.045
        self.question_accum = 0.0

        self.selected = 0
        self.checking_dots = 0
        self.dot_timer = 0.0

        self.subtitle = "Door lock control."
        self.subtitle_visible = ""
        self.subtitle_index = 0
        self.subtitle_accum = 0.0

        self.base_lines = INFO_LINES[:]
        self.replace_start_index = 4

    def current_window_rect(self) -> pygame.Rect:
        if self.state != "grow":
            return self.target_rect.copy()

        factor = ease_out_cubic(min(1.0, self.state_timer / self.grow_duration))
        start_width, start_height = self.grow_start_size
        target_width, target_height = self.target_rect.size

        width = int(lerp(start_width, target_width, factor))
        height = int(lerp(start_height, target_height, factor))
        x_pos = int(lerp(self.grow_origin[0], self.target_rect.x, factor))
        y_pos = int(lerp(self.grow_origin[1], self.target_rect.y, factor))
        return pygame.Rect(x_pos, y_pos, width, height)

    def reset_typing(self) -> None:
        self.visible_lines = [""]
        self.line_index = 0
        self.char_index = 0
        self.typing_accum = 0.0

    def set_state(self, new_state: str) -> None:
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing":
            self.reset_typing()

        elif new_state == "question":
            self.question_char_index_1 = 0
            self.question_char_index_2 = 0
            self.question_accum = 0.0
            play_sound(snd_main)

        elif new_state == "checking":
            self.checking_dots = 0
            self.dot_timer = 0.0
            if snd_waiting:
                wait_channel.play(snd_waiting, loops=-1)

        elif new_state == "done":
            wait_channel.stop()
            play_sound(snd_accept)

    def update_subtitle(self, dt: float) -> None:
        if self.subtitle_index >= len(self.subtitle):
            return

        self.subtitle_accum += dt
        speed = 0.028

        while self.subtitle_accum >= speed and self.subtitle_index < len(self.subtitle):
            self.subtitle_accum -= speed
            self.subtitle_visible += self.subtitle[self.subtitle_index]
            self.subtitle_index += 1

    def update_typing(self, dt: float) -> None:
        if self.line_index >= len(self.base_lines):
            return

        self.typing_accum += dt
        while self.typing_accum >= self.typing_speed:
            self.typing_accum -= self.typing_speed

            line = self.base_lines[self.line_index]
            base_text = line[0]

            if self.char_index < len(base_text):
                char = base_text[self.char_index]
                self.visible_lines[-1] += char
                self.char_index += 1

                if char != " ":
                    play_type_sound()
            else:
                if len(line) in (4, 6):
                    self.visible_lines[-1] = line
                    play_type_sound()
                else:
                    self.visible_lines[-1] = (self.visible_lines[-1], line[1])

                self.line_index += 1
                self.char_index = 0

                if self.line_index < len(self.base_lines):
                    self.visible_lines.append("")

    def update_question_typing(self, dt: float) -> None:
        self.question_accum += dt
        while self.question_accum >= self.question_speed:
            self.question_accum -= self.question_speed

            if self.question_char_index_1 < len(QUESTION_1):
                char = QUESTION_1[self.question_char_index_1]
                self.question_char_index_1 += 1
                if char != " ":
                    play_type_sound()

            elif self.question_char_index_2 < len(QUESTION_2):
                char = QUESTION_2[self.question_char_index_2]
                self.question_char_index_2 += 1
                if char != " ":
                    play_type_sound()

    def build_lines_for_current_state(self):
        lines = self.base_lines[:]

        if self.state in ("typing", "question"):
            return lines

        if self.state == "checking":
            prefix = lines[:self.replace_start_index]
            return prefix + CHECKING_REPLACEMENT_LINES

        if self.state == "done":
            prefix = lines[:self.replace_start_index]
            return prefix + CHECKING_REPLACEMENT_LINES + DONE_LINES

        return lines

    def update(self, dt: float) -> None:
        self.state_timer += dt
        self.update_subtitle(dt)

        if self.state == "idle_bg":
            if self.state_timer >= self.idle_bg_duration:
                self.set_state("grow")

        elif self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing")

        elif self.state == "typing":
            self.update_typing(dt)
            if self.line_index >= len(self.base_lines) and self.state_timer >= 2.5:
                self.set_state("question")

        elif self.state == "question":
            self.update_question_typing(dt)

        elif self.state == "checking":
            self.dot_timer += dt
            if self.dot_timer >= 0.40:
                self.dot_timer = 0.0
                self.checking_dots = (self.checking_dots + 1) % 5

            if self.state_timer >= 2.8:
                self.set_state("done")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return

            if self.state == "typing":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.visible_lines = []
                    for line in self.base_lines:
                        if len(line) in (4, 6):
                            self.visible_lines.append(line)
                        else:
                            self.visible_lines.append((line[0], line[1]))
                    self.line_index = len(self.base_lines)
                    self.char_index = 0
                    self.state_timer = 999

            elif self.state == "question":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.selected = max(0, self.selected - 1)
                    play_sound(snd_main)

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.selected = min(1, self.selected + 1)
                    play_sound(snd_main)

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.selected == 0:
                        self.set_state("checking")
                    else:
                        if snd_accept:
                            snd_accept.play()
                            pygame.time.delay(350)
                        self.running = False

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.running = False

    def draw_subtitle(self) -> None:
        if self.state in ("question", "checking", "done"):
            return

        draw_shadow_text(
            screen,
            font_prompt,
            self.subtitle_visible,
            WHITE_SOFT,
            SHADOW,
            (90, SCREEN_H - 80),
        )

    def draw_lines(self, inner_rect: pygame.Rect) -> None:
        if self.state in ("typing", "question"):
            items = self.visible_lines
        else:
            items = self.build_lines_for_current_state()

        x_pos = inner_rect.x + 18
        y_pos = inner_rect.y + 10
        line_height = 44

        for idx, item in enumerate(items):
            if self.state == "checking" and idx == self.replace_start_index:
                dynamic_text = f"Checking up ID-CARD{'.' * self.checking_dots}"
                draw_shadow_text(
                    screen,
                    font_term,
                    dynamic_text,
                    WHITE_DIRTY,
                    SHADOW,
                    (x_pos, y_pos),
                )
            else:
                if isinstance(item, str):
                    draw_shadow_text(
                        screen,
                        font_term,
                        item,
                        WHITE_DIRTY,
                        SHADOW,
                        (x_pos, y_pos),
                    )
                else:
                    if len(item) == 2:
                        text, color = item
                        draw_shadow_text(
                            screen,
                            font_term,
                            text,
                            color,
                            SHADOW,
                            (x_pos, y_pos),
                        )
                    elif len(item) == 4:
                        left_text, left_color, right_text, right_color = item
                        draw_shadow_text(
                            screen,
                            font_term,
                            left_text,
                            left_color,
                            SHADOW,
                            (x_pos, y_pos),
                        )
                        left_width = font_term.size(left_text)[0]
                        draw_shadow_text(
                            screen,
                            font_term,
                            right_text,
                            right_color,
                            GREEN_DARK,
                            (x_pos + left_width, y_pos),
                        )
                    elif len(item) == 6:
                        left_text, left_color, mid_text, mid_color, right_text, right_color = item
                        draw_shadow_text(
                            screen,
                            font_term,
                            left_text,
                            left_color,
                            SHADOW,
                            (x_pos, y_pos),
                        )
                        offset = font_term.size(left_text)[0]
                        draw_shadow_text(
                            screen,
                            font_term,
                            mid_text,
                            mid_color,
                            GREEN_DARK,
                            (x_pos + offset, y_pos),
                        )
                        offset += font_term.size(mid_text)[0]
                        draw_shadow_text(
                            screen,
                            font_term,
                            right_text,
                            right_color,
                            SHADOW,
                            (x_pos + offset, y_pos),
                        )
            y_pos += line_height

    def draw_question(self) -> None:
        question_1 = QUESTION_1[:self.question_char_index_1]
        question_2 = QUESTION_2[:self.question_char_index_2]

        draw_shadow_text(
            screen,
            font_prompt,
            question_1,
            WHITE_SOFT,
            SHADOW,
            (90, SCREEN_H - 112),
        )
        draw_shadow_text(
            screen,
            font_prompt,
            question_2,
            GREEN_TEXT,
            GREEN_DARK,
            (390, SCREEN_H - 112),
        )

        draw_shadow_text(
            screen,
            font_choice,
            "Yes",
            WHITE_DIRTY,
            SHADOW,
            (760, SCREEN_H - 78),
        )
        draw_shadow_text(
            screen,
            font_choice,
            "No",
            WHITE_DIRTY,
            SHADOW,
            (900, SCREEN_H - 78),
        )

        if self.selected == 0:
            draw_arrow(screen, 730, SCREEN_H - 66)
        else:
            draw_arrow(screen, 870, SCREEN_H - 66)

    def draw_bottom_status(self) -> None:
        if self.state == "checking":
            draw_shadow_text(
                screen,
                font_prompt,
                "Checking card...",
                WHITE_SOFT,
                SHADOW,
                (90, SCREEN_H - 112),
            )

        elif self.state == "done":
            draw_shadow_text(
                screen,
                font_prompt,
                "Hall side doors: ",
                WHITE_SOFT,
                SHADOW,
                (90, SCREEN_H - 112),
            )
            draw_shadow_text(
                screen,
                font_prompt,
                "UNLOCKED",
                GREEN_TEXT,
                GREEN_DARK,
                (360, SCREEN_H - 112),
            )

    def render(self) -> None:
        scene_base = build_scene_base()
        screen.blit(scene_base, (0, 0))

        if self.state != "idle_bg":
            rect = self.current_window_rect()
            inner_rect = draw_window(screen, rect, scene_base, "PROGRAM(011)")

            if rect.w > 300 and rect.h > 140 and self.state != "grow":
                self.draw_lines(inner_rect)

            if self.state == "question":
                self.draw_question()
            elif self.state in ("checking", "done"):
                self.draw_bottom_status()

        self.draw_subtitle()
        draw_scanlines(screen, alpha=18, step=2)

        flicker = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        flicker.fill((0, 0, 0, 6))
        screen.blit(flicker, (0, 0))

        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                self.handle_event(event)

            self.update(dt)
            self.render()

        wait_channel.stop()


if __name__ == "__main__":
    app = App()
    app.run()
    pygame.quit()
    sys.exit()
