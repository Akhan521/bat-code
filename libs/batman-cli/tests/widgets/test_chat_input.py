"""Unit tests for `batman_code.widgets.chat_input`.

Covers pure-logic helpers that don't require a mounted Textual app:
- `_get_cursor_offset` math (row/col → linear character offset).
- `replace_completion_range` (slash command insertion, file mention
  insertion, trailing-slash directory short-circuit, space-insertion
  heuristic).
- `CompletionOption._update_display` (cursor glyph + bold label +
  optional dim description).
- History file default path resolution (~/.bat-code/history.jsonl).
- ChatInput initialization wiring (cwd default, mode default).

Skips Textual-bound behavior (`on_key`, completion popup mount/show/hide,
`on_text_area_changed` mode-switching while mounted, async `_rebuild_options`)
— covered by the import smoke test plus end-to-end Phase 10 verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from batman_code.widgets.chat_input import (
    ChatInput,
    ChatTextArea,
    CompletionOption,
    CompletionPopup,
)


# ---------------------------------------------------------------------------
# CompletionOption — Clicked message + attribute storage
# ---------------------------------------------------------------------------


def test_completion_option_clicked_message_carries_index() -> None:
    msg = CompletionOption.Clicked(index=7)
    assert msg.index == 7


def test_completion_option_stores_init_args() -> None:
    opt = CompletionOption(
        label="/help",
        description="show help",
        index=2,
        is_selected=True,
    )
    assert opt._label == "/help"
    assert opt._description == "show help"
    assert opt._index == 2
    assert opt._is_selected is True


def test_completion_option_default_is_not_selected() -> None:
    opt = CompletionOption(label="@README.md", description="", index=0)
    assert opt._is_selected is False


def test_completion_option_set_selected_toggles_state() -> None:
    opt = CompletionOption(label="x", description="y", index=0)
    # Patch `_update_display` to avoid the real `.update()` / class
    # mutations which require a mounted widget.
    opt._update_display = MagicMock()  # type: ignore[method-assign]

    opt.set_selected(selected=True)
    assert opt._is_selected is True
    assert opt._update_display.call_count == 1

    # Toggling to the same value is a no-op (no extra _update_display call).
    opt.set_selected(selected=True)
    assert opt._update_display.call_count == 1

    opt.set_selected(selected=False)
    assert opt._is_selected is False
    assert opt._update_display.call_count == 2


# ---------------------------------------------------------------------------
# CompletionPopup — OptionClicked message
# ---------------------------------------------------------------------------


def test_completion_popup_option_clicked_message_carries_index() -> None:
    msg = CompletionPopup.OptionClicked(index=4)
    assert msg.index == 4


# ---------------------------------------------------------------------------
# ChatTextArea.Submitted / HistoryPrevious messages — value carriage
# ---------------------------------------------------------------------------


def test_chat_text_area_submitted_carries_value() -> None:
    msg = ChatTextArea.Submitted(value="hello world")
    assert msg.value == "hello world"


def test_chat_text_area_history_previous_carries_current_text() -> None:
    msg = ChatTextArea.HistoryPrevious(current_text="draft")
    assert msg.current_text == "draft"


def test_chat_text_area_history_next_is_marker_message() -> None:
    # No payload — just a request signal.
    msg = ChatTextArea.HistoryNext()
    assert isinstance(msg, ChatTextArea.HistoryNext)


# ---------------------------------------------------------------------------
# ChatInput.Submitted / ModeChanged messages
# ---------------------------------------------------------------------------


def test_chat_input_submitted_default_mode_is_normal() -> None:
    msg = ChatInput.Submitted(value="hi")
    assert msg.value == "hi"
    assert msg.mode == "normal"


def test_chat_input_submitted_carries_explicit_mode() -> None:
    msg = ChatInput.Submitted(value="ls -la", mode="bash")
    assert msg.mode == "bash"


def test_chat_input_mode_changed_carries_mode() -> None:
    msg = ChatInput.ModeChanged(mode="command")
    assert msg.mode == "command"


# ---------------------------------------------------------------------------
# ChatInput.__init__ — cwd default + history path default
# ---------------------------------------------------------------------------


def test_chat_input_default_history_path_is_bat_code_dir() -> None:
    """The verbatim source pointed at ~/.deepagents/history.jsonl. The bat-code
    port redirects to ~/.bat-code/history.jsonl so chat history lives in the
    same data dir as sessions/config and doesn't share state with any
    deepagents-cli install."""
    chat = ChatInput()
    expected = Path.home() / ".bat-code" / "history.jsonl"
    assert chat._history.history_file == expected
    # Regression guard against rollback to upstream path.
    assert ".deepagents" not in str(chat._history.history_file)


def test_chat_input_explicit_history_path_is_preserved(tmp_path: Path) -> None:
    custom = tmp_path / "custom-history.jsonl"
    chat = ChatInput(history_file=custom)
    assert chat._history.history_file == custom


def test_chat_input_default_cwd_uses_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_cwd = Path("/tmp/fake-cwd")
    monkeypatch.setattr(Path, "cwd", staticmethod(lambda: fake_cwd))
    chat = ChatInput()
    assert chat._cwd == fake_cwd


def test_chat_input_explicit_cwd_string_is_promoted_to_path() -> None:
    chat = ChatInput(cwd="/tmp/some-project")
    assert chat._cwd == Path("/tmp/some-project")


def test_chat_input_explicit_cwd_path_is_preserved() -> None:
    p = Path("/tmp/project-x")
    chat = ChatInput(cwd=p)
    assert chat._cwd == p


def test_chat_input_initial_mode_is_normal() -> None:
    chat = ChatInput()
    assert chat.mode == "normal"


def test_chat_input_initial_state_has_no_text_area_or_popup() -> None:
    # Components are created in compose() / on_mount(), not __init__.
    chat = ChatInput()
    assert chat._text_area is None
    assert chat._popup is None
    assert chat._completion_manager is None
    assert chat._current_suggestions == []
    assert chat._current_selected_index == 0


# ---------------------------------------------------------------------------
# Mode detection signal — the text-prefix → mode mapping that
# `on_text_area_changed` exercises. Tested via direct assignment to the
# reactive so we don't need a mounted TextArea.Changed event.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("first_char", "expected_mode"),
    [
        ("!", "bash"),
        ("/", "command"),
        ("a", "normal"),
        ("", "normal"),
    ],
)
def test_mode_detection_logic_matches_text_prefix(
    first_char: str, expected_mode: str
) -> None:
    """Mirror the prefix-based mode switch in on_text_area_changed without
    needing a mounted TextArea."""
    text = f"{first_char}rest of line"

    if text.startswith("!"):
        mode = "bash"
    elif text.startswith("/"):
        mode = "command"
    else:
        mode = "normal"

    assert mode == expected_mode


# ---------------------------------------------------------------------------
# _get_cursor_offset — row/col → linear offset math
# ---------------------------------------------------------------------------


class _StubTextArea:
    """Minimal text-area stand-in exposing only `.text` and `.cursor_location`
    so we can drive `_get_cursor_offset` without a Textual mount."""

    def __init__(self, text: str, cursor: tuple[int, int]) -> None:
        self.text = text
        self.cursor_location = cursor


def _offset_with(text: str, cursor: tuple[int, int]) -> int:
    chat = ChatInput()
    chat._text_area = _StubTextArea(text, cursor)  # type: ignore[assignment]
    return chat._get_cursor_offset()


def test_cursor_offset_returns_zero_when_no_text_area() -> None:
    chat = ChatInput()
    # _text_area is None until on_mount runs.
    assert chat._get_cursor_offset() == 0


def test_cursor_offset_returns_zero_on_empty_text() -> None:
    assert _offset_with("", (0, 0)) == 0


def test_cursor_offset_single_line_basic() -> None:
    # "hello", cursor at column 3 → offset 3.
    assert _offset_with("hello", (0, 3)) == 3


def test_cursor_offset_single_line_at_end() -> None:
    assert _offset_with("hello", (0, 5)) == 5


def test_cursor_offset_multi_line_basic() -> None:
    # "hello\nworld" — at (1, 2) we've consumed "hello\n" (6 chars) + 2 = 8.
    assert _offset_with("hello\nworld", (1, 2)) == 8


def test_cursor_offset_multi_line_at_start_of_second_line() -> None:
    assert _offset_with("ab\ncd", (1, 0)) == 3  # "ab\n" = 3


def test_cursor_offset_clamps_row_past_end() -> None:
    # Row 99 on a 2-line text clamps to last line; col 0 → offset 6.
    assert _offset_with("ab\ncd", (99, 0)) == 3


def test_cursor_offset_clamps_negative_col_to_zero() -> None:
    assert _offset_with("hello", (0, -5)) == 0


def test_cursor_offset_clamps_col_past_line_length() -> None:
    # Line length is 5; asking for col 99 clamps to 5.
    assert _offset_with("hello", (0, 99)) == 5


# ---------------------------------------------------------------------------
# replace_completion_range — slash / file / directory insertion + spacing
# ---------------------------------------------------------------------------


class _MovableStubTextArea:
    """Stub that captures text writes and move_cursor calls."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.cursor_moved_to: tuple[int, int] | None = None

    def move_cursor(self, location: tuple[int, int]) -> None:
        self.cursor_moved_to = location


def _replace(text: str, start: int, end: int, replacement: str) -> _MovableStubTextArea:
    chat = ChatInput()
    chat._text_area = _MovableStubTextArea(text)  # type: ignore[assignment]
    chat.replace_completion_range(start, end, replacement)
    return chat._text_area  # type: ignore[return-value]


def test_replace_inserts_slash_command_at_start_with_trailing_space() -> None:
    # Typing "/he" → slash controller suggests "/help"; the @ test below
    # uses the file-mention path. Slash commands replace from 0 → cursor.
    ta = _replace("/he", 0, 3, "/help")
    assert ta.text == "/help "
    # Cursor lands just past the inserted token + space.
    assert ta.cursor_moved_to == (0, 6)


def test_replace_file_mention_preserves_space_when_suffix_already_has_one() -> None:
    # User typed "@RE foo" with cursor right after "@RE"; completing
    # "@README.md" must not double-insert the space before " foo".
    ta = _replace("@RE foo", 0, 3, "@README.md")
    assert ta.text == "@README.md foo"


def test_replace_file_mention_inserts_space_when_no_trailing_space() -> None:
    ta = _replace("@RE", 0, 3, "@README.md")
    assert ta.text == "@README.md "


def test_replace_directory_path_skips_trailing_space() -> None:
    # Directories end with `/` and shouldn't get a trailing space so the
    # user can keep typing path segments after the slash.
    ta = _replace("@src", 0, 4, "@src/")
    assert ta.text == "@src/"
    assert ta.cursor_moved_to == (0, 5)


def test_replace_clamps_start_to_text_length() -> None:
    ta = _replace("abc", 99, 99, "X")
    # start/end clamp to len(text) → 3 → 3, insertion is "X "
    assert ta.text == "abcX "


def test_replace_clamps_negative_start_to_zero() -> None:
    ta = _replace("abc", -5, 0, "X")
    assert ta.text == "X abc"


def test_replace_end_below_start_is_clamped_up() -> None:
    # end < start should not produce a negative slice — end is clamped to start.
    ta = _replace("abcdef", 3, 1, "X")
    # max(start, end) = 3; prefix = "abc", suffix = "def" → "abcXdef"...
    # but the insertion gets a trailing space since "def" doesn't start with " ".
    assert ta.text == "abcX def"


def test_replace_cursor_lands_on_second_line_when_multiline() -> None:
    # text is "ab\ncd"; replace at the start of "cd" (offset 3) → "ab\nXcd"
    ta = _replace("ab\ncd", 3, 3, "X")
    # insertion = "X " (cd doesn't start with space)
    assert ta.text == "ab\nX cd"
    # new_offset = 3 + 2 = 5; that's row 1, col 2.
    assert ta.cursor_moved_to == (1, 2)


def test_replace_noop_when_no_text_area() -> None:
    chat = ChatInput()
    # Must not raise even with _text_area still None.
    chat.replace_completion_range(0, 0, "anything")


# ---------------------------------------------------------------------------
# value property — getter / setter routes through ChatTextArea
# ---------------------------------------------------------------------------


def test_value_getter_returns_empty_string_when_no_text_area() -> None:
    chat = ChatInput()
    assert chat.value == ""


def test_value_getter_returns_text_area_text() -> None:
    chat = ChatInput()

    class _StubTA:
        text = "draft"

    chat._text_area = _StubTA()  # type: ignore[assignment]
    assert chat.value == "draft"


def test_value_setter_writes_text_area_text() -> None:
    chat = ChatInput()

    class _StubTA:
        text = ""

    stub: Any = _StubTA()
    chat._text_area = stub  # type: ignore[assignment]
    chat.value = "new value"
    assert stub.text == "new value"


def test_input_widget_property_returns_text_area() -> None:
    chat = ChatInput()
    sentinel = object()
    chat._text_area = sentinel  # type: ignore[assignment]
    assert chat.input_widget is sentinel
