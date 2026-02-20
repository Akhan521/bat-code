"""Batcave splash screen animation for bat-code.

Two-act sequence:
  Act 1 — Bat swarm: ASCII bats fly left-to-right across a dark screen.
  Act 2 — Reveal: Bats scatter, batcave art fades in with glitch decay on the
           bat-symbol title, culminating in BATCOMPUTER ONLINE.

Any keypress or --no-splash skips immediately.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from rich.text import Text
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

# ── ASCII art ─────────────────────────────────────────────────────────────────

STALACTITES: tuple[str, ...] = (
    r" /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\ ",
    r" \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/  \/ ",
    r"      \    \    \    \    \    \    \    \    \    \    \    \    \    \   ",
    r"       \    \    \    \    \    \    \    \    \    \    \    \    \    \  ",
)

BAT_SYMBOL: tuple[str, ...] = (
    r"          __   __          ",
    r"    ______\ \ / /______    ",
    r"   /       \ V /       \   ",
    r"  / /~~~~~\ | | /~~~~~\ \  ",
    r" | |       \   /       | | ",
    r"  \ \_______\_/________/ / ",
    r"   \___________________/   ",
    r"          |     |          ",
    r"          |_____|          ",
)

BATCOMPUTER_BOX: tuple[str, ...] = (
    r"   ╔═══════════════════════════╗   ",
    r"   ║   B A T C O M P U T E R  ║   ",
    r"   ║       O N L I N E        ║   ",
    r"   ╚═══════════════════════════╝   ",
)

GLITCH_CHARS = "▓▒░╬╫╪┼╳※▪◆◇▄▀█"

# (display_string, visual_width)
BAT_CHARS: tuple[tuple[str, int], ...] = (
    ("/\\  /\\", 6),
    ("(^)", 3),
    (">==<", 4),
    ("/\\^/\\", 5),
    (">\\./<", 5),
    ("/v\\", 3),
)


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class _Bat:
    x: float       # column (float for smooth sub-pixel movement)
    y: int         # row
    speed: float   # columns per tick
    ci: int        # index into BAT_CHARS
    gold: bool     # True → bat-gold, False → dim white


# ── Screen ────────────────────────────────────────────────────────────────────

class BatcaveScreen(Screen[None]):
    """Full-screen animated Batcave intro shown at every launch."""

    DEFAULT_CSS = """
    BatcaveScreen {
        background: #0a0a0f;
        overflow: hidden;
    }
    #batcave-display {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }
    """

    # Tick durations per phase  (tick interval = 0.07 s)
    _SWARM_TICKS   = 30   # ~2.1 s  bats flying
    _SCATTER_TICKS = 12   # ~0.84 s bats scatter and fade
    _REVEAL_TICKS  = 24   # ~1.68 s batcave fades in
    _HOLD_TICKS    = 20   # ~1.4 s  hold before dismiss

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash
        self._phase = "swarm"
        self._tick = 0
        self._bats: list[_Bat] = []
        self._glitch: float = 1.0
        self._timer = None
        self._display: Static | None = None

    # ── Textual lifecycle ─────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        self._display = Static("", id="batcave-display")
        yield self._display

    def on_mount(self) -> None:
        if self._no_splash:
            self.dismiss()
            return
        self._spawn_bats()
        self._timer = self.set_interval(0.07, self._tick_handler)

    def on_key(self) -> None:
        self._finish()

    # ── Bat spawning ──────────────────────────────────────────────────────────

    def _spawn_bats(self) -> None:
        w = self.app.size.width
        h = self.app.size.height
        for _ in range(16):
            self._bats.append(_Bat(
                x=float(random.randint(-w, 0)),
                y=random.randint(1, max(1, h - 3)),
                speed=random.uniform(1.8, 4.2),
                ci=random.randint(0, len(BAT_CHARS) - 1),
                gold=random.random() > 0.55,
            ))

    # ── Main tick ─────────────────────────────────────────────────────────────

    def _tick_handler(self) -> None:
        self._tick += 1
        w, h = self.app.size.width, self.app.size.height

        if self._phase == "swarm":
            self._draw_swarm(w, h)
            if self._tick >= self._SWARM_TICKS:
                self._phase = "scatter"
                self._tick = 0

        elif self._phase == "scatter":
            self._draw_scatter(w, h)
            if self._tick >= self._SCATTER_TICKS:
                self._phase = "reveal"
                self._tick = 0
                self._glitch = 1.0

        elif self._phase == "reveal":
            self._glitch = max(0.0, 1.0 - (self._tick / 11))
            p = self._tick / self._REVEAL_TICKS
            self._draw_reveal(w, h, p)
            if self._tick >= self._REVEAL_TICKS:
                self._phase = "hold"
                self._tick = 0

        elif self._phase == "hold":
            self._draw_hold(w, h)
            if self._tick >= self._HOLD_TICKS:
                self._finish()

    # ── Grid helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _blank_grid(w: int, h: int) -> list[list[str]]:
        return [[" "] * w for _ in range(h)]

    def _place_bats(
        self,
        grid: list[list[str]],
        w: int,
        h: int,
        *,
        move: bool = True,
        speed_mult: float = 1.0,
    ) -> set[tuple[int, int]]:
        """Move bats and stamp them into the grid. Returns occupied cells."""
        occupied: set[tuple[int, int]] = set()
        for bat in self._bats:
            if move:
                bat.x += bat.speed * speed_mult
                if bat.x > w + 12:
                    bat.x = float(random.randint(-20, -4))
                    bat.y = random.randint(1, max(1, h - 3))
                    bat.speed = random.uniform(1.8, 4.2)
                    bat.ci = random.randint(0, len(BAT_CHARS) - 1)
                    bat.gold = random.random() > 0.55
            ch, cw = BAT_CHARS[bat.ci]
            col, row = int(bat.x), bat.y
            for i, c in enumerate(ch):
                cc = col + i
                if 0 <= row < h and 0 <= cc < w:
                    grid[row][cc] = c
                    occupied.add((row, cc))
        return occupied

    @staticmethod
    def _grid_to_text(
        grid: list[list[str]],
        occupied: set[tuple[int, int]],
        bat_color: str,
        bg_color: str = "#0a0a0f",
    ) -> Text:
        text = Text(overflow="fold", no_wrap=True)
        for r, row in enumerate(grid):
            c = 0
            while c < len(row):
                is_bat = (r, c) in occupied
                start = c
                while c < len(row) and ((r, c) in occupied) == is_bat:
                    c += 1
                text.append("".join(row[start:c]),
                             style=bat_color if is_bat else bg_color)
            text.append("\n")
        return text

    # ── Phase renderers ───────────────────────────────────────────────────────

    def _draw_swarm(self, w: int, h: int) -> None:
        grid = self._blank_grid(w, h)
        occ = self._place_bats(grid, w, h)
        # Mix gold and dim-white per-bat by re-examining positions
        text = Text(overflow="fold", no_wrap=True)
        # Build per-bat color map (row, col) → color
        color_map: dict[tuple[int, int], str] = {}
        for bat in self._bats:
            ch, _ = BAT_CHARS[bat.ci]
            col, row = int(bat.x), bat.y
            clr = "#f5c518" if bat.gold else "#aaaaaa"
            for i in range(len(ch)):
                cc = col + i
                if 0 <= row < h and 0 <= cc < w:
                    color_map[(row, cc)] = clr

        for r, row in enumerate(grid):
            c = 0
            while c < len(row):
                if (r, c) in occ:
                    clr = color_map.get((r, c), "#f5c518")
                    start = c
                    while c < len(row) and (r, c) in occ and color_map.get((r, c), "#f5c518") == clr:
                        c += 1
                    text.append("".join(row[start:c]), style=clr)
                else:
                    start = c
                    while c < len(row) and (r, c) not in occ:
                        c += 1
                    text.append("".join(row[start:c]), style="#0a0a0f")
            text.append("\n")

        if self._display:
            self._display.update(text)

    def _draw_scatter(self, w: int, h: int) -> None:
        fade = max(0.0, 1.0 - (self._tick / self._SCATTER_TICKS))
        v = int(fade * 0xAA)
        bat_color = f"#{v:02x}{int(v * 0.77):02x}{0:02x}"  # fades gold→dark
        grid = self._blank_grid(w, h)
        occ = self._place_bats(grid, w, h, speed_mult=3.0)
        text = self._grid_to_text(grid, occ, bat_color)
        if self._display:
            self._display.update(text)

    def _draw_reveal(self, w: int, h: int, p: float) -> None:
        text = self._build_cave_text(w, h, p, self._glitch)
        if self._display:
            self._display.update(text)

    def _draw_hold(self, w: int, h: int) -> None:
        text = self._build_cave_text(w, h, 1.0, 0.0)
        if self._display:
            self._display.update(text)

    # ── Batcave art builder ───────────────────────────────────────────────────

    def _build_cave_text(
        self, w: int, h: int, p: float, glitch: float
    ) -> Text:
        """Compose the full batcave art as Rich Text at reveal progress p∈[0,1]."""

        def gold(q: float) -> str:
            r = int(min(255, q * 245))
            g = int(min(255, q * 197))
            b = int(min(255, q * 24))
            return f"#{r:02x}{g:02x}{b:02x}"

        def blue(q: float) -> str:
            r = int(q * 26)
            g = int(q * 58)
            b = int(q * 92)
            return f"#{r:02x}{g:02x}{b:02x}"

        lines: list[tuple[str, str]] = []

        # ── Stalactites ── appear in first half of reveal
        stal_p = min(1.0, p * 2.2)
        for i, stal in enumerate(STALACTITES):
            row_p = max(0.0, stal_p - i * 0.2)
            lines.append((stal.center(w), blue(row_p)))

        lines.append(("", "#000000"))
        lines.append(("", "#000000"))

        # ── Bat symbol ── glitches in during mid-reveal
        sym_p = max(0.0, min(1.0, (p - 0.15) / 0.55))
        sym_color = gold(sym_p)
        for sym_line in BAT_SYMBOL:
            if glitch > 0.05 and random.random() < glitch:
                rendered = _glitch_str(sym_line, glitch * 0.7)
            else:
                rendered = sym_line
            lines.append((rendered.center(w), sym_color))

        lines.append(("", "#000000"))
        lines.append(("", "#000000"))

        # ── BATCOMPUTER box ── appears in last third of reveal
        if p > 0.6:
            box_p = (p - 0.6) / 0.4
            box_color = gold(box_p)
            for bt_line in BATCOMPUTER_BOX:
                lines.append((bt_line.center(w), box_color))

        # ── Skip hint ── subtle, appears after glitch settles
        if p > 0.35:
            lines.append(("", "#000000"))
            lines.append(("press any key to skip".center(w), "#222240"))

        text = Text(overflow="fold", no_wrap=True)
        for content, color in lines:
            text.append(content + "\n", style=color)
        return text

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _finish(self) -> None:
        if self._timer:
            self._timer.stop()
        self.dismiss()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _glitch_str(s: str, intensity: float) -> str:
    """Replace random non-space chars with glitch characters."""
    chars = list(s)
    for i, c in enumerate(chars):
        if c != " " and random.random() < intensity:
            chars[i] = random.choice(GLITCH_CHARS)
    return "".join(chars)
