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

# Colours
BLACK    = (  0,   0,   0)
DARK_BG  = ( 18,  18,  30)
GRID_COL = ( 40,  40,  60)
WHITE    = (255, 255, 255)
GRAY     = (128, 128, 128)

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

    def draw(self, surface):
        surface.fill(DARK_BG, (0, 0, COLS * CELL, ROWS * CELL))
        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                if color:
                    self._draw_cell(surface, r, c, color)
        for r in range(ROWS + 1):
            pygame.draw.line(surface, GRID_COL, (0, r * CELL), (COLS * CELL, r * CELL))
        for c in range(COLS + 1):
            pygame.draw.line(surface, GRID_COL, (c * CELL, 0), (c * CELL, ROWS * CELL))

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

    def draw(self):
        self.screen.fill(BLACK)
        self.board.draw(self.screen)
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
                self.board._draw_cell(self.screen, r, c, self.current.color)

    def _draw_ghost(self):
        ghost_r = self._ghost_row()
        ghost_color = tuple(v // 4 for v in self.current.color)
        for dr, dc in TETROMINOES[self.current.kind][self.current.rot]:
            r = ghost_r + dr
            c = self.current.col + dc
            if r >= 0:
                x = c * CELL + 1
                y = r * CELL + 1
                size = CELL - 2
                pygame.draw.rect(self.screen, ghost_color,
                                 (x, y, size, size), border_radius=3)
                pygame.draw.rect(self.screen, self.current.color,
                                 (x, y, size, size), 1, border_radius=3)

    def _draw_mini_piece(self, kind, ox, oy):
        cells = TETROMINOES[kind][0]
        color = COLORS[kind]
        mini = CELL - 8
        for dr, dc in cells:
            x = ox + dc * mini + 2
            y = oy + dr * mini + 2
            pygame.draw.rect(self.screen, color, (x, y, mini - 2, mini - 2), border_radius=2)

    def _draw_sidebar(self):
        ox = COLS * CELL + 10
        w = SIDEBAR - 20
        pygame.draw.rect(self.screen, DARK_BG, (COLS * CELL, 0, SIDEBAR, SCREEN_H))
        pygame.draw.line(self.screen, GRID_COL, (COLS * CELL, 0), (COLS * CELL, SCREEN_H), 2)

        def label(text, y, color=GRAY):
            surf = self.font_sm.render(text, True, color)
            self.screen.blit(surf, (ox, y))

        def value(text, y, color=WHITE):
            surf = self.font_lg.render(text, True, color)
            self.screen.blit(surf, (ox, y))

        label("SCORE", 20)
        value(str(self.score), 40)
        label("LINES", 90)
        value(str(self.lines), 110)
        label("LEVEL", 160)
        value(str(self.level), 180)

        label("NEXT", 240)
        pygame.draw.rect(self.screen, GRID_COL, (ox, 265, w, 80), 1)
        if self.bag:
            self._draw_mini_piece(self.bag[0], ox + 10, 270)

        label("HOLD", 365)
        pygame.draw.rect(self.screen, GRID_COL, (ox, 390, w, 80), 1)
        if self.held:
            cells = TETROMINOES[self.held][0]
            mini = CELL - 8
            orig = COLORS[self.held]
            tinted = tuple(int(v * 0.5) for v in orig) if not self.can_hold else orig
            for dr, dc in cells:
                x = ox + 10 + dc * mini + 2
                y = 395 + dr * mini + 2
                pygame.draw.rect(self.screen, tinted, (x, y, mini - 2, mini - 2), border_radius=2)

        hints = [
            ("← →", "Move"),
            ("Up / X",     "Rotate CW"),
            ("Z",          "Rotate CCW"),
            ("↓",       "Soft drop"),
            ("Space",      "Hard drop"),
            ("C",          "Hold"),
            ("P",          "Pause"),
            ("R",          "Restart"),
        ]
        y = SCREEN_H - len(hints) * 22 - 10
        label("CONTROLS", y - 24)
        for hkey, action in hints:
            k_surf = self.font_sm.render(hkey, True, (100, 200, 255))
            a_surf = self.font_sm.render(action, True, GRAY)
            self.screen.blit(k_surf, (ox, y))
            self.screen.blit(a_surf, (ox + 72, y))
            y += 22

    def _draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        t = self.font_lg.render(title, True, WHITE)
        s = self.font_sm.render(subtitle, True, GRAY)
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
            self.update(dt)
            self.draw()


def main():
    Tetris().run()


if __name__ == "__main__":
    main()
