"""Unit tests for `batman_code.widgets.thread_selector`.

Covers pure-logic helpers — formatters, label builders, title rendering —
without spinning up a Textual app. Layout/render behavior is covered by the
import smoke test plus integration once Phase 8 wires `app.py`.
"""

from __future__ import annotations

from rich.text import Text

from batman_code.sessions import ThreadInfo
from batman_code.widgets.thread_selector import (
    _COL_AGENT,
    _COL_MSGS,
    _COL_TID,
    ThreadSelectorScreen,
)


# ---------------------------------------------------------------------------
# _format_header — static column header
# ---------------------------------------------------------------------------


def test_format_header_contains_all_columns() -> None:
    header = ThreadSelectorScreen._format_header()
    assert "Thread" in header
    assert "Agent" in header
    assert "Msgs" in header
    assert "Updated" in header


def test_format_header_column_widths_respected() -> None:
    header = ThreadSelectorScreen._format_header()
    # Two leading spaces, then "Thread" left-padded to _COL_TID.
    assert header.startswith("  Thread")
    # After Thread block + 2 spaces, the Agent column begins.
    expected_agent_start = 2 + _COL_TID + 2
    assert header[expected_agent_start : expected_agent_start + len("Agent")] == "Agent"


# ---------------------------------------------------------------------------
# _format_option_label — per-thread row
# ---------------------------------------------------------------------------


def _make_thread(
    thread_id: str = "abc123",
    agent_name: str | None = "batman",
    message_count: int = 5,
    updated_at: str | None = None,
) -> ThreadInfo:
    return {
        "thread_id": thread_id,
        "agent_name": agent_name,
        "message_count": message_count,
        "updated_at": updated_at,
        "created_at": None,
    }


def test_format_option_label_shows_cursor_when_selected() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(), selected=True, current=False
    )
    # Selected rows lead with a cursor glyph (not two spaces).
    assert not label.startswith("  abc")


def test_format_option_label_no_cursor_when_unselected() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(), selected=False, current=False
    )
    assert label.startswith("  ")


def test_format_option_label_marks_current_thread() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(), selected=False, current=True
    )
    # Themed: "active" replaces upstream "current" for Gotham consistency.
    assert "(active)" in label


def test_format_option_label_omits_current_marker_for_non_current() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(), selected=False, current=False
    )
    assert "(active)" not in label
    # Also guard against accidental regression to the upstream wording.
    assert "(current)" not in label


def test_format_option_label_truncates_thread_id() -> None:
    long_id = "x" * 50
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(thread_id=long_id), selected=False, current=False
    )
    # The truncated id should appear exactly _COL_TID chars long.
    assert ("x" * _COL_TID) in label
    assert ("x" * (_COL_TID + 1)) not in label


def test_format_option_label_truncates_agent_name() -> None:
    long_agent = "a" * 30
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(agent_name=long_agent), selected=False, current=False
    )
    assert ("a" * _COL_AGENT) in label
    assert ("a" * (_COL_AGENT + 1)) not in label


def test_format_option_label_renders_unknown_for_missing_agent() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(agent_name=None), selected=False, current=False
    )
    assert "unknown" in label


def test_format_option_label_renders_message_count() -> None:
    label = ThreadSelectorScreen._format_option_label(
        _make_thread(message_count=42), selected=False, current=False
    )
    assert "42" in label
    # _COL_MSGS sanity — the field exists and is used in the formatter.
    assert _COL_MSGS == 4


# ---------------------------------------------------------------------------
# _build_title — plain / current-only / linked variants
# ---------------------------------------------------------------------------


def test_build_title_no_current_thread_uses_gotham_label() -> None:
    screen = ThreadSelectorScreen()
    title = screen._build_title()
    assert title == "Case Files"
    # Guard against regression to upstream wording.
    assert "Select Thread" not in title


def test_build_title_with_current_thread_no_url() -> None:
    screen = ThreadSelectorScreen(current_thread="abc-123")
    title = screen._build_title()
    assert isinstance(title, str)
    assert "Case Files" in title
    assert "active:" in title
    assert "abc-123" in title


def test_build_title_with_url_returns_rich_text_with_link() -> None:
    screen = ThreadSelectorScreen(current_thread="abc-123")
    url = "https://smith.langchain.com/o/x/projects/p/threads/abc-123"
    title = screen._build_title(thread_url=url)
    assert isinstance(title, Text)
    plain = title.plain
    assert "Case Files" in plain
    assert "active:" in plain
    assert "abc-123" in plain
    # The link should be attached to the thread-id span.
    assert any(getattr(span.style, "link", None) == url for span in title.spans)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_screen_initializes_with_empty_state() -> None:
    screen = ThreadSelectorScreen(current_thread="active-thread")
    assert screen._current_thread == "active-thread"
    assert screen._threads == []
    assert screen._selected_index == 0
    assert screen._option_widgets == []


def test_screen_initializes_without_current_thread() -> None:
    screen = ThreadSelectorScreen()
    assert screen._current_thread is None
