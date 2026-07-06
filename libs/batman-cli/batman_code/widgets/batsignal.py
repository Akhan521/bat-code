"""Bat-signal overlay widget for bat-code.

Renders a flickering ASCII bat-symbol as a background overlay on the
``batsignal`` CSS layer. Toggled by the ``/batsignal`` slash command in
`batman_code.app`. See CLAUDE.md § Phase 1 Bat-Signal Toggle for spec.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from rich.text import Text
from textual.widget import Widget

if TYPE_CHECKING:
    from textual.app import RenderResult


BAT_SYMBOL_ASCII: str = (
    "     _  _\n"
    "   _/ \\/ \\_\n"
    "  / /\\  /\\ \\\n"
    " / /  \\/  \\ \\\n"
    "/_/   /\\   \\_\\\n"
    "     /  \\\n"
    "    /    \\"
)
"""Bat-symbol ASCII art (7 rows). Verbatim from CLAUDE.md § Phase 1."""

_FLICKER_COLORS: dict[str, str] = {
    "dim": "#2d2d2d",
    "normal": "#b8960c",
    "bright": "#f5c518",
}

_FLICKER_STATES: tuple[str, ...] = ("dim", "normal", "bright", "off")

_FLICKER_INTERVAL_RANGE: tuple[float, float] = (0.3, 1.5)

# Weighted pool — "off" is rare (simulates a spotlight-blackout blink);
# other states share weight for a normal spotlight pulse rhythm.
_STATE_WEIGHTS: dict[str, int] = {
    "dim": 3,
    "normal": 3,
    "bright": 3,
    "off": 1,
}


def _pick_next_state(rng: random.Random | None = None) -> str:
    """Pick the next flicker state from the weighted pool.

    Args:
        rng: Optional RNG for deterministic testing. Defaults to the
            module-level ``random`` state.

    Returns:
        One of ``_FLICKER_STATES`` — most often ``dim``/``normal``/
        ``bright``, occasionally ``off``.
    """
    r = rng or random
    return r.choices(
        list(_STATE_WEIGHTS.keys()),
        weights=list(_STATE_WEIGHTS.values()),
    )[0]


def _next_interval(rng: random.Random | None = None) -> float:
    """Pick a jittered delay in seconds before the next flicker tick.

    Args:
        rng: Optional RNG for deterministic testing.

    Returns:
        A float in ``_FLICKER_INTERVAL_RANGE`` (inclusive).
    """
    r = rng or random
    lo, hi = _FLICKER_INTERVAL_RANGE
    return r.uniform(lo, hi)


class BatSignalOverlay(Widget):
    """Flickering ASCII bat-signal overlay on the ``batsignal`` CSS layer.

    Cycles through ``dim`` / ``normal`` / ``bright`` / ``off`` with
    jittered intervals to simulate a spotlight. The widget uses a
    self-rescheduling ``set_timer`` loop (rather than ``set_interval``)
    so each tick's delay can be jittered independently.

    The widget is instantiated once by ``BatmanApp._toggle_batsignal``
    on the first ``/batsignal`` invocation and removed on the second.
    """

    DEFAULT_CSS = """
    BatSignalOverlay {
        layer: batsignal;
        width: 100%;
        height: 100%;
        content-align: center middle;
        opacity: 0.35;
    }
    """

    def __init__(self, **kwargs: object) -> None:
        """Initialize the overlay in the ``normal`` (mid-brightness) state."""
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._state: str = "normal"

    def on_mount(self) -> None:
        """Start the flicker loop after mount."""
        self._schedule_next_flicker()

    def render(self) -> "RenderResult":
        """Return the ASCII art colored for the current state.

        Returns:
            A Rich ``Text`` of the bat symbol in the current color, or
            an empty ``Text`` when the state is ``"off"`` (simulating a
            spotlight blackout).
        """
        if self._state == "off":
            return Text("")
        color = _FLICKER_COLORS[self._state]
        return Text(BAT_SYMBOL_ASCII, style=color)

    def _schedule_next_flicker(self) -> None:
        """Register a one-shot timer for the next flicker tick."""
        interval = _next_interval()
        self.set_timer(interval, self._flicker)

    def _flicker(self) -> None:
        """One flicker tick: swap state, refresh, schedule the next tick."""
        self._state = _pick_next_state()
        self.refresh()
        self._schedule_next_flicker()
