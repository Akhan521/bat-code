"""Batcave loading screen for bat-code.

"BAT CODE" block-letter text materializes from glitch noise.
Only cells within the letter shapes glitch — the rest of the
screen stays black.  Letters settle from dark-blue noise into
bright bat-gold.

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

BG = "#0a0a0f"
_FINAL_GOLD = "#f5c518"
_PROMPT_COLOR = "#c49e14"

_GLITCH_COLORS = [
    "#1a3a5c", "#0d2440", "#1a3a5c",
    "#2d2d4e", "#1a1a3a", "#0d2440",
    "#3a4a6c", "#1a3a5c", "#0d2440",
    "#4a5a7c", "#1a3a5c", "#2d2d4e",
]

def _lerp_color(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

# Glyph set for glitch noise within letters
_GLITCH_HEAVY = list("▓▒░╬╫╪┼╳※▪◆▄▀█@#$%&")

# ── "BAT CODE" block-letter ASCII art ────────────────────────────────────────

BAT_CODE_ASCII = [
    "██████╗   █████╗ ████████╗     ██████╗  ██████╗ ██████╗ ███████╗",
    "██╔══██╗ ██╔══██╗╚══██╔══╝    ██╔════╝ ██╔═══██╗██╔══██╗██╔════╝",
    "██████╔╝ ███████║   ██║       ██║      ██║   ██║██║  ██║█████╗  ",
    "██╔══██╗ ██╔══██║   ██║       ██║      ██║   ██║██║  ██║██╔══╝  ",
    "██████╔╝ ██║  ██║   ██║       ╚██████╗ ╚██████╔╝██████╔╝███████╗",
    "╚═════╝  ╚═╝  ╚═╝   ╚═╝        ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝",
]

# ── Batman portrait (kept for future Phase 2 multi-phase splash) ─────────────
# BATMAN_ART = [
#     r"                      .                .                      ",
#     r"                     .:.              .:.                     ",
#     ... (portrait data preserved in git history)
# ]

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
    """'BAT CODE' block letters materialize from glitch noise."""

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

    _TICK_S = 0.06  # ~17 fps

    # Art cell timing
    _ART_DELAY_MIN  = 5
    _ART_DELAY_MAX  = 20
    _ART_SETTLE_MIN = 20
    _ART_SETTLE_MAX = 35

    _HOLD_TICKS = 25  # ~1.5s hold before auto-dismiss

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash
        self._art_grid: dict[tuple, _MatCell] = {}
        self._locked:   dict[tuple, tuple]    = {}
        self._art_keys: set[tuple] = set()
        self._glitch_t = 0
        self._hold_t   = 0
        self._holding  = False
        self._done     = False
        self._timer    = None
        self._display: Static | None = None
        self._w = 0
        self._h = 0
        self._art_off_r = 0
        self._art_h = 0

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
        if self._done:
            return
        if self._holding:
            self._finish()
        else:
            self._skip_to_settled()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build(self, w: int, h: int) -> None:
        art    = BAT_CODE_ASCII
        art_h  = len(art)
        art_w  = max(len(line) for line in art)
        off_r  = max(0, (h - art_h) // 2)
        off_c  = max(0, (w - art_w) // 2)

        self._art_off_r = off_r
        self._art_h = art_h

        for r, line in enumerate(art):
            for c, ch in enumerate(line):
                if ch != " ":
                    key = (r + off_r, c + off_c)
                    total = random.randint(self._ART_SETTLE_MIN, self._ART_SETTLE_MAX)
                    delay = random.randint(self._ART_DELAY_MIN, self._ART_DELAY_MAX)
                    self._art_grid[key] = _MatCell(
                        final_ch=ch, final_color=_FINAL_GOLD,
                        delay=delay, ticks_left=total, total_ticks=total,
                        cur_char=random.choice(_GLITCH_HEAVY),
                    )
                    self._art_keys.add(key)

    # ── Tick ──────────────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if self._done:
            return

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
                mat.cur_char = random.choice(_GLITCH_HEAVY)
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
                        mat.cur_char = random.choice(_GLITCH_HEAVY)

            if mat.ticks_left <= 0:
                newly_locked.append(key)

        for key in newly_locked:
            mat = self._art_grid.pop(key)
            self._locked[key] = (mat.final_ch, mat.final_color)

        # ── Check completion ──────────────────────────────────────────────────
        if not self._art_grid:
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

        # Materializing art cells
        for (r, c), mat in self._art_grid.items():
            if 0 <= r < h and 0 <= c < w:
                if mat.delay > 0:
                    grid[r][c] = (mat.cur_char, glitch_color)
                else:
                    p = mat.progress
                    cell_color = _lerp_color(glitch_color, mat.final_color, p ** 1.5)
                    grid[r][c] = (mat.cur_char, cell_color)

        # Prompt text during hold phase
        if self._holding:
            prompt = "Press any key to enter the Batcave..."
            prompt_r = self._art_off_r + self._art_h + 3
            prompt_c = max(0, (w - len(prompt)) // 2)
            for i, ch in enumerate(prompt):
                c = prompt_c + i
                if 0 <= prompt_r < h and 0 <= c < w:
                    grid[prompt_r][c] = (ch, _PROMPT_COLOR)

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

    # ── Skip to settled ───────────────────────────────────────────────────────

    def _skip_to_settled(self) -> None:
        """Instantly lock all art cells and enter hold phase."""
        for key, mat in self._art_grid.items():
            self._locked[key] = (mat.final_ch, mat.final_color)
        self._art_grid.clear()
        self._holding = True
        self._draw(self._w, self._h)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _blank_screen(self) -> Text:
        """Build a full-screen blank to wipe residual chars on dismiss."""
        w, h = self._w, self._h
        line = " " * w + "\n"
        opaque_style = f"{BG} on {BG}"
        text = Text(overflow="fold", no_wrap=True)
        for _ in range(h):
            text.append(line, style=opaque_style)
        return text

    def _finish(self) -> None:
        if self._done:
            return
        self._done = True
        if self._timer:
            self._timer.stop()
        self._art_grid.clear()
        self._locked.clear()
        if self._display:
            self._display.update(self._blank_screen())
        self.call_after_refresh(self._deferred_dismiss)

    def _deferred_dismiss(self) -> None:
        """Dismiss after the blank frame has been painted by the compositor."""
        self.dismiss()
