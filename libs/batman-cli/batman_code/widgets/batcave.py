"""Batman Beyond loading screen for bat-code.

Cyberpunk neon-alley animation:
  Phase rain   — rain streaks fall across a dark screen
  Phase alley  — perspective walls and neon signs flicker in
  Phase reveal — Batman Beyond silhouette materializes center
  Phase hold   — full scene with rain, neons, reflection, title text

Any keypress or --no-splash skips immediately.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

# ── Color palette ─────────────────────────────────────────────────────────────

BG          = "#0a0008"
RAIN_DIM    = "#1a1428"
RAIN_MID    = "#2a2a3a"
NEON_RED    = "#cc0033"
NEON_BRIGHT = "#ff2255"
NEON_MAG    = "#e0007a"
NEON_MAG_HI = "#ff2d7a"
NEON_TEAL   = "#00aacc"
WALL_DIM    = "#150508"
WALL_MID    = "#2a080f"
BAT_BODY    = "#0d0d0d"
BAT_SYMBOL  = "#cc0033"
BAT_SYM_HI  = "#ff0044"
GLOW_CORE   = "#440015"
GLOW_MID    = "#330011"

GLITCH_CHARS = "▓▒░╬╫╪┼╳※▪◆▄▀█"

# ── ASCII assets ──────────────────────────────────────────────────────────────

# Batman Beyond silhouette — slim suit, pointed ears, red chest symbol.
# Each entry: (line_string, is_symbol_row)
# The character '*' on a symbol row is rendered as the red bat symbol.
FIGURE_LINES: tuple[tuple[str, bool], ...] = (
    (r"   /\     /\   ", False),
    (r"  /  \   /  \  ", False),
    (r" / /\ \_/ /\ \ ", False),
    (r"| |   (_)   | |", False),
    (r" \ \  / \  / / ", False),
    (r"  \_\/   \/_/  ", False),
    (r"   /|     |\   ", False),
    (r"  / |  *  | \  ", True ),   # * = bat symbol, rendered in red
    (r" /  |     |  \ ", False),
    (r"    |     |    ", False),
    (r"    |     |    ", False),
    (r"     \   /     ", False),
    (r"      | |      ", False),
    (r"      | |      ", False),
    (r"     /   \     ", False),
)

# Left neon sign (crimson/magenta)
NEON_SIGN: tuple[str, ...] = (
    "╔═══╗",
    "║ G ║",
    "║ T ║",
    "║ M ║",
    "║   ║",
    "║ 2 ║",
    "║ 0 ║",
    "║ 4 ║",
    "╚═══╝",
)

# Right accent sign (teal)
TEAL_SIGN: tuple[str, ...] = (
    "┌──┐",
    "│NE│",
    "│ON│",
    "└──┘",
)

_RAIN_CHARS = ("│", "╎", "╷", "·")

# ── Grid helpers ──────────────────────────────────────────────────────────────

# Grid[row][col] = (char, color_hex)
Grid = list[list[tuple[str, str]]]


def _make_grid(w: int, h: int) -> Grid:
    return [[(" ", BG)] * w for _ in range(h)]


def _set(grid: Grid, row: int, col: int, char: str, color: str) -> None:
    if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
        grid[row][col] = (char, color)


def _grid_to_text(grid: Grid) -> Text:
    text = Text(overflow="fold", no_wrap=True)
    for row in grid:
        col = 0
        while col < len(row):
            ch, color = row[col]
            start = col
            while col < len(row) and row[col][1] == color:
                col += 1
            text.append("".join(r[0] for r in row[start:col]), style=color)
        text.append("\n")
    return text


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * max(0.0, min(1.0, t)))


def _lerp_color(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    return f"#{_lerp(r1,r2,t):02x}{_lerp(g1,g2,t):02x}{_lerp(b1,b2,t):02x}"


def _dim_color(c: str, factor: float) -> str:
    r = int(int(c[1:3], 16) * factor)
    g = int(int(c[3:5], 16) * factor)
    b = int(int(c[5:7], 16) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def _glitch_str(s: str, intensity: float) -> str:
    chars = list(s)
    for i, c in enumerate(chars):
        if c not in (" ", "*") and random.random() < intensity:
            chars[i] = random.choice(GLITCH_CHARS)
    return "".join(chars)


# ── Drop dataclass ─────────────────────────────────────────────────────────────

@dataclass
class _Drop:
    col: int
    row: float
    speed: float
    char: str


# ── Screen ────────────────────────────────────────────────────────────────────

class BatcaveScreen(Screen[None]):
    """Batman Beyond cyberpunk alley loading screen."""

    DEFAULT_CSS = """
    BatcaveScreen {
        background: #0a0008;
        overflow: hidden;
    }
    #bb-display {
        width: 100%;
        height: 100%;
    }
    """

    _TICK_S       = 0.06
    _RAIN_TICKS   = 18
    _ALLEY_TICKS  = 25
    _REVEAL_TICKS = 18
    _HOLD_TICKS   = 28

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash    = no_splash
        self._phase        = "rain"
        self._tick         = 0
        self._drops: list[_Drop] = []
        self._alley_p      = 0.0
        self._neon_on      = False
        self._neon_tick    = 0
        self._reveal_row   = 0
        self._glitch       = 1.0
        self._timer        = None
        self._display: Static | None = None

    def compose(self) -> ComposeResult:
        self._display = Static("", id="bb-display")
        yield self._display

    def on_mount(self) -> None:
        if self._no_splash:
            self.dismiss()
            return
        w = self.app.size.width
        h = self.app.size.height
        self._init_rain(w, h)
        self._timer = self.set_interval(self._TICK_S, self._tick_handler)

    def on_key(self) -> None:
        self._finish()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_rain(self, w: int, h: int) -> None:
        # Seed drops staggered across screen so it doesn't look like they all
        # start at the top simultaneously.
        step = max(1, w // 60)
        for col in range(0, w, step):
            self._drops.append(_Drop(
                col=col,
                row=float(random.randint(0, h - 1)),
                speed=random.uniform(0.35, 1.1),
                char=random.choice(_RAIN_CHARS),
            ))

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick_handler(self) -> None:
        self._tick += 1
        w, h = self.app.size.width, self.app.size.height

        if self._phase == "rain":
            if self._tick >= self._RAIN_TICKS:
                self._phase = "alley"
                self._tick = 0

        elif self._phase == "alley":
            self._alley_p = min(1.0, self._tick / self._ALLEY_TICKS)
            self._neon_tick += 1
            if self._neon_tick % 3 == 0:
                self._neon_on = not self._neon_on
            if self._tick >= self._ALLEY_TICKS:
                self._neon_on = True
                self._phase = "reveal"
                self._tick = 0
                self._glitch = 1.0

        elif self._phase == "reveal":
            p = self._tick / self._REVEAL_TICKS
            self._reveal_row = int(p * len(FIGURE_LINES))
            self._glitch = max(0.0, 1.0 - p * 1.5)
            self._neon_tick += 1
            if self._neon_tick % 4 == 0:
                self._neon_on = not self._neon_on
            if self._tick >= self._REVEAL_TICKS:
                self._reveal_row = len(FIGURE_LINES)
                self._glitch = 0.0
                self._phase = "hold"
                self._tick = 0

        elif self._phase == "hold":
            self._neon_tick += 1
            if self._neon_tick % 6 == 0:
                self._neon_on = not self._neon_on
            if self._tick >= self._HOLD_TICKS:
                self._finish()

        self._advance_rain(w, h)
        grid = self._render_frame(w, h)
        if self._display:
            self._display.update(_grid_to_text(grid))

    # ── Rain ──────────────────────────────────────────────────────────────────

    def _advance_rain(self, w: int, h: int) -> None:
        for drop in self._drops:
            drop.row += drop.speed
            if drop.row >= h:
                drop.row = 0.0
                drop.col = random.randint(0, max(0, w - 1))
                drop.char = random.choice(_RAIN_CHARS)
                drop.speed = random.uniform(0.35, 1.1)

    def _draw_rain(self, grid: Grid, h: int) -> None:
        for drop in self._drops:
            r, c = int(drop.row), drop.col
            trail = (
                (r,     drop.char, 0.85),
                (r - 1, "╷",       0.45),
                (r - 2, "·",       0.20),
                (r - 3, "·",       0.08),
            )
            for tr, ch, alpha in trail:
                color = _lerp_color(BG, RAIN_MID, alpha)
                _set(grid, tr, c, ch, color)

    # ── Alley ─────────────────────────────────────────────────────────────────

    def _draw_alley(self, grid: Grid, w: int, h: int, p: float) -> None:
        cx = w // 2
        vy = h // 3  # vanishing point row

        # Glow at vanishing point (atmospheric backlight)
        for dr in range(-4, 8):
            for dc in range(-12, 13):
                gr, gc = vy + dr, cx + dc
                dist = (abs(dc) / 12.0) * 0.7 + (abs(dr) / 8.0) * 0.3
                intensity = p * max(0.0, 1.0 - dist)
                glow = _lerp_color(BG, GLOW_CORE, intensity * 0.9)
                if 0 <= gr < h and 0 <= gc < w and grid[gr][gc][0] == " ":
                    _set(grid, gr, gc, " ", glow)

        # Perspective walls
        for row in range(vy, h):
            t = (row - vy) / max(1, h - vy - 1)
            left_col  = max(0, int(cx - t * cx * 0.88))
            right_col = min(w - 1, int(cx + t * cx * 0.88))
            wall_c = _lerp_color(BG, WALL_MID, p * min(1.0, t * 1.4))

            ch_l = "\\" if (row % 2 == 0) else "│"
            ch_r = "/"  if (row % 2 == 0) else "│"
            _set(grid, row, left_col,  ch_l, wall_c)
            _set(grid, row, right_col, ch_r, wall_c)

            # Fill wall faces with dim color
            fill_c = _lerp_color(BG, WALL_DIM, p * 0.6)
            for c in range(0, left_col):
                if grid[row][c][0] == " ":
                    _set(grid, row, c, " ", fill_c)
            for c in range(right_col + 1, w):
                if grid[row][c][0] == " ":
                    _set(grid, row, c, " ", fill_c)

        # Floor
        if p > 0.3:
            floor_p = (p - 0.3) / 0.7
            for c in range(w):
                dist = abs(c - cx) / max(1, cx)
                fc = _lerp_color(BG, "#200808", floor_p * (1.0 - dist * 0.6))
                _set(grid, h - 1, c, "─", fc)

        # Neon signs
        self._draw_neon_signs(grid, w, h, p)

    def _draw_neon_signs(self, grid: Grid, w: int, h: int, p: float) -> None:
        if p < 0.2:
            return
        sign_p = (p - 0.2) / 0.8

        # Flicker: bright or dim
        neon_c = NEON_MAG_HI if self._neon_on else _dim_color(NEON_MAG, 0.18)
        teal_c = NEON_TEAL   if self._neon_on else _dim_color(NEON_TEAL, 0.15)

        # Left neon sign
        sign_row = h // 4
        sign_col = 2
        rows_show = max(1, int(sign_p * len(NEON_SIGN)))
        for i, line in enumerate(NEON_SIGN[:rows_show]):
            for j, ch in enumerate(line):
                _set(grid, sign_row + i, sign_col + j, ch, neon_c)

        # Right teal sign
        tsign_row = h // 3
        tsign_col = max(0, w - 6)
        rows_show_t = max(1, int(sign_p * len(TEAL_SIGN)))
        for i, line in enumerate(TEAL_SIGN[:rows_show_t]):
            for j, ch in enumerate(line):
                c = tsign_col + j
                if 0 <= c < w:
                    _set(grid, tsign_row + i, c, ch, teal_c)

    # ── Silhouette ────────────────────────────────────────────────────────────

    def _draw_figure(self, grid: Grid, w: int, h: int) -> None:
        if self._reveal_row == 0:
            return

        fig_w   = max(len(line) for line, _ in FIGURE_LINES)
        fig_col = (w - fig_w) // 2
        fig_row = h // 3

        # Radial backlight glow behind figure
        glow_p = min(1.0, self._reveal_row / max(1, len(FIGURE_LINES)))
        cx = w // 2
        for dr in range(-1, len(FIGURE_LINES) + 1):
            gy = fig_row + dr
            for dc in range(-(fig_w // 2) - 5, fig_w // 2 + 6):
                gc = cx + dc
                dist = abs(dc) / (fig_w // 2 + 5)
                if dist < 1.0 and 0 <= gy < h and 0 <= gc < w:
                    if grid[gy][gc][0] == " ":
                        g = _lerp_color(BG, GLOW_CORE, glow_p * (1.0 - dist) * 0.65)
                        _set(grid, gy, gc, " ", g)

        # Silhouette rows
        pulse = (self._tick % 3 < 2)
        sym_color = BAT_SYM_HI if pulse else BAT_SYMBOL

        for i, (line, is_sym) in enumerate(FIGURE_LINES[:self._reveal_row]):
            row = fig_row + i
            is_last = (i == self._reveal_row - 1)
            rendered = (
                _glitch_str(line, self._glitch * 0.55)
                if is_last and self._glitch > 0.05
                else line
            )
            for j, ch in enumerate(rendered):
                col = fig_col + j
                if ch == " ":
                    continue
                if is_sym and ch == "*":
                    _set(grid, row, col, "✦", sym_color)
                elif is_sym:
                    _set(grid, row, col, ch, NEON_RED)
                else:
                    _set(grid, row, col, ch, BAT_BODY)

    # ── Reflection ────────────────────────────────────────────────────────────

    def _draw_reflection(self, grid: Grid, w: int, h: int) -> None:
        fig_w   = max(len(line) for line, _ in FIGURE_LINES)
        fig_col = (w - fig_w) // 2
        fig_row = h // 3
        horizon = fig_row + len(FIGURE_LINES)

        # Horizon line
        for c in range(w):
            dist = abs(c - w // 2) / max(1, w // 2)
            hc = _lerp_color(WALL_MID, BG, dist * 0.7)
            _set(grid, horizon, c, "─", hc)

        # Mirrored figure below horizon
        total = len(FIGURE_LINES)
        for i, (line, is_sym) in enumerate(FIGURE_LINES):
            refl_row = horizon + 1 + (total - 1 - i)
            if refl_row >= h:
                continue
            for j, ch in enumerate(line):
                col = fig_col + j
                if ch == " " or not (0 <= col < w):
                    continue
                # Dim + slight blue tint for wet reflection
                if is_sym and ch == "*":
                    _set(grid, refl_row, col, "·", _dim_color(NEON_RED, 0.15))
                else:
                    rv = int(0x0d * 0.25)
                    bv = int(0x1a * 0.35)
                    _set(grid, refl_row, col, ch, f"#{rv:02x}{rv:02x}{bv:02x}")

    # ── Title ─────────────────────────────────────────────────────────────────

    def _draw_title(self, grid: Grid, w: int, h: int) -> None:
        title    = "B A T M A N   B E Y O N D"
        subtitle = "I N I T I A L I Z I N G . . ."
        hint     = "press any key to continue"

        tc = (w - len(title))    // 2
        sc = (w - len(subtitle)) // 2
        hc = (w - len(hint))     // 2

        title_row = max(1, h // 3 - 3)
        if title_row > 0:
            for j, ch in enumerate(title):
                _set(grid, title_row,     tc + j, ch, NEON_MAG_HI)
            for j, ch in enumerate(subtitle):
                _set(grid, title_row + 1, sc + j, ch, _dim_color(NEON_RED, 0.75))

        # Skip hint at very bottom
        for j, ch in enumerate(hint):
            _set(grid, h - 1, hc + j, ch, _dim_color(WALL_MID, 1.5))

    # ── Frame ─────────────────────────────────────────────────────────────────

    def _render_frame(self, w: int, h: int) -> Grid:
        grid = _make_grid(w, h)

        self._draw_rain(grid, h)

        if self._phase in ("alley", "reveal", "hold"):
            self._draw_alley(grid, w, h, self._alley_p)

        if self._phase in ("reveal", "hold"):
            self._draw_figure(grid, w, h)

        if self._phase == "hold":
            self._draw_reflection(grid, w, h)
            self._draw_title(grid, w, h)

        return grid

    # ── Finish ────────────────────────────────────────────────────────────────

    def _finish(self) -> None:
        if self._timer:
            self._timer.stop()
        self.dismiss()
