"""Unit tests for `batman_code.widgets.batsignal` pure-logic helpers.

Covers the ASCII constant, the color/state/interval tables, the pure
helper functions (`_pick_next_state`, `_next_interval`), and the
`render()` branch table (colored `Text` per state, empty `Text` for
``off``). Skips lifecycle hooks (`on_mount`, `_schedule_next_flicker`,
`_flicker`) — those depend on the Textual event loop and are covered
by Phase 10 end-to-end.
"""

from __future__ import annotations

import random

from rich.text import Text

from batman_code.widgets.batsignal import (
    BAT_SYMBOL_ASCII,
    _FLICKER_COLORS,
    _FLICKER_INTERVAL_RANGE,
    _FLICKER_STATES,
    BatSignalOverlay,
    _next_interval,
    _pick_next_state,
)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_bat_symbol_ascii_is_seven_rows() -> None:
    assert BAT_SYMBOL_ASCII.count("\n") == 6  # 7 rows -> 6 newlines


def test_bat_symbol_ascii_matches_spec() -> None:
    # Verbatim from CLAUDE.md § Phase 1. Regression guard against
    # accidental edits that would drift the art out of sync with spec.
    expected = (
        "     _  _\n"
        "   _/ \\/ \\_\n"
        "  / /\\  /\\ \\\n"
        " / /  \\/  \\ \\\n"
        "/_/   /\\   \\_\\\n"
        "     /  \\\n"
        "    /    \\"
    )
    assert BAT_SYMBOL_ASCII == expected


def test_flicker_colors_use_bat_gold_family() -> None:
    assert _FLICKER_COLORS == {
        "dim": "#2d2d2d",
        "normal": "#b8960c",
        "bright": "#f5c518",
    }


def test_flicker_states_include_off_for_blackout_blink() -> None:
    assert set(_FLICKER_STATES) == {"dim", "normal", "bright", "off"}


def test_flicker_interval_range() -> None:
    assert _FLICKER_INTERVAL_RANGE == (0.3, 1.5)


# ---------------------------------------------------------------------------
# Pure helpers — deterministic RNG
# ---------------------------------------------------------------------------


def test_pick_next_state_returns_valid_state() -> None:
    rng = random.Random(42)
    for _ in range(100):
        assert _pick_next_state(rng) in _FLICKER_STATES


def test_pick_next_state_hits_all_states_over_time() -> None:
    # Regression: weighted pool shouldn't accidentally starve any state.
    rng = random.Random(0)
    seen = {_pick_next_state(rng) for _ in range(1000)}
    assert seen == set(_FLICKER_STATES)


def test_pick_next_state_off_is_rare() -> None:
    # "off" weight is 1 vs 3 for each other state — should be ~1/10 of
    # picks. Give generous slack (0-25%) to keep the test non-flaky.
    rng = random.Random(0)
    off_count = sum(1 for _ in range(1000) if _pick_next_state(rng) == "off")
    assert 0 < off_count < 250


def test_next_interval_stays_in_range() -> None:
    rng = random.Random(42)
    lo, hi = _FLICKER_INTERVAL_RANGE
    for _ in range(100):
        val = _next_interval(rng)
        assert lo <= val <= hi


# ---------------------------------------------------------------------------
# render() — branch table
# ---------------------------------------------------------------------------


def test_render_returns_colored_text_for_normal_state() -> None:
    overlay = BatSignalOverlay()
    overlay._state = "normal"
    result = overlay.render()
    assert isinstance(result, Text)
    assert result.plain == BAT_SYMBOL_ASCII
    assert str(result.style) == "#b8960c"


def test_render_returns_colored_text_for_dim_state() -> None:
    overlay = BatSignalOverlay()
    overlay._state = "dim"
    result = overlay.render()
    assert isinstance(result, Text)
    assert str(result.style) == "#2d2d2d"


def test_render_returns_colored_text_for_bright_state() -> None:
    overlay = BatSignalOverlay()
    overlay._state = "bright"
    result = overlay.render()
    assert isinstance(result, Text)
    assert str(result.style) == "#f5c518"


def test_render_returns_empty_text_for_off_state() -> None:
    overlay = BatSignalOverlay()
    overlay._state = "off"
    result = overlay.render()
    assert isinstance(result, Text)
    assert result.plain == ""


# ---------------------------------------------------------------------------
# __init__ defaults
# ---------------------------------------------------------------------------


def test_bat_signal_overlay_starts_in_normal_state() -> None:
    overlay = BatSignalOverlay()
    assert overlay._state == "normal"


def test_bat_signal_overlay_default_css_declares_batsignal_layer() -> None:
    # Regression against DEFAULT_CSS drift — the widget must land on
    # the batsignal CSS layer so it renders behind chat, not on top.
    assert "layer: batsignal;" in BatSignalOverlay.DEFAULT_CSS
