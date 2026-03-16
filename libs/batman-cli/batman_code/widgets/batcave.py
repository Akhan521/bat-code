"""Batcave loading screen for bat-code.

"BAT CODE" block letters materialize from glitch noise on a pure black
background. Letters settle from dark-blue noise into multi-shade bat-gold
with a top-lit gradient. Press any key to skip, or --no-splash to bypass.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

# ── Helpers ───────────────────────────────────────────────────────────────────

def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

# ── Palette ───────────────────────────────────────────────────────────────────

BG = "#0a0a0f"
_PROMPT_COLOR = "#c49e14"
_GOLD_EDGE = "#f5c518"

_FACE_TOP    = "#ffe566"
_FACE_BOTTOM = "#9a7508"
_FACE_SHADES = [
    _lerp_color(_FACE_TOP, _FACE_BOTTOM, (i / 9) ** 1.4) for i in range(10)
]


def _gold_for_cell(ch: str, art_row: int) -> str:
    if ch == "█":
        idx = max(0, min(art_row, len(_FACE_SHADES) - 1))
        return _FACE_SHADES[idx]
    return _GOLD_EDGE

_GLITCH_COLORS = [
    "#1a3a5c", "#0d2440", "#1a3a5c",
    "#2d2d4e", "#1a1a3a", "#0d2440",
    "#3a4a6c", "#1a3a5c", "#0d2440",
    "#4a5a7c", "#1a3a5c", "#2d2d4e",
]

_GLITCH_HEAVY = list("▓░█@#%&")

# ── "BAT CODE" block-letter font (10 rows, 3D box-drawing) ──────────────────

_LETTERS: dict[str, list[str]] = {
    "B": [
        "████████╗ ",
        "██╔═════██╗",
        "██║     ██║",
        "██║     ██║",
        "████████╔╝",
        "██╔═════██╗",
        "██║     ██║",
        "██║     ██║",
        "████████╔╝",
        "╚═══════╝ ",
    ],
    "A": [
        "  ██████╗  ",
        " ██╔════██╗",
        "██╔╝    ╚██╗",
        "██║      ██║",
        "██████████║",
        "██╔══════██║",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "╚═╝      ╚═╝",
    ],
    "T": [
        "████████████╗",
        "╚════██╔════╝",
        "     ██║     ",
        "     ██║     ",
        "     ██║     ",
        "     ██║     ",
        "     ██║     ",
        "     ██║     ",
        "     ██║     ",
        "     ╚═╝     ",
    ],
    "C": [
        " ████████╗ ",
        "██╔═══════╝",
        "██║        ",
        "██║        ",
        "██║        ",
        "██║        ",
        "██║        ",
        "██║        ",
        "╚████████╗ ",
        " ╚════════╝",
    ],
    "O": [
        " ████████╗ ",
        "██╔══════██╗",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "╚████████╔╝",
        " ╚════════╝",
    ],
    "D": [
        "████████╗  ",
        "██╔═════██╗",
        "██║     ╚██╗",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "██║      ██║",
        "██║     ╔██╝",
        "████████╔╝ ",
        "╚═══════╝  ",
    ],
    "E": [
        "████████████╗",
        "██╔═════════╝",
        "██║          ",
        "██║          ",
        "████████╗    ",
        "██╔═════╝    ",
        "██║          ",
        "██║          ",
        "████████████╗",
        "╚═══════════╝",
    ],
}

_FONT_HEIGHT = 10
_LETTER_GAP = 2
_WORD_GAP = 5


def _compose_text(text: str) -> list[str]:
    words = text.split()
    for letter_rows in _LETTERS.values():
        max_w = max(len(row) for row in letter_rows)
        for i, row in enumerate(letter_rows):
            letter_rows[i] = row.ljust(max_w)
    word_blocks: list[list[str]] = []
    for word in words:
        letters = [_LETTERS[ch] for ch in word]
        spacer = " " * _LETTER_GAP
        block = [spacer.join(L[row] for L in letters) for row in range(_FONT_HEIGHT)]
        word_blocks.append(block)
    spacer = " " * _WORD_GAP
    return [spacer.join(wb[row] for wb in word_blocks) for row in range(_FONT_HEIGHT)]


BAT_CODE_ASCII = _compose_text("BAT CODE")

# ── Art cell ─────────────────────────────────────────────────────────────────

_COLOR_STEPS = 10


@dataclass
class _MatCell:
    final_ch:    str
    final_color: str
    delay:       int
    ticks_left:  int
    total_ticks: int
    color_steps: list[str] = field(default_factory=list)
    char_tick:   int = 0
    cur_char:    str = ""

    @property
    def progress(self) -> float:
        if self.total_ticks <= 0:
            return 1.0
        return 1.0 - (self.ticks_left / self.total_ticks)


# ── Screen ────────────────────────────────────────────────────────────────────

class BatcaveScreen(Screen[None]):
    """BAT CODE glitch splash screen."""

    DEFAULT_CSS = """
    BatcaveScreen {
        background: #0a0a0f;
        overflow: hidden;
    }
    #bb-display {
        width: 100%;
        height: 100%;
    }
    """

    _TICK_S = 0.08

    # Letter glitch timing
    _ART_DELAY_MIN  = 2
    _ART_DELAY_MAX  = 7
    _ART_SETTLE_MIN = 8
    _ART_SETTLE_MAX = 16
    _HOLD_TICKS     = 22   # ~1.8s

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash
        self._display: Static | None = None
        self._timer = None
        self._done = False
        self._w = 0
        self._h = 0

        # Phase state machine
        self._phase = "glitch"  # glitch → hold
        self._phase_tick = 0

        # Letter glitch state
        self._art_grid: dict[tuple, _MatCell] = {}
        self._art_off_r = 0
        self._art_h = 0
        self._base_grid: list[list[tuple[str, str]]] = []
        self._row_cache: list[list[tuple[str, str]]] = []
        self._dirty_rows: set[int] = set()
        self._row_art_count: dict[int, int] = {}

    def compose(self) -> ComposeResult:
        self._display = Static("", id="bb-display")
        yield self._display

    def on_mount(self) -> None:
        if self._no_splash:
            self.dismiss()
            return
        self._w, self._h = self.app.size.width, self.app.size.height
        self._build(self._w, self._h)
        self._draw_glitch()
        self._timer = self.set_interval(self._TICK_S, self._tick)

    def on_key(self) -> None:
        if self._done:
            return
        if self._phase == "glitch":
            self._skip_to_settled()
        elif self._phase == "hold":
            self._finish()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build(self, w: int, h: int) -> None:
        art = BAT_CODE_ASCII
        art_h = len(art)
        art_w = max(len(line) for line in art)
        off_r = max(0, (h - art_h) // 2)
        off_c = max(0, (w - art_w) // 2)

        self._art_off_r = off_r
        self._art_h = art_h

        for r, line in enumerate(art):
            for c, ch in enumerate(line):
                if ch != " ":
                    key = (r + off_r, c + off_c)
                    total = random.randint(self._ART_SETTLE_MIN, self._ART_SETTLE_MAX)
                    delay = random.randint(self._ART_DELAY_MIN, self._ART_DELAY_MAX)
                    final_color = _gold_for_cell(ch, r)
                    glitch_c = random.choice(_GLITCH_COLORS)
                    steps = [
                        _lerp_color(glitch_c, final_color, (i / (_COLOR_STEPS - 1)) ** 1.5)
                        for i in range(_COLOR_STEPS)
                    ]
                    self._art_grid[key] = _MatCell(
                        final_ch=ch, final_color=final_color,
                        delay=delay, ticks_left=total, total_ticks=total,
                        color_steps=steps,
                        cur_char=random.choice(_GLITCH_HEAVY),
                    )
                    row_idx = key[0]
                    self._dirty_rows.add(row_idx)
                    self._row_art_count[row_idx] = self._row_art_count.get(row_idx, 0) + 1

        self._base_grid = [[(" ", BG)] * w for _ in range(h)]
        self._row_cache = [self._build_row_segments(r) for r in range(h)]

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if self._done:
            return

        self._phase_tick += 1

        if self._phase == "glitch":
            self._tick_glitch()

        elif self._phase == "hold":
            if self._phase_tick >= self._HOLD_TICKS:
                self._finish()

    # ── Glitch tick ───────────────────────────────────────────────────────────

    def _tick_glitch(self) -> None:
        newly_locked: list[tuple] = []

        for key, mat in self._art_grid.items():
            if mat.delay > 0:
                mat.delay -= 1
                mat.cur_char = random.choice(_GLITCH_HEAVY)
                continue

            mat.ticks_left -= 1
            mat.char_tick += 1
            p = mat.progress

            if p >= 0.9:
                mat.cur_char = mat.final_ch
            elif p >= 0.6:
                if mat.char_tick >= 3:
                    mat.char_tick = 0
                    mat.cur_char = mat.final_ch if random.random() < 0.7 else random.choice(_GLITCH_HEAVY)
            elif p >= 0.3:
                if mat.char_tick >= 2:
                    mat.char_tick = 0
                    mat.cur_char = mat.final_ch if random.random() < p else random.choice(_GLITCH_HEAVY)
            else:
                mat.cur_char = random.choice(_GLITCH_HEAVY)

            if mat.ticks_left <= 0:
                newly_locked.append(key)

        for key in newly_locked:
            r, c = key
            mat = self._art_grid.pop(key)
            self._base_grid[r][c] = (mat.final_ch, mat.final_color)
            self._row_art_count[r] -= 1
            if self._row_art_count[r] <= 0:
                self._dirty_rows.discard(r)
                self._row_cache[r] = self._build_row_segments(r)

        if not self._art_grid:
            self._phase = "hold"
            self._phase_tick = 0

        self._draw_glitch()

    # ── Render ────────────────────────────────────────────────────────────────

    def _build_row_segments(self, row_idx: int) -> list[tuple[str, str]]:
        row = self._base_grid[row_idx]
        segments: list[tuple[str, str]] = []
        col = 0
        w = len(row)
        while col < w:
            ch, color = row[col]
            start = col
            while col < w and row[col][1] == color:
                col += 1
            segments.append(("".join(r[0] for r in row[start:col]), color))
        return segments

    def _draw_glitch(self) -> None:
        w, h = self._w, self._h

        # Build art cell overlay for dirty rows
        art_by_row: dict[int, list[tuple[int, str, str]]] = {}
        max_step = _COLOR_STEPS - 1
        for (r, c), mat in self._art_grid.items():
            if 0 <= r < h and 0 <= c < w:
                if mat.delay > 0:
                    color = mat.color_steps[0]
                else:
                    step = min(int(mat.progress * max_step), max_step)
                    color = mat.color_steps[step]
                art_by_row.setdefault(r, []).append((c, mat.cur_char, color))

        # Prompt during hold phase
        prompt_cells: list[tuple[int, str, str]] | None = None
        if self._phase == "hold":
            prompt = "Press any key to enter the Batcave..."
            prompt_r = self._art_off_r + self._art_h + 3
            if 0 <= prompt_r < h:
                prompt_c = max(0, (w - len(prompt)) // 2)
                prompt_cells = [
                    (prompt_c + i, ch, _PROMPT_COLOR)
                    for i, ch in enumerate(prompt)
                    if prompt_c + i < w
                ]

        # Build Rich Text row-by-row
        text = Text(overflow="fold", no_wrap=True)
        for r in range(h):
            row_arts = art_by_row.get(r)
            is_prompt_row = prompt_cells is not None and r == self._art_off_r + self._art_h + 3

            if row_arts or is_prompt_row or r in self._dirty_rows:
                row = self._base_grid[r][:]
                if row_arts:
                    for c, ch, color in row_arts:
                        row[c] = (ch, color)
                if is_prompt_row and prompt_cells:
                    for c, ch, color in prompt_cells:
                        row[c] = (ch, color)
                col = 0
                while col < w:
                    ch, color = row[col]
                    start = col
                    while col < w and row[col][1] == color:
                        col += 1
                    text.append("".join(cell[0] for cell in row[start:col]), style=color)
            else:
                for run, style in self._row_cache[r]:
                    text.append(run, style=style)
            text.append("\n")

        if self._display:
            self._display.update(text)

    # ── Skip / finish ─────────────────────────────────────────────────────────

    def _skip_to_settled(self) -> None:
        for (r, c), mat in self._art_grid.items():
            self._base_grid[r][c] = (mat.final_ch, mat.final_color)
        affected_rows = set(self._dirty_rows)
        self._art_grid.clear()
        self._dirty_rows.clear()
        self._row_art_count.clear()
        for r in affected_rows:
            self._row_cache[r] = self._build_row_segments(r)
        self._phase = "hold"
        self._phase_tick = 0
        self._draw_glitch()

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        if self._timer:
            self._timer.stop()
        self._art_grid.clear()
        self.call_after_refresh(self._deferred_dismiss)

    def _deferred_dismiss(self) -> None:
        self.dismiss()
