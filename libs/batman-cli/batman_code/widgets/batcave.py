"""Batcave loading screen for bat-code.

Batman ASCII portrait materializes from glitch noise.
Art cells settle smoothly via per-cell progress tracking.
Background noise uses lightweight fade-out entries for performance.

Press any key or pass --no-splash to skip.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

# ── Palette ───────────────────────────────────────────────────────────────────

BG = "#050008"

_GLITCH_COLORS = [
    "#ff0000", "#cc0000", "#ff2200",
    "#dd0000", "#ff1100", "#8b0000",
    "#ff3300", "#ff0000", "#aa0000",
    "#ffffff", "#ff0000", "#cc0000",
]

_BRIGHTNESS: dict[str, float] = {
    "@": 1.0,  "#": 0.95, "8": 0.90, "0": 0.85, "%": 0.80,
    "&": 0.75, "$": 0.70, "W": 0.68, "M": 0.66, "B": 0.64,
    "Q": 0.62, "N": 0.60, "H": 0.58, "D": 0.56, "R": 0.54,
    "U": 0.52, "m": 0.50, "w": 0.48, "b": 0.46, "d": 0.44,
    "q": 0.42, "p": 0.40, "h": 0.38, "k": 0.36, "n": 0.34,
    "*": 0.32, "+": 0.30, "=": 0.28, "~": 0.26, "^": 0.24,
    "o": 0.22, "c": 0.20, "r": 0.18, "!": 0.16, ";": 0.14,
    ":": 0.12, ",": 0.10, ".": 0.08, "`": 0.06, "'": 0.04,
}

def _locked_color(ch: str) -> str:
    b = _BRIGHTNESS.get(ch, 0.3)
    r = int(40 + b * 215)
    g = int(b * 18)
    bv = int(b * 8)
    return f"#{r:02x}{g:02x}{bv:02x}"

def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

_GLITCH = list("▓▒░╬╫╪┼╳※▪◆▄▀█@#$%&*!?/\\|+=~^<>{}[]0123456789")
_GLITCH_MID = list("+=~^*:;!?|/\\<>")   # medium density — transitional
_GLITCH_SPARSE = list(".:,;'` ")          # sparse — near-invisible before vanishing

# ── Batman ASCII art ──────────────────────────────────────────────────────────

BATMAN_ART = [
    r"                      .                .                      ",
    r"                     .:.              .:.                     ",
    r"                    .:;:.            .:;:.                    ",
    r"                   .:;;;;:.        .:;;;;:.                   ",
    r"                  .:;;;;;;;:.    .:;;;;;;;:.                  ",
    r"                .::;;;;;;;;;:::::;;;;;;;;;::.                 ",
    r"              .::;;;;;;;;;;;;;;;;;;;;;;;;;;;;::.              ",
    r"            .::;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;::.          ",
    r"          .::;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;:.       ",
    r"        .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.      ",
    r"       .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.     ",
    r"      .:;@@@@@@@     @@@@@@@@@@@@@@@@@     @@@@@@@@@@@;:.    ",
    r"      .:;@@@@@@@     @@@@@@@@@@@@@@@@@     @@@@@@@@@@@;:.    ",
    r"      .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.    ",
    r"       .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.      ",
    r"        .:;@@@@@@@                           @@@@@@@;:.      ",
    r"         .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.       ",
    r"          .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.        ",
    r"           .:;@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@;:.          ",
    r"             .::;;@@@@@@@@@@@@@@@@@@@@@@@@@@@;;::.           ",
    r"               .::;;@@@   @@@@@@@@@   @@@;;::.               ",
    r"                 .::;;@   @@@@@@@@@   @;;::.                 ",
    r"                    .:;@@@@@@@@@@@@@@@;:.                    ",
    r"                  .:;@@@@@@     @@@@@@@@@;:.                 ",
    r"                .:;@@@@@@@       @@@@@@@@@@@;:.              ",
    r"               .:;@@@@@@@         @@@@@@@@@@@;:.             ",
    r"             .:;@@@@@@@@@         @@@@@@@@@@@@@;:.           ",
    r"           .:;@@@@@@@@@@@         @@@@@@@@@@@@@@@;:.         ",
]

# ── Art cell — rich settling state ────────────────────────────────────────────

@dataclass
class _MatCell:
    final_ch:    str
    final_color: str
    delay:       int       # ticks of pure chaos before settling
    ticks_left:  int
    total_ticks: int
    char_tick:   int = 0
    cur_char:    str = ""

    @property
    def progress(self) -> float:
        if self.total_ticks <= 0:
            return 1.0
        return 1.0 - (self.ticks_left / self.total_ticks)


# ── Screen ────────────────────────────────────────────────────────────────────

class BatcaveScreen(Screen[None]):
    """Batman portrait materializes from glitch noise."""

    DEFAULT_CSS = """
    BatcaveScreen {
        background: #050008;
        overflow: hidden;
    }
    #bb-display {
        width: 100%;
        height: 100%;
    }
    """

    _TICK_S = 0.05  # 20 fps

    # Art cell timing — longer settle for smoother snap, tight finish window
    _ART_DELAY_MIN  = 18
    _ART_DELAY_MAX  = 28
    _ART_SETTLE_MIN = 38
    _ART_SETTLE_MAX = 50

    # Noise — lightweight background cells
    _NOISE_FILL     = 0.35   # fraction of screen covered by noise
    _NOISE_LIFE_MIN = 8      # min ticks before a noise cell fades
    _NOISE_LIFE_MAX = 35     # max ticks

    _HOLD_TICKS = 40

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash
        self._art_grid: dict[tuple, _MatCell] = {}  # art cells settling
        self._locked:   dict[tuple, tuple]    = {}  # (r,c) → (char, color)
        self._art_keys: set[tuple] = set()          # all art positions (for collision)
        # Noise: list of [row, col, ticks_remaining, char]
        self._noise: list[list] = []
        self._glitch_t = 0
        self._hold_t   = 0
        self._holding  = False
        self._timer    = None
        self._display: Static | None = None
        self._w = 0
        self._h = 0

    def compose(self) -> ComposeResult:
        self._display = Static("", id="bb-display")
        yield self._display

    def on_mount(self) -> None:
        if self._no_splash:
            self.dismiss()
            return
        self._w, self._h = self.app.size.width, self.app.size.height
        self._build(self._w, self._h)
        self._timer = self.set_interval(self._TICK_S, self._tick)

    def on_key(self) -> None:
        self._finish()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build(self, w: int, h: int) -> None:
        art    = BATMAN_ART
        art_h  = len(art)
        art_w  = max(len(line) for line in art)
        off_r  = max(0, (h - art_h) // 2)
        off_c  = max(0, (w - art_w) // 2)

        # Art cells — full settling behavior
        for r, line in enumerate(art):
            for c, ch in enumerate(line):
                if ch != " ":
                    key = (r + off_r, c + off_c)
                    total = random.randint(self._ART_SETTLE_MIN, self._ART_SETTLE_MAX)
                    delay = random.randint(self._ART_DELAY_MIN, self._ART_DELAY_MAX)
                    self._art_grid[key] = _MatCell(
                        final_ch=ch, final_color=_locked_color(ch),
                        delay=delay, ticks_left=total, total_ticks=total,
                        cur_char=random.choice(_GLITCH),
                    )
                    self._art_keys.add(key)

        # Noise cells — [row, col, life, char, total_life, tick_counter]
        noise_count = int(w * h * self._NOISE_FILL)
        for _ in range(noise_count):
            nr = random.randint(0, h - 1)
            nc = random.randint(0, w - 1)
            if (nr, nc) not in self._art_keys:
                life = random.randint(self._NOISE_LIFE_MIN, self._NOISE_LIFE_MAX)
                self._noise.append([nr, nc, life, random.choice(_GLITCH), life, 0])

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        self._glitch_t += 1

        if self._holding:
            self._hold_t += 1
            if self._hold_t >= self._HOLD_TICKS:
                self._finish()
            return

        # ── Advance art cells ────────────────────────────────────────────────
        newly_locked: list[tuple] = []

        for key, mat in self._art_grid.items():
            if mat.delay > 0:
                mat.delay -= 1
                mat.cur_char = random.choice(_GLITCH)
                continue

            mat.ticks_left -= 1
            mat.char_tick += 1
            p = mat.progress

            if p >= 0.95:
                mat.cur_char = mat.final_ch
            else:
                if p < 0.3:
                    change_every = 1
                elif p < 0.6:
                    change_every = 2
                elif p < 0.8:
                    change_every = 3
                else:
                    change_every = 5

                if mat.char_tick >= change_every:
                    mat.char_tick = 0
                    if random.random() < p * 0.85:
                        mat.cur_char = mat.final_ch
                    else:
                        mat.cur_char = random.choice(_GLITCH)

            if mat.ticks_left <= 0:
                newly_locked.append(key)

        for key in newly_locked:
            mat = self._art_grid.pop(key)
            self._locked[key] = (mat.final_ch, mat.final_color)

        # ── Advance noise cells — decelerate + transition to sparse chars ────
        surviving: list[list] = []
        for entry in self._noise:
            entry[2] -= 1   # decrement life
            entry[5] += 1   # increment tick counter
            if entry[2] > 0:
                # fade = 1.0 (fresh) → 0.0 (about to die)
                fade = entry[2] / entry[4]

                # Char cycling decelerates as fade decreases
                if fade > 0.6:
                    change_every = 1
                elif fade > 0.3:
                    change_every = 2
                else:
                    change_every = 4

                if entry[5] >= change_every:
                    entry[5] = 0
                    # Transition: heavy glitch → medium → sparse as life drains
                    if fade > 0.5:
                        entry[3] = random.choice(_GLITCH)
                    elif fade > 0.2:
                        entry[3] = random.choice(_GLITCH_MID)
                    else:
                        entry[3] = random.choice(_GLITCH_SPARSE)

                surviving.append(entry)
        self._noise = surviving

        # ── Check completion ──────────────────────────────────────────────────
        if not self._art_grid and not self._noise:
            self._holding = True

        self._draw(self._w, self._h)

    # ── Render ────────────────────────────────────────────────────────────────

    def _draw(self, w: int, h: int) -> None:
        glitch_color = _GLITCH_COLORS[self._glitch_t % len(_GLITCH_COLORS)]

        grid: list[list[tuple[str, str]]] = [[(" ", BG)] * w for _ in range(h)]

        # Locked art cells
        for (r, c), (ch, color) in self._locked.items():
            if 0 <= r < h and 0 <= c < w:
                grid[r][c] = (ch, color)

        # Noise cells — color dims smoothly per-cell as life drains
        for entry in self._noise:
            nr, nc, life, ch, total_life = entry[0], entry[1], entry[2], entry[3], entry[4]
            if 0 <= nr < h and 0 <= nc < w:
                fade = max(0.0, life / total_life)
                noise_base = _GLITCH_COLORS[
                    (self._glitch_t + nr + nc) % len(_GLITCH_COLORS)
                ]
                noise_color = _lerp_color(BG, noise_base, fade)
                grid[nr][nc] = (ch, noise_color)

        # Materializing art cells (rendered on top of noise)
        for (r, c), mat in self._art_grid.items():
            if 0 <= r < h and 0 <= c < w:
                if mat.delay > 0:
                    grid[r][c] = (mat.cur_char, glitch_color)
                else:
                    p = mat.progress
                    cell_color = _lerp_color(glitch_color, mat.final_color, p ** 1.5)
                    grid[r][c] = (mat.cur_char, cell_color)

        # Build Rich Text
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

        if self._display:
            self._display.update(text)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _finish(self) -> None:
        if self._timer:
            self._timer.stop()
        # Clean final render — only locked art on blank background
        if self._display:
            w, h = self._w, self._h
            grid: list[list[tuple[str, str]]] = [[(" ", BG)] * w for _ in range(h)]
            for (r, c), (ch, color) in self._locked.items():
                if 0 <= r < h and 0 <= c < w:
                    grid[r][c] = (ch, color)
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
            self._display.update(text)
        self.dismiss()
