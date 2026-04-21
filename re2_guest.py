import sys
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent

SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

BG_IMAGE = BASE_DIR / "Guest_hd.png"

SND_OPEN = BASE_DIR / "safsprin_openning_terminal_letters_pc.mp3"
SND_LETTERS = BASE_DIR / "safsprin_letters_pc.mp3"
SND_CHOOSE = BASE_DIR / "safsprin_chosing_single_letters_pc.mp3"
SND_ENTER = BASE_DIR / "safsprin_enter_passwd_pc.mp3"
SND_FINISH = BASE_DIR / "safsprin_finish_passwd_pc.mp3"

VALID_USERNAME = "GUEST"

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Resident Evil 2 - Guest Terminal")
clock = pygame.time.Clock()

WHITE_DIRTY = (236, 236, 236)
SHADOW = (38, 38, 38)
FRAME_LIGHT = (208, 208, 208)
FRAME_MID = (152, 152, 152)
FRAME_DARK = (54, 54, 54)
KEY_FILL = (150, 150, 150)
KEY_FILL_BLINK_LOW = (155, 155, 155)
KEY_FILL_BLINK_HIGH = (188, 188, 188)
KEY_TEXT = (68, 68, 68)
BLACK = (0, 0, 0)

font_title = pygame.font.SysFont("couriernew", 26, bold=True)
font_term = pygame.font.SysFont("couriernew", 34, bold=True)
font_key = pygame.font.SysFont("arial", 24, bold=True)
font_key_small = pygame.font.SysFont("arial", 16, bold=True)

typing_channel = pygame.mixer.Channel(0)
ui_channel = pygame.mixer.Channel(1)
finish_channel = pygame.mixer.Channel(2)


def load_image(path: Path) -> pygame.Surface:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    img = pygame.image.load(str(path)).convert()
    return pygame.transform.smoothscale(img, (SCREEN_W, SCREEN_H))


def load_sound(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing sound file: {path}")
    try:
        return pygame.mixer.Sound(str(path))
    except pygame.error as e:
        raise RuntimeError(f"Cannot load sound {path}: {e}")


bg = load_image(BG_IMAGE)

snd_open = load_sound(SND_OPEN)
snd_letters = load_sound(SND_LETTERS)
snd_choose = load_sound(SND_CHOOSE)
snd_enter = load_sound(SND_ENTER)
snd_finish = load_sound(SND_FINISH)

snd_open.set_volume(1.0)
snd_letters.set_volume(1.0)
snd_choose.set_volume(0.75)
snd_enter.set_volume(0.85)
snd_finish.set_volume(1.0)


def play_enter():
    ui_channel.stop()
    ui_channel.play(snd_enter)


def play_finish():
    finish_channel.stop()
    finish_channel.play(snd_finish)


def draw_shadow_text(surface, font, text, color, shadow_color, pos):
    x_pos, y_pos = pos
    shadow = font.render(text, True, shadow_color)
    main = font.render(text, True, color)
    surface.blit(shadow, (x_pos + 2, y_pos + 2))
    surface.blit(main, (x_pos, y_pos))


def lerp(a_val, b_val, factor):
    return a_val + (b_val - a_val) * factor


def ease_out_cubic(factor):
    factor = max(0.0, min(1.0, factor))
    return 1 - pow(1 - factor, 3)


def draw_scanlines(surface, alpha=18, step=2):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    width, height = surface.get_size()
    for y_pos in range(0, height, step):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y_pos), (width, y_pos))
    surface.blit(overlay, (0, 0))


def build_scene_base():
    base = bg.copy()
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 12))
    base.blit(overlay, (0, 0))
    return base


def make_scene_window_background(scene_base, inner_rect):
    slice_surface = scene_base.subsurface(inner_rect).copy().convert_alpha()
    darken = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    darken.fill((0, 0, 0, 98))
    slice_surface.blit(darken, (0, 0))

    internal_scan = pygame.Surface((inner_rect.w, inner_rect.h), pygame.SRCALPHA)
    for y_pos in range(0, inner_rect.h, 3):
        pygame.draw.line(internal_scan, (255, 255, 255, 3), (0, y_pos), (inner_rect.w, y_pos))
    slice_surface.blit(internal_scan, (0, 0))
    return slice_surface


def make_plain_window_background(size):
    width, height = size
    surface = pygame.Surface((width, height))
    surface.fill((120, 120, 120))

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 30))
    surface.blit(overlay, (0, 0))

    for y_pos in range(0, height, 3):
        pygame.draw.line(surface, (135, 135, 135), (0, y_pos), (width, y_pos))

    return surface


def draw_window(surface, rect, title="PROGRAM(1:1)", scene_base=None, plain_fill=False):
    x_pos, y_pos, width, height = rect

    pygame.draw.rect(surface, FRAME_MID, rect)
    pygame.draw.rect(surface, FRAME_DARK, rect, 2)
    pygame.draw.line(surface, WHITE_DIRTY, (x_pos + 1, y_pos + 1), (x_pos + width - 2, y_pos + 1))
    pygame.draw.line(surface, WHITE_DIRTY, (x_pos + 1, y_pos + 1), (x_pos + 1, y_pos + height - 2))
    pygame.draw.line(surface, FRAME_DARK, (x_pos, y_pos + height - 1), (x_pos + width - 1, y_pos + height - 1))
    pygame.draw.line(surface, FRAME_DARK, (x_pos + width - 1, y_pos), (x_pos + width - 1, y_pos + height - 1))

    bar_height = max(24, int(height * 0.05))
    title_rect = pygame.Rect(x_pos + 4, y_pos + 4, width - 8, bar_height)
    pygame.draw.rect(surface, FRAME_LIGHT, title_rect)
    pygame.draw.rect(surface, FRAME_DARK, title_rect, 1)

    button_width = 18
    left_button = pygame.Rect(x_pos + 8, y_pos + 7, button_width, bar_height - 6)
    right_button = pygame.Rect(x_pos + width - 8 - button_width, y_pos + 7, button_width, bar_height - 6)
    pygame.draw.rect(surface, FRAME_MID, left_button)
    pygame.draw.rect(surface, FRAME_MID, right_button)
    pygame.draw.rect(surface, FRAME_DARK, left_button, 1)
    pygame.draw.rect(surface, FRAME_DARK, right_button, 1)
    pygame.draw.line(surface, BLACK, (left_button.x + 4, left_button.centery), (left_button.right - 4, left_button.centery), 2)
    pygame.draw.line(surface, BLACK, (right_button.x + 4, right_button.centery), (right_button.right - 4, right_button.centery), 2)

    title_surface = font_title.render(title, True, (80, 80, 80))
    title_pos = title_surface.get_rect(center=(x_pos + width // 2, y_pos + 4 + bar_height // 2))
    surface.blit(title_surface, title_pos)

    pad = 6
    inner = pygame.Rect(x_pos + pad, y_pos + bar_height + pad, width - pad * 2, height - bar_height - pad * 2 - 10)

    if plain_fill:
        inner_surface = make_plain_window_background((inner.w, inner.h))
    else:
        inner_surface = make_scene_window_background(scene_base, inner)

    surface.blit(inner_surface, inner.topleft)
    pygame.draw.rect(surface, BLACK, inner, 2)

    bottom_height = 12
    bottom_rect = pygame.Rect(x_pos + 4, y_pos + height - bottom_height - 4, width - 8, bottom_height)
    pygame.draw.rect(surface, FRAME_LIGHT, bottom_rect)
    pygame.draw.rect(surface, FRAME_DARK, bottom_rect, 1)

    handle = pygame.Rect(bottom_rect.x + 160, bottom_rect.y + 1, 18, bottom_rect.h - 2)
    pygame.draw.rect(surface, FRAME_MID, handle)
    pygame.draw.rect(surface, FRAME_DARK, handle, 1)

    return inner


class KeyboardWindow:
    def __init__(self):
        self.rect = pygame.Rect(185, 520, 910, 190)
        self.grid = [
            ["ESC", "A", "B", "C", "D", "E", "F", "G", "H", "BACK"],
            ["I", "J", "K", "L", "M", "N", "O", "P", "Q", "ENTER"],
            ["R", "S", "T", "U", "V", "W", "X", "Y", "Z", None],
        ]
        self.row = 0
        self.col = 1
        self.blink_timer = 0.0
        self.blink_on = True
        self.blink_interval = 0.16

    def update(self, dt):
        self.blink_timer += dt
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0.0
            self.blink_on = not self.blink_on

    def _is_enter_selected(self):
        return (self.row == 1 and self.col == 9) or (self.row == 2 and self.col == 9)

    def move(self, dx, dy):
        old_row = self.row
        old_col = self.col

        if dy != 0:
            if self._is_enter_selected():
                if dy < 0:
                    self.row = 0
                    self.col = 8
                elif dy > 0:
                    self.row = 2
                    self.col = 9
            else:
                target_row = max(0, min(2, self.row + dy))
                if self.row == 1 and self.col == 9 and dy > 0:
                    self.row = 2
                    self.col = 9
                else:
                    self.row = target_row

        if dx != 0:
            if self.row == 2 and self.col == 8 and dx > 0:
                self.row = 2
                self.col = 9
            elif self._is_enter_selected() and dx < 0:
                self.row = 2
                self.col = 8
            else:
                self.col = max(0, min(9, self.col + dx))
                if self.row == 0 and self.col == 9:
                    self.col = 8
                if self.row == 2 and self.col == 9 and dx > 0:
                    self.col = 9

        if self.row == 0 and self.col == 9:
            self.col = 8

        moved = old_row != self.row or old_col != self.col
        if moved:
            self.blink_timer = 0.0
            self.blink_on = True
        return moved

    def get_label(self):
        if self._is_enter_selected():
            return "ENTER"
        return self.grid[self.row][self.col]

    def draw_enter_symbol(self, surface, rect):
        x_right = rect.centerx + 15
        x_inner = x_right - 5

        y_top = rect.y + 20
        y_base_top = rect.bottom - 36
        y_base_bottom = rect.bottom - 31

        x_base_left = rect.centerx - 7
        x_notch_outer = rect.centerx - 18   # MÁS CERCA -> diagonal corta
        y_notch_top = rect.bottom - 41
        y_notch_bottom = rect.bottom - 38

        points = [
            (x_inner, y_top),
            (x_right, y_top),
            (x_right, y_base_bottom),
            (x_base_left, y_base_bottom),
            (x_notch_outer, y_notch_bottom),
            (x_notch_outer + 3, y_notch_top),  # punta más compacta
            (x_base_left + 2, y_base_top),
            (x_inner, y_base_top),
        ]

        pygame.draw.polygon(surface, KEY_TEXT, points)

    def draw(self, surface):
        inner = draw_window(surface, self.rect, "KEYBOARD(1:1)", plain_fill=True)

        start_x = inner.x + 4
        start_y = inner.y + 4
        gap = 4
        cell_w = (inner.w - gap * 9) // 10
        cell_h = (inner.h - gap * 2) // 3

        for row_idx in range(3):
            for col_idx in range(10):
                if row_idx == 2 and col_idx == 9:
                    continue

                label = self.grid[row_idx][col_idx]
                x_pos = start_x + col_idx * (cell_w + gap)
                y_pos = start_y + row_idx * (cell_h + gap)

                width = cell_w
                height = cell_h

                is_enter = row_idx == 1 and col_idx == 9
                if is_enter:
                    height = cell_h * 2 + gap

                rect = pygame.Rect(x_pos, y_pos, width, height)

                if is_enter:
                    selected = self._is_enter_selected()
                else:
                    selected = row_idx == self.row and col_idx == self.col

                if selected:
                    fill = KEY_FILL_BLINK_HIGH if self.blink_on else KEY_FILL_BLINK_LOW
                else:
                    fill = KEY_FILL

                pygame.draw.rect(surface, fill, rect)
                pygame.draw.rect(surface, FRAME_DARK, rect, 2)
                pygame.draw.line(surface, WHITE_DIRTY, (rect.x + 1, rect.y + 1), (rect.right - 2, rect.y + 1))
                pygame.draw.line(surface, WHITE_DIRTY, (rect.x + 1, rect.y + 1), (rect.x + 1, rect.bottom - 2))

                if label == "BACK":
                    lines = ["BACK", "SPACE"]
                    for idx, txt in enumerate(lines):
                        txt_surface = font_key_small.render(txt, True, KEY_TEXT)
                        txt_rect = txt_surface.get_rect(center=(rect.centerx, rect.y + rect.h * 0.35 + idx * 18))
                        surface.blit(txt_surface, txt_rect)
                elif label == "ESC":
                    txt_surface = font_key.render(label, True, KEY_TEXT)
                    txt_rect = txt_surface.get_rect(center=rect.center)
                    surface.blit(txt_surface, txt_rect)
                elif is_enter:
                    self.draw_enter_symbol(surface, rect)
                elif label is not None:
                    txt_surface = font_key.render(label, True, KEY_TEXT)
                    txt_rect = txt_surface.get_rect(center=rect.center)
                    surface.blit(txt_surface, txt_rect)


class App:
    def __init__(self):
        self.running = True
        self.state = "selector"
        self.state_timer = 0.0

        self.selector_rect = pygame.Rect(44, 111, 341, 143)

        self.target_rect = pygame.Rect(52, 53, 1053, 560)
        self.grow_origin = (130, 135)
        self.grow_start_size = (120, 90)
        self.grow_duration = 0.32
        self.selector_duration = 0.55

        self.intro_lines = [
            ('UMBRELLA "RODEM" SYSTEM', WHITE_DIRTY, "Ver 5.0", WHITE_DIRTY),
            ("Culture Experiment Room Staff", WHITE_DIRTY),
            ("Registry.", WHITE_DIRTY),
            ("", WHITE_DIRTY),
            ("Accessing.....", WHITE_DIRTY),
            ("", WHITE_DIRTY),
            ("Enter your user name.", WHITE_DIRTY),
        ]

        self.result_lines = [
            ("Register your fingerprint.", WHITE_DIRTY),
            ("Please wait.....", WHITE_DIRTY),
            ("Registration complete.", WHITE_DIRTY),
            ("", WHITE_DIRTY),
            ("Guest registration is valid", WHITE_DIRTY),
            ("for 24 hours.", WHITE_DIRTY),
            ("-", WHITE_DIRTY),
        ]

        self.visible_lines = []
        self.current_block = []
        self.block_index = 0
        self.block_char = 0
        self.block_done = False
        self.typing_accum = 0.0

        self.opening_speed = 0.030
        self.normal_speed = 0.030

        self.input_text = ""
        self.cursor_timer = 0.0
        self.cursor_on = True
        self.input_locked = False
        self.input_line_active = False

        self.keyboard = KeyboardWindow()

        self.typing_sound_cooldown = 0.0
        self.typing_sound_interval = 0.038
        self.choose_sound_cooldown = 0.0
        self.choose_sound_interval = 0.065

        self.open_sound_started = False
        self.open_sound_duration = snd_open.get_length()
        self.open_sound_elapsed = 0.0
        self.use_normal_letters_after_open = False

        self.flash_timer = 0.0
        self.flash_alpha = 0

        self.finish_waiting_to_start = False
        self.finish_has_started_playing = False

        self.result_phase = 0
        self.result_pause_timer = 0.0
        self.result_line_sound_duration = max(snd_letters.get_length(), 0.16)

    def play_choose(self):
        if self.choose_sound_cooldown > 0:
            return
        ui_channel.stop()
        ui_channel.play(snd_choose)
        self.choose_sound_cooldown = self.choose_sound_interval

    def current_window_rect(self):
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

    def current_speed(self):
        if self.state == "typing_intro":
            return self.opening_speed
        return self.normal_speed

    def begin_block(self, block_lines):
        self.current_block = block_lines
        self.block_index = 0
        self.block_char = 0
        self.block_done = False
        self.typing_accum = 0.0
        if not self.visible_lines:
            self.visible_lines = [""]

    def finalize_current_line(self, line):
        if len(line) == 4:
            self.visible_lines[-1] = line
        else:
            if isinstance(self.visible_lines[-1], str):
                self.visible_lines[-1] = (self.visible_lines[-1], line[1])
            else:
                self.visible_lines[-1] = line

    def start_open_sequence(self):
        self.open_sound_started = True
        self.open_sound_elapsed = 0.0
        self.use_normal_letters_after_open = False
        typing_channel.stop()
        typing_channel.play(snd_open)

    def update_open_sequence(self, dt):
        if not self.open_sound_started or self.use_normal_letters_after_open:
            return

        self.open_sound_elapsed += dt

        if self.open_sound_elapsed >= max(0.0, self.open_sound_duration - 0.01):
            self.use_normal_letters_after_open = True
            self.typing_sound_cooldown = 0.0

    def play_normal_letter_sound(self):
        if self.typing_sound_cooldown > 0:
            return
        typing_channel.stop()
        typing_channel.play(snd_letters)
        self.typing_sound_cooldown = self.typing_sound_interval

    def play_char_sound(self):
        if self.state == "typing_intro":
            if not self.open_sound_started:
                self.start_open_sequence()
                return
            if not self.use_normal_letters_after_open:
                return
            self.play_normal_letter_sound()
            return

        self.play_normal_letter_sound()

    def update_typing_block(self, dt):
        if self.block_done:
            return

        self.typing_accum += dt
        speed = self.current_speed()

        while self.typing_accum >= speed and not self.block_done:
            self.typing_accum -= speed

            if self.block_index >= len(self.current_block):
                self.block_done = True
                break

            line = self.current_block[self.block_index]
            text = line[0]

            if self.block_char < len(text):
                char = text[self.block_char]
                if not isinstance(self.visible_lines[-1], str):
                    self.visible_lines.append("")
                self.visible_lines[-1] += char
                self.block_char += 1
                if char != " ":
                    self.play_char_sound()
            else:
                self.finalize_current_line(line)
                self.block_index += 1
                self.block_char = 0
                if self.block_index < len(self.current_block):
                    self.visible_lines.append("")
                else:
                    self.block_done = True

    def push_result_line(self, text, color):
        if not self.visible_lines:
            self.visible_lines = [""]
        self.visible_lines[-1] = (text, color)
        self.result_phase += 1
        if self.result_phase < len(self.result_lines):
            self.visible_lines.append("")

    def set_state(self, new_state):
        self.state = new_state
        self.state_timer = 0.0

        if new_state == "typing_intro":
            self.visible_lines = [""]
            self.begin_block(self.intro_lines)
            self.typing_sound_cooldown = 0.0
            self.open_sound_started = False
            self.open_sound_elapsed = 0.0
            self.use_normal_letters_after_open = False
            self.input_line_active = False
            self.start_open_sequence()

        elif new_state == "name_entry":
            self.cursor_timer = 0.0
            self.cursor_on = True
            self.input_text = ""
            self.keyboard = KeyboardWindow()
            self.input_locked = False
            self.input_line_active = True
            if not self.visible_lines or self.visible_lines[-1] != "":
                self.visible_lines.append("")

        elif new_state == "submitting":
            self.input_locked = True
            self.input_line_active = False
            self.finish_waiting_to_start = True
            self.finish_has_started_playing = False
            play_finish()

        elif new_state == "typing_result":
            self.visible_lines = [""]
            self.result_phase = 0
            self.result_pause_timer = 0.0
            self.input_line_active = False

        elif new_state == "invalid":
            self.flash_timer = 0.35
            self.flash_alpha = 90
            self.input_locked = True
            self.input_line_active = False

        elif new_state == "done":
            self.cursor_on = False
            self.input_line_active = False

    def submit_username(self):
        if self.input_text == VALID_USERNAME:
            self.set_state("submitting")
        else:
            self.set_state("invalid")

    def activate_key(self):
        if self.input_locked:
            return

        label = self.keyboard.get_label()

        if label == "ESC":
            self.running = False
            return

        if label == "BACK":
            if self.input_text:
                self.input_text = self.input_text[:-1]
                play_enter()
            return

        if label == "ENTER":
            if self.input_text:
                self.submit_username()
            return

        if len(label) == 1 and label.isalpha():
            if len(self.input_text) < len(VALID_USERNAME):
                self.input_text += label
                play_enter()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.state not in ("name_entry", "done"):
                self.running = False
                return

            if self.state == "name_entry":
                if self.input_locked:
                    return

                if event.key == pygame.K_LEFT:
                    moved = self.keyboard.move(-1, 0)
                    if moved:
                        self.play_choose()
                elif event.key == pygame.K_RIGHT:
                    moved = self.keyboard.move(1, 0)
                    if moved:
                        self.play_choose()
                elif event.key == pygame.K_UP:
                    moved = self.keyboard.move(0, -1)
                    if moved:
                        self.play_choose()
                elif event.key == pygame.K_DOWN:
                    moved = self.keyboard.move(0, 1)
                    if moved:
                        self.play_choose()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.activate_key()

            elif self.state == "done":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.running = False

    def update_cursor(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= 0.45:
            self.cursor_timer = 0.0
            self.cursor_on = not self.cursor_on

    def draw_selector_box(self):
        alpha = 255 if (self.state_timer % 0.44) < 0.22 else 140
        overlay = pygame.Surface((self.selector_rect.w, self.selector_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (255, 255, 255, alpha), overlay.get_rect(), 4)
        screen.blit(overlay, self.selector_rect.topleft)

    def update(self, dt):
        self.state_timer += dt

        if self.typing_sound_cooldown > 0:
            self.typing_sound_cooldown -= dt
            if self.typing_sound_cooldown < 0:
                self.typing_sound_cooldown = 0.0

        if self.choose_sound_cooldown > 0:
            self.choose_sound_cooldown -= dt
            if self.choose_sound_cooldown < 0:
                self.choose_sound_cooldown = 0.0

        if self.flash_timer > 0:
            self.flash_timer -= dt
            if self.flash_timer <= 0:
                self.flash_timer = 0.0
                self.flash_alpha = 0
                if self.state == "invalid":
                    self.input_text = ""
                    self.set_state("name_entry")
                    return

        if self.state == "selector":
            if self.state_timer >= self.selector_duration:
                self.set_state("grow")

        elif self.state == "grow":
            if self.state_timer >= self.grow_duration:
                self.set_state("typing_intro")

        elif self.state == "typing_intro":
            self.update_open_sequence(dt)
            self.update_typing_block(dt)
            if self.block_done:
                self.set_state("name_entry")

        elif self.state == "name_entry":
            self.update_cursor(dt)
            self.keyboard.update(dt)

        elif self.state == "submitting":
            if self.finish_waiting_to_start:
                if finish_channel.get_busy():
                    self.finish_waiting_to_start = False
                    self.finish_has_started_playing = True
            elif self.finish_has_started_playing:
                if not finish_channel.get_busy():
                    self.finish_has_started_playing = False
                    self.set_state("typing_result")

        elif self.state == "typing_result":
            if self.result_pause_timer > 0:
                self.result_pause_timer -= dt
                if self.result_pause_timer < 0:
                    self.result_pause_timer = 0.0
            else:
                if self.result_phase < len(self.result_lines):
                    line = self.result_lines[self.result_phase]
                    self.push_result_line(line[0], line[1])
                    typing_channel.stop()
                    typing_channel.play(snd_letters)
                    self.result_pause_timer = self.result_line_sound_duration
                else:
                    self.set_state("done")

    def draw_program_lines(self, inner_rect):
        x_pos = inner_rect.x + 18
        y_pos = inner_rect.y + 10
        line_height = 50

        for idx, item in enumerate(self.visible_lines):
            if isinstance(item, str):
                text = item
                if self.input_line_active and idx == len(self.visible_lines) - 1:
                    text = ">" + self.input_text
                    if self.cursor_on and not self.input_locked:
                        text += "_"
                draw_shadow_text(screen, font_term, text, WHITE_DIRTY, SHADOW, (x_pos, y_pos))
            else:
                if len(item) == 2:
                    txt, color = item
                    draw_shadow_text(screen, font_term, txt, color, SHADOW, (x_pos, y_pos))
                elif len(item) == 4:
                    left_txt, left_col, right_txt, right_col = item
                    draw_shadow_text(screen, font_term, left_txt, left_col, SHADOW, (x_pos, y_pos))
                    right_w = font_term.size(right_txt)[0]
                    draw_shadow_text(screen, font_term, right_txt, right_col, SHADOW, (inner_rect.right - 18 - right_w, y_pos))
            y_pos += line_height

    def render(self):
        scene_base = build_scene_base()
        screen.blit(scene_base, (0, 0))

        if self.state == "selector":
            self.draw_selector_box()

        if self.state != "selector":
            rect = self.current_window_rect()
            inner_rect = draw_window(screen, rect, "PROGRAM(1:1)", scene_base=scene_base)
            if rect.w > 280 and rect.h > 150 and self.state != "grow":
                self.draw_program_lines(inner_rect)

        if self.state == "name_entry":
            self.keyboard.draw(screen)

        if self.flash_alpha > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, int(self.flash_alpha)))
            screen.blit(overlay, (0, 0))

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

        typing_channel.stop()
        ui_channel.stop()
        finish_channel.stop()


if __name__ == "__main__":
    try:
        App().run()
    finally:
        pygame.quit()
        sys.exit()