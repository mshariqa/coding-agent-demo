import pygame
import random
import sys

# ── Constants ─────────────────────────────────────────────────────────────────
COLS, ROWS = 10, 20
CELL = 32
SIDEBAR = 200

SCREEN_W = COLS * CELL + SIDEBAR
SCREEN_H = ROWS * CELL

FPS = 60
LOCK_DELAY = 500          # ms before a landed piece locks
LINES_PER_LEVEL = 10
CONTROL_LINE_HEIGHT = 15

# Colours
BLACK    = (  0,   0,   0)
DARK_BG  = ( 18,  18,  30)
GRID_COL = ( 40,  40,  60)
WHITE    = (255, 255, 255)
GRAY     = (128, 128, 128)
LIGHT_BG = (245, 245, 250)
LIGHT_GRID_COL = (180, 180, 200)
DARK_TEXT = (35, 35, 45)
BLUE_HINT = (60, 110, 200)

COLORS = {
    "I": (  0, 240, 240),
    "O": (240, 240,   0),
    "T": (160,   0, 240),
    "S": (  0, 240,   0),
    "Z": (240,   0,   0),
    "J": (  0,   0, 240),
    "L": (240, 160,   0),
}

# Tetrominoes: list of rotation states, each state a list of (row, col) offsets
TETROMINOES = {
    "I": [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(2,0),(2,1),(2,2),(2,3)],
        [(0,1),(1,1),(2,1),(3,1)],
    ],
    "O": [
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    "T": [
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(1,2),(2,1)],
        [(0,1),(1,0),(1,1),(2,1)],
    ],
    "S": [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,1),(1,2),(2,0),(2,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    "Z": [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,2),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    "J": [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,1),(0,2),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    "L": [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(1,2),(2,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}

# SRS wall-kick offsets for J/L/S/T/Z and I pieces
KICKS_JLSTZ = {
    (0,1): [(-1,0),(-1, 1),(0,-2),(-1,-2)],
    (1,0): [( 1,0),( 1,-1),(0, 2),( 1, 2)],
    (1,2): [( 1,0),( 1,-1),(0, 2),( 1, 2)],
    (2,1): [(-1,0),(-1, 1),(0,-2),(-1,-2)],
    (2,3): [(-1,0),(-1, 1),(0,-2),(-1,-2)],
    (3,2): [( 1,0),( 1,-1),(0, 2),( 1, 2)],
    (3,0): [( 1,0),( 1,-1),(0, 2),( 1, 2)],
    (0,3): [(-1,0),(-1, 1),(0,-2),(-1,-2)],
}
KICKS_I = {
    (0,1): [(0,-1),(0, 2),(-1,-1),(2, 2)],
    (1,0): [(0, 1),(0,-2),( 1, 1),(-2,-2)],
    (1,2): [(0,-2),(0, 1),( 2,-2),(-1, 1)],
    (2,1): [(0, 2),(0,-1),(-2, 2),( 1,-1)],
    (2,3): [(0, 1),(0,-2),(-1, 1),(2, 2)],
    (3,2): [(0,-1),(0, 2),( 1,-1),(-2, 2)],
    (3,0): [(0, 2),(0,-1),(-2,-2),(1,-1)],
    (0,3): [(0,-2),(0, 1),( 2,-1),(-1, 2)],
}

SCORE_TABLE = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

CONTROL_HINTS = [
    ("← →", "Move"),
    ("Up / X", "Rotate CW"),
    ("Z", "Rotate CCW"),
    ("↓", "Soft drop"),
    ("Space", "Hard drop"),
    ("C", "Hold"),
    ("T", "Theme"),
    ("P", "Pause"),
    ("R", "Restart"),
]


def _relative_luminance(color):
    def channel(v):
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = color
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(a, b):
    la, lb = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def _blend_color(color, target, amount):
    return tuple(int(color[i] + (target[i] - color[i]) * amount) for i in range(3))


# ── Board ──────────────────────────────────────────────────────────────────────
class Board:
    def __init__(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]

    def is_valid(self, cells):
        for r, c in cells:
            if c < 0 or c >= COLS or r >= ROWS:
                return False
            if r >= 0 and self.grid[r][c] is not None:
                return False
        return True

    def lock(self, cells, color):
        for r, c in cells:
            if r >= 0:
                self.grid[r][c] = color

    def clear_lines(self):
        full = [r for r in range(ROWS) if all(self.grid[r])]
        for r in full:
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        return len(full)

    def draw(self, surface, bg_color=DARK_BG, grid_color=GRID_COL, color_transform=None):
        transform = color_transform or (lambda color: color)
        surface.fill(bg_color, (0, 0, COLS * CELL, ROWS * CELL))
        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                if color:
                    self._draw_cell(surface, r, c, transform(color))
        for r in range(ROWS + 1):
            pygame.draw.line(surface, grid_color, (0, r * CELL), (COLS * CELL, r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surface, grid_color, (c * CELL, 0), (c * CELL, ROWS * CELL))

    def _draw_cell(self, surface, r, c, color, ox=0, oy=0):
        x = ox + c * CELL + 1
        y = oy + r * CELL + 1
        size = CELL - 2
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(surface, color, rect, border_radius=3)
        highlight = tuple(min(255, v + 80) for v in color)
        pygame.draw.line(surface, highlight, (x, y), (x + size - 1, y), 2)
        pygame.draw.line(surface, highlight, (x, y), (x, y + size - 1), 2)


# ── Piece ──────────────────────────────────────────────────────────────────────
class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.color = COLORS[kind]
        self.rot = 0
        self.row = -1
        self.col = COLS // 2 - 2

    def cells(self, row=None, col=None, rot=None):
        r = self.row if row is None else row
        c = self.col if col is None else col
        rotation = self.rot if rot is None else rot
        return [(r + dr, c + dc) for dr, dc in TETROMINOES[self.kind][rotation]]

    def num_rotations(self):
        return len(TETROMINOES[self.kind])


# ── Game ───────────────────────────────────────────────────────────────────────
class Tetris:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 18)
        self.font_xs = pygame.font.SysFont("monospace", 14)
        self.dark_mode = True
        self.theme_button_rect = None
        self._new_game()

    def _new_game(self):
        self.board = Board()
        self.bag = []
        self.current = self._next_piece()
        self.held = None
        self.can_hold = True
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.fall_interval = self._fall_speed()
        self.fall_timer = 0
        self.lock_timer = None
        self.down_held = False

    def _theme_colors(self):
        if self.dark_mode:
            return {
                "board_bg": DARK_BG,
                "sidebar_bg": DARK_BG,
                "grid": GRID_COL,
                "text": WHITE,
                "label": GRAY,
                "hint": (100, 200, 255),
                "button_bg": (35, 35, 55),
                "button_text": WHITE,
                "overlay_bg": (0, 0, 0, 160),
            }
        return {
            "board_bg": LIGHT_BG,
            "sidebar_bg": (235, 235, 245),
            "grid": LIGHT_GRID_COL,
            "text": DARK_TEXT,
            "label": (90, 90, 115),
            "hint": BLUE_HINT,
            "button_bg": (210, 215, 235),
            "button_text": DARK_TEXT,
            "overlay_bg": (255, 255, 255, 150),
        }

    def _high_contrast_color(self, color):
        target_bg = self._theme_colors()["board_bg"]
        adjusted = color
        target = BLACK if _relative_luminance(target_bg) > 0.45 else WHITE
        for _ in range(10):
            if _contrast_ratio(adjusted, target_bg) >= 4.5:
                break
            adjusted = _blend_color(adjusted, target, 0.2)
        return adjusted

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode

    def _refill_bag(self):
        pieces = list(TETROMINOES.keys())
        random.shuffle(pieces)
        self.bag.extend(pieces)

    def _next_piece(self):
        if len(self.bag) < 7:
            self._refill_bag()
        return Piece(self.bag.pop(0))

    def _fall_speed(self):
        return 1000 * (0.8 ** (self.level - 1))

    def _hold(self):
        if not self.can_hold:
            return
        if self.held is None:
            self.held = self.current.kind
            self.current = self._next_piece()
        else:
            self.held, self.current = self.current.kind, Piece(self.held)
        self.can_hold = False
        self.lock_timer = None

    def _move(self, dr, dc):
        nr, nc = self.current.row + dr, self.current.col + dc
        if self.board.is_valid(self.current.cells(nr, nc)):
            self.current.row, self.current.col = nr, nc
            if dr > 0:
                self.lock_timer = None
            return True
        return False

    def _rotate(self, direction):
        old_rot = self.current.rot
        new_rot = (old_rot + direction) % self.current.num_rotations()
        if self.board.is_valid(self.current.cells(rot=new_rot)):
            self.current.rot = new_rot
            self.lock_timer = None
            return
        kicks = KICKS_I if self.current.kind == "I" else KICKS_JLSTZ
        key = (old_rot, new_rot)
        for dr, dc in kicks.get(key, []):
            nr = self.current.row + dr
            nc = self.current.col + dc
            if self.board.is_valid(self.current.cells(nr, nc, new_rot)):
                self.current.row, self.current.col = nr, nc
                self.current.rot = new_rot
                self.lock_timer = None
                return

    def _hard_drop(self):
        while self._move(1, 0):
            self.score += 2
        self._lock_piece()

    def _ghost_row(self):
        r = self.current.row
        while self.board.is_valid(self.current.cells(r + 1, self.current.col)):
            r += 1
        return r

    def _lock_piece(self):
        self.board.lock(self.current.cells(), self.current.color)
        cleared = self.board.clear_lines()
        self.score += SCORE_TABLE.get(cleared, 0) * self.level
        self.lines += cleared
        self.level = self.lines // LINES_PER_LEVEL + 1
        self.fall_interval = self._fall_speed()
        self.current = self._next_piece()
        self.can_hold = True
        self.lock_timer = None
        if not self.board.is_valid(self.current.cells()):
            self.game_over = True

    def update(self, dt):
        if self.game_over or self.paused:
            return
        landed = not self.board.is_valid(self.current.cells(self.current.row + 1, self.current.col))
        if landed:
            if self.lock_timer is None:
                self.lock_timer = 0
            else:
                self.lock_timer += dt
                if self.lock_timer >= LOCK_DELAY:
                    self._lock_piece()
                    return
        else:
            self.lock_timer = None
            self.fall_timer += dt
            # Fall faster when Down key is held
            effective_interval = self.fall_interval // 10 if self.down_held else self.fall_interval
            if self.fall_timer >= effective_interval:
                self.fall_timer -= effective_interval
                if self._move(1, 0) and self.down_held:
                    self.score += 1

    def handle_keydown(self, key):
        if key == pygame.K_r:
            self._new_game()
            return
        if key == pygame.K_t:
            self._toggle_theme()
            return
        if self.game_over:
            return
        if key == pygame.K_p:
            self.paused = not self.paused
            return
        if self.paused:
            return
        if key == pygame.K_LEFT:
            self._move(0, -1)
        elif key == pygame.K_RIGHT:
            self._move(0, 1)
        elif key == pygame.K_DOWN:
            self.down_held = True
            if self._move(1, 0):
                self.score += 1
        elif key == pygame.K_UP or key == pygame.K_x:
            self._rotate(1)
        elif key == pygame.K_z:
            self._rotate(-1)
        elif key == pygame.K_SPACE:
            self._hard_drop()
        elif key == pygame.K_c:
            self._hold()

    def handle_keyup(self, key):
        if key == pygame.K_DOWN:
            self.down_held = False

    def handle_mouse_down(self, pos):
        if self.theme_button_rect and self.theme_button_rect.collidepoint(pos):
            self._toggle_theme()

    def draw(self):
        self.screen.fill(BLACK)
        theme = self._theme_colors()
        self.board.draw(
            self.screen,
            bg_color=theme["board_bg"],
            grid_color=theme["grid"],
            color_transform=self._high_contrast_color,
        )
        self._draw_ghost()
        self._draw_current()
        self._draw_sidebar()
        if self.game_over:
            self._draw_overlay("GAME OVER", "Press R to restart")
        elif self.paused:
            self._draw_overlay("PAUSED", "Press P to resume")
        pygame.display.flip()

    def _draw_current(self):
        for r, c in self.current.cells():
            if r >= 0:
                self.board._draw_cell(self.screen, r, c, self._high_contrast_color(self.current.color))

    def _draw_ghost(self):
        theme = self._theme_colors()
        ghost_r = self._ghost_row()
        block_color = self._high_contrast_color(self.current.color)
        ghost_color = _blend_color(block_color, theme["board_bg"], 0.65)
        for dr, dc in TETROMINOES[self.current.kind][self.current.rot]:
            r = ghost_r + dr
            c = self.current.col + dc
            if r >= 0:
                x = c * CELL + 1
                y = r * CELL + 1
                size = CELL - 2
                pygame.draw.rect(self.screen, ghost_color,
                                 (x, y, size, size), border_radius=3)
                pygame.draw.rect(self.screen, block_color,
                                 (x, y, size, size), 1, border_radius=3)

    def _draw_mini_piece(self, kind, ox, oy):
        cells = TETROMINOES[kind][0]
        color = self._high_contrast_color(COLORS[kind])
        mini = CELL - 8
        for dr, dc in cells:
            x = ox + dc * mini + 2
            y = oy + dr * mini + 2
            pygame.draw.rect(self.screen, color, (x, y, mini - 2, mini - 2), border_radius=2)

    def _sidebar_layout(self):
        ox = COLS * CELL + 10
        w = SIDEBAR - 20
        hold_box = (ox, 390, w, 80)
        controls_label_y = hold_box[1] + hold_box[3] + 8
        return {
            "ox": ox,
            "w": w,
            "theme_button_box": (ox, 205, w, 30),
            "next_box": (ox, 265, w, 80),
            "hold_box": hold_box,
            "controls_label_y": controls_label_y,
            "controls_y": controls_label_y + 20,
            "control_line_height": CONTROL_LINE_HEIGHT,
            "control_key_right": ox + 58,
            "control_action_x": ox + 72,
        }

    def _draw_sidebar(self):
        theme = self._theme_colors()
        layout = self._sidebar_layout()
        ox = layout["ox"]
        w = layout["w"]
        pygame.draw.rect(self.screen, theme["sidebar_bg"], (COLS * CELL, 0, SIDEBAR, SCREEN_H))
        pygame.draw.line(self.screen, theme["grid"], (COLS * CELL, 0), (COLS * CELL, SCREEN_H), 2)

        def label(text, y, color=None):
            draw_color = theme["label"] if color is None else color
            surf = self.font_sm.render(text, True, draw_color)
            self.screen.blit(surf, (ox, y))

        def value(text, y, color=None):
            draw_color = theme["text"] if color is None else color
            surf = self.font_lg.render(text, True, draw_color)
            self.screen.blit(surf, (ox, y))

        label("SCORE", 20)
        value(str(self.score), 40)
        label("LINES", 90)
        value(str(self.lines), 110)
        label("LEVEL", 160)
        value(str(self.level), 180)

        self.theme_button_rect = pygame.Rect(*layout["theme_button_box"])
        pygame.draw.rect(self.screen, theme["button_bg"], self.theme_button_rect, border_radius=4)
        pygame.draw.rect(self.screen, theme["grid"], self.theme_button_rect, 1, border_radius=4)
        mode_text = "Dark mode" if self.dark_mode else "Light mode"
        btn_surf = self.font_sm.render(f"Theme: {mode_text}", True, theme["button_text"])
        self.screen.blit(btn_surf, btn_surf.get_rect(center=self.theme_button_rect.center))

        label("NEXT", 240)
        pygame.draw.rect(self.screen, theme["grid"], layout["next_box"], 1)
        if self.bag:
            self._draw_mini_piece(self.bag[0], ox + 10, 270)

        label("HOLD", 365)
        pygame.draw.rect(self.screen, theme["grid"], layout["hold_box"], 1)
        if self.held:
            cells = TETROMINOES[self.held][0]
            mini = CELL - 8
            orig = self._high_contrast_color(COLORS[self.held])
            tinted = tuple(int(v * 0.5) for v in orig) if not self.can_hold else orig
            for dr, dc in cells:
                x = ox + 10 + dc * mini + 2
                y = 395 + dr * mini + 2
                pygame.draw.rect(self.screen, tinted, (x, y, mini - 2, mini - 2), border_radius=2)

        label("CONTROLS", layout["controls_label_y"])
        y = layout["controls_y"]
        for hkey, action in CONTROL_HINTS:
            k_surf = self.font_xs.render(hkey, True, theme["hint"])
            a_surf = self.font_xs.render(action, True, theme["label"])
            self.screen.blit(k_surf, k_surf.get_rect(topright=(layout["control_key_right"], y)))
            self.screen.blit(a_surf, (layout["control_action_x"], y))
            y += layout["control_line_height"]

    def _draw_overlay(self, title, subtitle):
        theme = self._theme_colors()
        overlay = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        overlay.fill(theme["overlay_bg"])
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render(title, True, theme["text"])
        s = self.font_sm.render(subtitle, True, theme["label"])
        cx = COLS * CELL // 2
        self.screen.blit(t, t.get_rect(center=(cx, ROWS * CELL // 2 - 20)))
        self.screen.blit(s, s.get_rect(center=(cx, ROWS * CELL // 2 + 20)))

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.handle_keyup(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_mouse_down(event.pos)
            self.update(dt)
            self.draw()


def main():
    Tetris().run()


if __name__ == "__main__":
    main()
