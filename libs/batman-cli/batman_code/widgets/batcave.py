"""Batcave loading screen for bat-code.

"BAT CODE" block letters materialize from glitch noise on a pure black
background, settle into multi-shade bat-gold, hold briefly, then fade/glitch
away. A retro CRT Batcomputer materializes from noise, and a typewriter
prompt types out. Press any key to skip, or --no-splash to bypass.

Phase flow: glitch → hold → fadeout → materialize → typewriter → dismiss
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
_GOTHAM_BLUE = "#1a3a5c"
_DIM_VIOLET = "#2d2d4e"
_SCREEN_BORDER = "#3a5a7c"
_DIM_GOLD = "#9a7508"

# Dark Knight theme — Batcomputer CRT colors
_CRT_BEZEL = "#2a2a2a"       # dark gunmetal frame
_CRT_GLOW = "#1a1a1a"        # charcoal glow strip
_CRT_SCREEN = "#8a7010"      # muted gold screen border
_CRT_UNDERLINE = "#705a08"   # dim amber underline

# Dark Knight glitch palette — warm darks matching the CRT theme
_CRT_GLITCH_COLORS = [
    "#1a1a1a", "#2a2a2a", "#1a1a1a",   # charcoal / gunmetal darks
    "#3a3020", "#2a2010", "#1a1a1a",   # warm dark browns
    "#4a3a10", "#3a2a08", "#2a2a2a",   # dim amber undertones
    "#1a1a1a", "#3a3a3a", "#2a2010",   # neutral darks with warmth
]

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
    orig_ch:     str = ""  # for fadeout: the char being faded away

    @property
    def progress(self) -> float:
        if self.total_ticks <= 0:
            return 1.0
        return 1.0 - (self.ticks_left / self.total_ticks)


# ── Compact 5-row CRT font for "BATCOMPUTER" ────────────────────────────────

_CRT_LETTERS: dict[str, list[str]] = {
    "B": ["██████▄", "██  ▄██", "█████▀ ", "██  ▄██", "██████▀"],
    "A": ["▄█████▄", "██   ██", "███████", "██   ██", "██   ██"],
    "T": ["███████", "   ██  ", "   ██  ", "   ██  ", "   ██  "],
    "C": ["▄██████", "██     ", "██     ", "██     ", "▀██████"],
    "O": ["▄█████▄", "██   ██", "██   ██", "██   ██", "▀█████▀"],
    "M": ["██▄ ▄██", "███▀███", "██ ▀ ██", "██   ██", "██   ██"],
    "P": ["██████▄", "██  ▄██", "█████▀ ", "██     ", "██     "],
    "U": ["██   ██", "██   ██", "██   ██", "██▄ ▄██", "▀█████▀"],
    "E": ["███████", "██     ", "█████  ", "██     ", "███████"],
    "R": ["██████▄", "██  ▄██", "█████▀ ", "██ ▀█▄ ", "██   ██"],
}
_CRT_FONT_HEIGHT = 5
_CRT_LETTER_GAP = 1


def _compose_crt_text(text: str) -> list[str]:
    """Compose text using compact 5-row CRT font (single word, no spaces)."""
    for letter_rows in _CRT_LETTERS.values():
        max_w = max(len(row) for row in letter_rows)
        for i, row in enumerate(letter_rows):
            letter_rows[i] = row.ljust(max_w)
    letters = [_CRT_LETTERS[ch] for ch in text]
    spacer = " " * _CRT_LETTER_GAP
    return [spacer.join(L[row] for L in letters) for row in range(_CRT_FONT_HEIGHT)]


BATCOMPUTER_ASCII = _compose_crt_text("BATCOMPUTER")


# ── Boot monologues (randomly selected each launch) ─────────────────────────

_BOOT_MONOLOGUES: list[str] = [
    "I am vengeance. I am the night. Beneath Wayne Manor, the Batcomputer stirs \u2014 deep agents rising from the dark like bats from the cave. Every bug is a criminal. Every fix, justice served. The Dark Knight's code never sleeps.",
    "Gotham's protector doesn't wait for daylight. The Bat-Signal blazes and the agents answer \u2014 scanning, analyzing, hunting through the codebase like shadows across rooftops. No vulnerability escapes the World's Greatest Detective.",
    "They think the dark is their ally. But I was born in it, molded by it. Every commit, every deploy, every refactor \u2014 silent, precise, and relentless. The cape and cowl may be analog, but the Batcomputer is anything but.",
    "Alfred once said the cave was just a hole in the ground. He was wrong. It's a fortress \u2014 and tonight its agents deploy across the codebase like the Bat-Family across Gotham. Each one trained. Each one ready. Justice compiles at midnight.",
    "The criminals of Gotham think they can hide in spaghetti code and tangled dependencies. They're wrong. The Batcomputer's agents move through the darkness, methodical and unforgiving. I don't need superpowers. I need a clean build.",
    "The Bat-Signal cuts through the Gotham sky. Below, the cave hums to life \u2014 deep agents spinning up like a swarm of bats, ready for deployment. Wayne Enterprises built the machine. The Dark Knight gives it purpose. Let's begin.",
]

_MONOLOGUE_COLOR = "#8a8a6a"  # dim sage for system-log feel


# ── Computer art builder ─────────────────────────────────────────────────────

# Reserve rows for monologue (4 lines) + blank + "Press any key..." = 6 rows
_MONOLOGUE_RESERVE = 6


def _build_computer_cells(
    screen_w: int,
    screen_h: int,
) -> tuple[list[list[tuple[str, str]]], int, int, int, int]:
    """Build full-screen Batcomputer CRT as a 2D cell grid.

    The CRT fills ~95% of terminal width and expands vertically to fill the
    terminal. No stand — just a massive screen.

    Returns (cells_grid, monitor_width, tw_col, tw_max_width, tw_start_row).
    """
    mw = max(70, min(screen_w - 2, int(screen_w * 0.95)))
    if mw % 2 != 0:
        mw += 1
    iw = mw - 6  # interior width (inside █░║ ... ║░█)

    # Dark Knight theme colors
    B = _CRT_BEZEL       # dark gunmetal frame
    V = _CRT_GLOW        # charcoal glow strip
    S = _CRT_SCREEN      # muted gold screen border
    G = _GOLD_EDGE       # bright gold header
    D = _CRT_UNDERLINE   # dim amber underline

    rows: list[list[tuple[str, str]]] = []

    def pad(row: list[tuple[str, str]]) -> list[tuple[str, str]]:
        while len(row) < mw:
            row.append((" ", BG))
        return row[:mw]

    def screen_row(content: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
        """Wrap interior content in █░║ ... ║░█ frame."""
        r: list[tuple[str, str]] = [("█", B), ("░", V), ("║", S)]
        if content:
            r.extend(content)
        while len(r) < mw - 3:
            r.append((" ", BG))
        r.extend([("║", S), ("░", V), ("█", B)])
        return r[:mw]

    # -- Top bezel (3 rows) --
    r = [(" ", BG), ("▄", B)]
    r.extend([("█", B)] * (mw - 4))
    r.extend([("▄", B), (" ", BG)])
    rows.append(pad(r))

    r = [("█", B), ("▀", B)]
    r.extend([("░", V)] * (mw - 4))
    r.extend([("▀", B), ("█", B)])
    rows.append(pad(r))

    r = [("█", B), ("░", V), ("╔", S)]
    r.extend([("═", S)] * iw)
    r.extend([("╗", S), ("░", V), ("█", B)])
    rows.append(pad(r))

    # -- Screen interior --
    target_total = max(20, screen_h - 2)
    interior_rows = target_total - 6  # minus 3 top bezel + 3 bottom bezel

    # BATCOMPUTER title (5-row compact font)
    art_lines = BATCOMPUTER_ASCII
    art_h = len(art_lines)
    art_w = max(len(line) for line in art_lines)

    # Fallback for very narrow terminals: plain spaced text
    use_block_font = art_w <= iw - 4

    # Layout: 2 top pad + 5 title + 1 blank + 1 underline + 1 blank
    #         + _MONOLOGUE_RESERVE (6) + bottom pad
    content_rows_needed = 2 + art_h + 1 + 1 + 1 + _MONOLOGUE_RESERVE
    bottom_pad = max(2, interior_rows - content_rows_needed)
    total_content = content_rows_needed + bottom_pad

    if total_content < interior_rows:
        top_extra = interior_rows - total_content
    else:
        top_extra = 0

    # Top blank rows
    for _ in range(2 + top_extra):
        rows.append(screen_row())

    # BATCOMPUTER title rows
    if use_block_font:
        for line in art_lines:
            left_pad = max(0, (iw - art_w) // 2)
            content: list[tuple[str, str]] = [(" ", BG)] * left_pad
            for ch in line:
                if ch == " ":
                    content.append((" ", BG))
                else:
                    content.append((ch, G))
            rows.append(screen_row(content))
    else:
        # Narrow fallback: spaced plain text
        spaced = "B A T C O M P U T E R"
        left_pad = max(0, (iw - len(spaced)) // 2)
        content = [(" ", BG)] * left_pad
        content.extend([(ch, G) for ch in spaced])
        rows.append(screen_row(content))
        # Pad to same height as block font
        for _ in range(art_h - 1):
            rows.append(screen_row())

    # 1 blank row after title
    rows.append(screen_row())

    # Underline
    ul_w = min(art_w if use_block_font else len("B A T C O M P U T E R"), iw - 4)
    left_pad = max(0, (iw - ul_w) // 2)
    content = [(" ", BG)] * left_pad
    content.extend([("═", D) for _ in range(ul_w)])
    rows.append(screen_row(content))

    # 1 blank row
    rows.append(screen_row())

    # Typewriter area: reserve blank rows for monologue + prompt
    tw_start_row = len(rows)
    for _ in range(_MONOLOGUE_RESERVE):
        rows.append(screen_row())

    # Bottom blank rows to fill
    for _ in range(bottom_pad):
        rows.append(screen_row())

    # -- Bottom bezel (3 rows) --
    r = [("█", B), ("░", V), ("╚", S)]
    r.extend([("═", S)] * iw)
    r.extend([("╝", S), ("░", V), ("█", B)])
    rows.append(pad(r))

    r = [("█", B), ("▄", B)]
    r.extend([("░", V)] * (mw - 4))
    r.extend([("▄", B), ("█", B)])
    rows.append(pad(r))

    r = [(" ", BG), ("▀", B)]
    r.extend([("█", B)] * (mw - 4))
    r.extend([("▀", B), (" ", BG)])
    rows.append(pad(r))

    # Typewriter text starts at col 6 (after ║ + 3 spaces)
    tw_col = 6
    tw_max = iw - 4

    return rows, mw, tw_col, tw_max, tw_start_row


# ── Screen ────────────────────────────────────────────────────────────────────

class BatcaveScreen(Screen[None]):
    """BAT CODE → Batcomputer splash screen."""

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

    # BAT CODE glitch timing
    _ART_DELAY_MIN  = 2
    _ART_DELAY_MAX  = 7
    _ART_SETTLE_MIN = 8
    _ART_SETTLE_MAX = 16
    _HOLD_TICKS     = 12   # ~1s (shortened to transition faster)

    # Fadeout timing
    _FADE_SETTLE_MIN = 6
    _FADE_SETTLE_MAX = 12

    # Computer materialize timing
    _MAT_DELAY_MIN  = 1
    _MAT_DELAY_MAX  = 5
    _MAT_SETTLE_MIN = 6
    _MAT_SETTLE_MAX = 14

    # Typewriter timing
    _COMPUTER_HOLD_TICKS = 18       # ~1.5s after flicker ends
    _ELLIPSIS_FLICKER_TICKS = 8     # ~0.6s of flicker

    def __init__(self, no_splash: bool = False) -> None:
        super().__init__()
        self._no_splash = no_splash
        self._display: Static | None = None
        self._timer = None
        self._done = False
        self._w = 0
        self._h = 0

        # Phase state machine
        self._phase = "glitch"
        self._phase_tick = 0

        # Shared animation grid (reused across glitch, fadeout, materialize)
        self._art_grid: dict[tuple, _MatCell] = {}
        self._art_off_r = 0
        self._art_h = 0
        self._base_grid: list[list[tuple[str, str]]] = []
        self._row_cache: list[list[tuple[str, str]]] = []
        self._dirty_rows: set[int] = set()
        self._row_art_count: dict[int, int] = {}

        # Computer state
        self._computer_mw = 0
        self._boot_monologue = random.choice(_BOOT_MONOLOGUES)

        # Multi-line typewriter state
        self._tw_lines: list[str] = []        # all lines to type
        self._tw_colors: list[str] = []       # color per line
        self._tw_line_idx = 0                 # current line being typed
        self._tw_char_idx = 0                 # position within current line
        self._tw_done = False                 # all lines fully typed
        self._flicker_tick = 0
        self._flicker_done = False
        self._tw_start_row = 0               # screen row of first typewriter line
        self._tw_col = 0                      # screen column where text starts
        self._tw_max = 0                      # max chars per line

    def compose(self) -> ComposeResult:
        self._display = Static("", id="bb-display")
        yield self._display

    def on_mount(self) -> None:
        if self._no_splash:
            self.dismiss()
            return
        self._w, self._h = self.app.size.width, self.app.size.height
        self._build(self._w, self._h)
        self._render_frame()
        self._timer = self.set_interval(self._TICK_S, self._tick)

    def on_key(self) -> None:
        if self._done:
            return
        if self._phase == "glitch":
            self._skip_to_settled()
        elif self._phase in ("hold", "fadeout"):
            self._skip_to_computer()
        elif self._phase == "materialize":
            self._skip_to_computer()
        elif self._phase == "typewriter":
            if not self._tw_done:
                # Snap all lines to fully typed
                self._tw_line_idx = len(self._tw_lines) - 1
                self._tw_char_idx = len(self._tw_lines[-1]) if self._tw_lines else 0
                self._tw_done = True
                self._flicker_tick = 0
                self._render_frame()
            else:
                self._finish()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _build(self, w: int, h: int) -> None:
        """Build BAT CODE glitch cells."""
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

    # ── Tick dispatch ─────────────────────────────────────────────────────────

    def _tick(self) -> None:
        if self._done:
            return

        self._phase_tick += 1

        if self._phase == "glitch":
            self._tick_glitch()
        elif self._phase == "hold":
            if self._phase_tick >= self._HOLD_TICKS:
                self._enter_fadeout()
        elif self._phase == "fadeout":
            self._tick_fadeout()
        elif self._phase == "materialize":
            self._tick_materialize()
        elif self._phase == "typewriter":
            self._tick_typewriter()

    # ── Shared settle logic ───────────────────────────────────────────────────

    def _settle_cells(self) -> bool:
        """Animate all _art_grid cells through glitch-settle. Returns True when done."""
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
                    mat.cur_char = (
                        mat.final_ch if random.random() < 0.7
                        else random.choice(_GLITCH_HEAVY)
                    )
            elif p >= 0.3:
                if mat.char_tick >= 2:
                    mat.char_tick = 0
                    mat.cur_char = (
                        mat.final_ch if random.random() < p
                        else random.choice(_GLITCH_HEAVY)
                    )
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

        return not self._art_grid

    # ── Phase: Glitch ─────────────────────────────────────────────────────────

    def _tick_glitch(self) -> None:
        if self._settle_cells():
            self._phase = "hold"
            self._phase_tick = 0
        self._render_frame()

    # ── Phase: Fadeout ────────────────────────────────────────────────────────

    def _enter_fadeout(self) -> None:
        """Move settled BAT CODE cells back to _art_grid as fadeout animations."""
        self._phase = "fadeout"
        self._phase_tick = 0
        self._art_grid.clear()
        self._dirty_rows.clear()
        self._row_art_count.clear()

        affected_rows: set[int] = set()

        for r in range(self._h):
            for c in range(self._w):
                ch, color = self._base_grid[r][c]
                if ch != " ":
                    key = (r, c)
                    total = random.randint(self._FADE_SETTLE_MIN, self._FADE_SETTLE_MAX)
                    delay = random.randint(0, 4)
                    # Color fades: current gold → glitch blue → BG
                    glitch_c = random.choice(_GLITCH_COLORS)
                    steps = []
                    for i in range(_COLOR_STEPS):
                        t = i / (_COLOR_STEPS - 1)
                        if t < 0.6:
                            steps.append(_lerp_color(color, glitch_c, t / 0.6))
                        else:
                            steps.append(_lerp_color(glitch_c, BG, (t - 0.6) / 0.4))

                    self._art_grid[key] = _MatCell(
                        final_ch=" ", final_color=BG,
                        delay=delay, ticks_left=total, total_ticks=total,
                        color_steps=steps,
                        cur_char=ch, orig_ch=ch,
                    )
                    self._base_grid[r][c] = (" ", BG)
                    self._dirty_rows.add(r)
                    self._row_art_count[r] = self._row_art_count.get(r, 0) + 1
                    affected_rows.add(r)

        for r in affected_rows:
            self._row_cache[r] = self._build_row_segments(r)

        if not self._art_grid:
            self._enter_materialize()
            return

        self._render_frame()

    def _tick_fadeout(self) -> None:
        """Fade BAT CODE cells: gold → glitch → black."""
        newly_dead: list[tuple] = []

        for key, mat in self._art_grid.items():
            if mat.delay > 0:
                mat.delay -= 1
                continue

            mat.ticks_left -= 1
            mat.char_tick += 1
            p = mat.progress

            # Character degradation: original → glitch → space
            if p < 0.2:
                mat.cur_char = mat.orig_ch
            elif p < 0.5:
                if mat.char_tick >= 2:
                    mat.char_tick = 0
                    mat.cur_char = (
                        mat.orig_ch if random.random() > p * 1.5
                        else random.choice(_GLITCH_HEAVY)
                    )
            elif p < 0.85:
                if mat.char_tick >= 1:
                    mat.char_tick = 0
                    mat.cur_char = random.choice(_GLITCH_HEAVY)
            else:
                mat.cur_char = " "

            if mat.ticks_left <= 0:
                newly_dead.append(key)

        for key in newly_dead:
            r, c = key
            self._art_grid.pop(key)
            # base_grid already set to (" ", BG) in _enter_fadeout
            self._row_art_count[r] -= 1
            if self._row_art_count[r] <= 0:
                self._dirty_rows.discard(r)
                self._row_cache[r] = self._build_row_segments(r)

        if not self._art_grid:
            self._enter_materialize()
        else:
            self._render_frame()

    # ── Phase: Materialize ────────────────────────────────────────────────────

    def _enter_materialize(self) -> None:
        """Build computer art cells and start glitch-settle animation."""
        self._phase = "materialize"
        self._phase_tick = 0
        self._art_grid.clear()
        self._dirty_rows.clear()
        self._row_art_count.clear()

        cells, mw, tw_col, tw_max, tw_start_row = _build_computer_cells(self._w, self._h)
        self._computer_mw = mw
        art_h = len(cells)
        comp_off_r = max(0, (self._h - art_h) // 2)
        comp_off_c = max(0, (self._w - mw) // 2)

        # Typewriter screen coordinates
        self._tw_start_row = comp_off_r + tw_start_row
        self._tw_col = comp_off_c + tw_col
        self._tw_max = tw_max

        # Reset base grid to all black
        for r in range(self._h):
            for c in range(self._w):
                self._base_grid[r][c] = (" ", BG)
            self._row_cache[r] = self._build_row_segments(r)

        # Create _MatCell for each non-space cell in computer art
        for ar, row in enumerate(cells):
            for ac, (ch, color) in enumerate(row):
                if ch == " ":
                    continue
                sr = comp_off_r + ar
                sc = comp_off_c + ac
                if 0 <= sr < self._h and 0 <= sc < self._w:
                    key = (sr, sc)
                    total = random.randint(self._MAT_SETTLE_MIN, self._MAT_SETTLE_MAX)
                    delay = random.randint(self._MAT_DELAY_MIN, self._MAT_DELAY_MAX)
                    glitch_c = random.choice(_CRT_GLITCH_COLORS)
                    steps = [
                        _lerp_color(glitch_c, color, (i / (_COLOR_STEPS - 1)) ** 1.5)
                        for i in range(_COLOR_STEPS)
                    ]
                    self._art_grid[key] = _MatCell(
                        final_ch=ch, final_color=color,
                        delay=delay, ticks_left=total, total_ticks=total,
                        color_steps=steps,
                        cur_char=random.choice(_GLITCH_HEAVY),
                    )
                    self._dirty_rows.add(sr)
                    self._row_art_count[sr] = self._row_art_count.get(sr, 0) + 1

        if not self._art_grid:
            self._enter_typewriter()
            return

        self._render_frame()

    def _tick_materialize(self) -> None:
        if self._settle_cells():
            self._enter_typewriter()
        else:
            self._render_frame()

    # ── Phase: Typewriter ─────────────────────────────────────────────────────

    def _enter_typewriter(self) -> None:
        self._phase = "typewriter"
        self._phase_tick = 0
        self._tw_line_idx = 0
        self._tw_char_idx = 0
        self._tw_done = False
        self._flicker_tick = 0
        self._flicker_done = False

        # Build typewriter lines from boot monologue
        monologue_lines = self._boot_monologue.split("\n")
        # Word-wrap each line to fit CRT interior
        wrapped: list[str] = []
        colors: list[str] = []
        for line in monologue_lines:
            if len(line) <= self._tw_max:
                wrapped.append(line)
                colors.append(_MONOLOGUE_COLOR)
            else:
                # Simple word wrap
                words = line.split(" ")
                current = ""
                for word in words:
                    if current and len(current) + 1 + len(word) > self._tw_max:
                        wrapped.append(current)
                        colors.append(_MONOLOGUE_COLOR)
                        current = word
                    else:
                        current = current + " " + word if current else word
                if current:
                    wrapped.append(current)
                    colors.append(_MONOLOGUE_COLOR)

        # Blank line + "Press any key..."
        wrapped.append("")
        colors.append(_MONOLOGUE_COLOR)
        wrapped.append("Press any key to enter the Batcave...")
        colors.append(_PROMPT_COLOR)

        self._tw_lines = wrapped
        self._tw_colors = colors
        self._render_frame()

    _TW_CHARS_PER_TICK = 2  # 2 chars per tick for snappier typing

    def _tick_typewriter(self) -> None:
        if not self._tw_done:
            for _ in range(self._TW_CHARS_PER_TICK):
                if self._tw_line_idx >= len(self._tw_lines):
                    self._tw_done = True
                    self._flicker_tick = 0
                    break
                line = self._tw_lines[self._tw_line_idx]
                if len(line) == 0:
                    # Blank line — skip to next immediately
                    self._tw_line_idx += 1
                    self._tw_char_idx = 0
                else:
                    self._tw_char_idx += 1
                    if self._tw_char_idx >= len(line):
                        # Line complete — advance to next
                        self._tw_line_idx += 1
                        self._tw_char_idx = 0
                if self._tw_line_idx >= len(self._tw_lines):
                    self._tw_done = True
                    self._flicker_tick = 0
                    break
        elif not self._flicker_done:
            self._flicker_tick += 1
            if self._flicker_tick >= self._ELLIPSIS_FLICKER_TICKS:
                self._flicker_done = True
                self._phase_tick = 0  # reset for hold countdown
        else:
            if self._phase_tick >= self._COMPUTER_HOLD_TICKS:
                self._finish()
                return

        self._render_frame()

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

    def _render_frame(self) -> None:
        """Render current state to display. Used by all phases."""
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

        # Typewriter overlay info
        tw_active = self._phase == "typewriter" and self._tw_lines
        tw_row_start = self._tw_start_row if tw_active else -1
        tw_row_end = tw_row_start + len(self._tw_lines) if tw_active else -1

        # Build Rich Text row-by-row
        text = Text(overflow="fold", no_wrap=True)
        for r in range(h):
            row_arts = art_by_row.get(r)
            is_tw = tw_row_start <= r < tw_row_end

            if row_arts or is_tw or r in self._dirty_rows:
                row = self._base_grid[r][:]
                if row_arts:
                    for c, ch, color in row_arts:
                        row[c] = (ch, color)
                if is_tw:
                    line_i = r - tw_row_start
                    line_text = self._tw_lines[line_i]
                    line_color = self._tw_colors[line_i]
                    sc = self._tw_col

                    if line_i < self._tw_line_idx:
                        # Fully typed line
                        for i, ch in enumerate(line_text):
                            if sc + i < w:
                                row[sc + i] = (ch, line_color)
                    elif line_i == self._tw_line_idx:
                        # Currently typing line
                        revealed = line_text[:self._tw_char_idx]
                        # Ellipsis flicker on final line
                        if (self._tw_done and not self._flicker_done
                                and self._flicker_tick % 3 != 0):
                            if revealed.endswith("..."):
                                revealed = revealed[:-3] + "   "
                        # Blinking cursor
                        cursor = ""
                        if not self._flicker_done:
                            cursor = "█" if self._phase_tick % 8 < 4 else " "
                        full = revealed + cursor
                        for i, ch in enumerate(full):
                            if sc + i < w:
                                row[sc + i] = (ch, line_color)
                    # else: future line — leave blank
                # Render row
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
        """Skip BAT CODE glitch → show settled letters (hold)."""
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
        self._render_frame()

    def _skip_to_computer(self) -> None:
        """Skip directly to settled computer → start typewriter."""
        self._art_grid.clear()
        self._dirty_rows.clear()
        self._row_art_count.clear()

        # Build computer art and place directly in base grid
        cells, mw, tw_col, tw_max, tw_start_row = _build_computer_cells(self._w, self._h)
        self._computer_mw = mw
        art_h = len(cells)
        comp_off_r = max(0, (self._h - art_h) // 2)
        comp_off_c = max(0, (self._w - mw) // 2)
        self._tw_start_row = comp_off_r + tw_start_row
        self._tw_col = comp_off_c + tw_col
        self._tw_max = tw_max

        # Reset entire base grid
        for r in range(self._h):
            for c in range(self._w):
                self._base_grid[r][c] = (" ", BG)

        # Place computer art directly
        for ar, row in enumerate(cells):
            for ac, (ch, color) in enumerate(row):
                if ch == " ":
                    continue
                sr = comp_off_r + ar
                sc = comp_off_c + ac
                if 0 <= sr < self._h and 0 <= sc < self._w:
                    self._base_grid[sr][sc] = (ch, color)

        # Rebuild all row caches
        for r in range(self._h):
            self._row_cache[r] = self._build_row_segments(r)

        self._enter_typewriter()

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
