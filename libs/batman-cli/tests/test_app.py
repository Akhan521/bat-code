"""Unit tests for `batman_code.app` pure-logic helpers.

Covers everything that can be exercised without mounting a Textual app:
- `QueuedMessage` dataclass (init, frozen, mode field).
- `TextualTokenTracker` (add accumulates, reset zeroes, hide/show
  callback wiring).
- `TextualSessionState` (auto_approve flag, thread_id default + reset).
- `_COMMAND_URLS` dict integrity (keys present, bat-code repo URLs).
- `_build_thread_message` URL fallback (linked Text vs plain str).
- `BatmanApp.__init__` smoke (no_splash default + storage; required
  param wiring without spinning up the App event loop).

Skips lifecycle hooks, action handlers, modal wiring — those bind to
a mounted Textual app and are covered by Phase 10 end-to-end.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest
from rich.text import Text

from batman_code import app as app_module
from batman_code.app import (
    _COMMAND_URLS,
    BatmanApp,
    QueuedMessage,
    TextualSessionState,
    TextualTokenTracker,
)


# ---------------------------------------------------------------------------
# QueuedMessage — frozen dataclass for pending user messages
# ---------------------------------------------------------------------------


def test_queued_message_stores_text_and_mode() -> None:
    msg = QueuedMessage(text="hi", mode="normal")
    assert msg.text == "hi"
    assert msg.mode == "normal"


def test_queued_message_is_frozen() -> None:
    msg = QueuedMessage(text="hi", mode="normal")
    with pytest.raises(FrozenInstanceError):
        msg.text = "bye"  # type: ignore[misc]


def test_queued_message_accepts_all_input_modes() -> None:
    # InputMode literal allows "normal", "bash", "command".
    for mode in ("normal", "bash", "command"):
        msg = QueuedMessage(text="x", mode=mode)  # type: ignore[arg-type]
        assert msg.mode == mode


def test_queued_message_equality() -> None:
    a = QueuedMessage(text="same", mode="normal")
    b = QueuedMessage(text="same", mode="normal")
    c = QueuedMessage(text="same", mode="bash")
    assert a == b
    assert a != c


# ---------------------------------------------------------------------------
# TextualTokenTracker — token count + callback wiring
# ---------------------------------------------------------------------------


def test_token_tracker_starts_at_zero() -> None:
    tracker = TextualTokenTracker(update_callback=lambda _n: None)
    assert tracker.current_context == 0


def test_token_tracker_add_updates_current_context() -> None:
    seen: list[int] = []
    tracker = TextualTokenTracker(update_callback=seen.append)
    tracker.add(1500)
    assert tracker.current_context == 1500
    assert seen == [1500]


def test_token_tracker_add_overwrites_previous_value() -> None:
    # `add` replaces the running total rather than incrementing — the
    # call site already passes a cumulative count from usage_metadata.
    seen: list[int] = []
    tracker = TextualTokenTracker(update_callback=seen.append)
    tracker.add(1000)
    tracker.add(1500)
    assert tracker.current_context == 1500
    assert seen == [1000, 1500]


def test_token_tracker_add_ignores_unused_second_arg() -> None:
    # `_output_tokens` kwarg is kept for backwards compat but unused.
    seen: list[int] = []
    tracker = TextualTokenTracker(update_callback=seen.append)
    tracker.add(500, 999)
    assert tracker.current_context == 500
    assert seen == [500]


def test_token_tracker_reset_zeroes_and_notifies() -> None:
    seen: list[int] = []
    tracker = TextualTokenTracker(update_callback=seen.append)
    tracker.add(2000)
    tracker.reset()
    assert tracker.current_context == 0
    assert seen == [2000, 0]


def test_token_tracker_hide_calls_hide_callback_when_provided() -> None:
    hide_called: list[bool] = []
    tracker = TextualTokenTracker(
        update_callback=lambda _n: None,
        hide_callback=lambda: hide_called.append(True),
    )
    tracker.hide()
    assert hide_called == [True]


def test_token_tracker_hide_is_noop_without_hide_callback() -> None:
    # Must not raise — Phase 0 stubs / tests can construct without a
    # hide_callback and still call .hide().
    tracker = TextualTokenTracker(update_callback=lambda _n: None)
    tracker.hide()  # must not raise


def test_token_tracker_show_replays_current_context() -> None:
    seen: list[int] = []
    tracker = TextualTokenTracker(update_callback=seen.append)
    tracker.add(750)
    seen.clear()
    tracker.show()
    assert seen == [750]


# ---------------------------------------------------------------------------
# TextualSessionState — auto_approve flag + thread_id management
# ---------------------------------------------------------------------------


def test_session_state_defaults() -> None:
    state = TextualSessionState()
    assert state.auto_approve is False
    # Auto-generated thread_id is 8-char hex.
    assert len(state.thread_id) == 8
    int(state.thread_id, 16)  # must parse as hex; raises if not


def test_session_state_auto_approve_flag_persists() -> None:
    state = TextualSessionState(auto_approve=True)
    assert state.auto_approve is True


def test_session_state_thread_id_explicit_value_preserved() -> None:
    state = TextualSessionState(thread_id="my-thread-id")
    assert state.thread_id == "my-thread-id"


def test_session_state_reset_thread_generates_new_8char_hex() -> None:
    state = TextualSessionState(thread_id="old-thread")
    new_id = state.reset_thread()
    assert state.thread_id == new_id
    assert state.thread_id != "old-thread"
    assert len(state.thread_id) == 8
    int(state.thread_id, 16)


def test_session_state_reset_thread_produces_distinct_ids() -> None:
    state = TextualSessionState()
    first = state.thread_id
    second = state.reset_thread()
    assert first != second


def test_session_state_reset_thread_preserves_auto_approve() -> None:
    # reset_thread only swaps thread_id; the auto_approve flag stays.
    state = TextualSessionState(auto_approve=True)
    state.reset_thread()
    assert state.auto_approve is True


# ---------------------------------------------------------------------------
# _COMMAND_URLS — repointed to bat-code repo
# ---------------------------------------------------------------------------


def test_command_urls_has_all_three_keys() -> None:
    assert set(_COMMAND_URLS.keys()) == {"/changelog", "/docs", "/feedback"}


def test_command_urls_changelog_points_at_bat_code_repo() -> None:
    url = _COMMAND_URLS["/changelog"]
    assert "Akhan521/bat-code" in url
    # Regression guard against rollback to upstream URL.
    assert "langchain-ai/deepagents" not in url


def test_command_urls_feedback_points_at_bat_code_issues() -> None:
    url = _COMMAND_URLS["/feedback"]
    assert "Akhan521/bat-code/issues/new" in url
    assert "langchain-ai/deepagents" not in url


def test_command_urls_docs_uses_config_constant() -> None:
    # /docs delegates to the DOCS_URL constant from batman_code.config
    # (so any future re-pointing happens centrally, not here).
    from batman_code.config import DOCS_URL

    assert _COMMAND_URLS["/docs"] == DOCS_URL


# ---------------------------------------------------------------------------
# _build_thread_message — URL resolution with timeout fallback
# ---------------------------------------------------------------------------


async def test_build_thread_message_returns_rich_text_when_url_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module,
        "build_langsmith_thread_url",
        lambda _tid: "https://smith.example.com/thread/abc",
    )
    result = await BatmanApp._build_thread_message("Resumed thread", "abc")
    assert isinstance(result, Text)
    plain = result.plain
    assert plain.startswith("Resumed thread: ")
    assert "abc" in plain


async def test_build_thread_message_returns_plain_str_when_url_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module, "build_langsmith_thread_url", lambda _tid: None
    )
    result = await BatmanApp._build_thread_message("Resumed thread", "xyz")
    assert isinstance(result, str)
    assert result == "Resumed thread: xyz"


async def test_build_thread_message_falls_back_when_resolver_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(_tid: str) -> str:
        msg = "no network"
        raise OSError(msg)

    monkeypatch.setattr(app_module, "build_langsmith_thread_url", _boom)
    result = await BatmanApp._build_thread_message("Resumed thread", "fail")
    # Exception is swallowed by the broad `except (TimeoutError, Exception)`
    # and the function returns the plain-text fallback.
    assert isinstance(result, str)
    assert result == "Resumed thread: fail"


async def test_build_thread_message_uses_custom_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module, "build_langsmith_thread_url", lambda _tid: None
    )
    result = await BatmanApp._build_thread_message("Active patrol", "t-1")
    assert result == "Active patrol: t-1"


# ---------------------------------------------------------------------------
# BatmanApp.__init__ — no_splash deviation + base storage
#
# We only test attribute-storage behavior; mounting the app requires a
# Textual event loop and is covered by Phase 10 end-to-end.
# ---------------------------------------------------------------------------


def test_batman_app_init_no_splash_defaults_false() -> None:
    app = BatmanApp()
    # Regression guard: the no_splash deviation must keep its default
    # `False` so existing main.py call sites (Phase 1 stub) still work.
    assert app._no_splash is False


def test_batman_app_init_no_splash_explicit_true_preserved() -> None:
    app = BatmanApp(no_splash=True)
    assert app._no_splash is True


def test_batman_app_init_defaults_for_other_storage() -> None:
    app = BatmanApp()
    assert app._agent is None
    assert app._assistant_id is None
    assert app._backend is None
    assert app._auto_approve is False
    assert app._lc_thread_id is None
    assert app._initial_prompt is None
    assert app._checkpointer is None
    assert app._tools == []
    assert app._sandbox is None
    assert app._sandbox_type is None
    assert app._quit_pending is False
    assert app._agent_running is False
    assert app._processing_pending is False


def test_batman_app_init_cwd_defaults_to_cwd_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_cwd = Path("/tmp/fake-cwd")
    monkeypatch.setattr(Path, "cwd", staticmethod(lambda: fake_cwd))
    app = BatmanApp()
    assert app._cwd == str(fake_cwd)


def test_batman_app_init_cwd_string_preserved() -> None:
    app = BatmanApp(cwd="/tmp/some-project")
    assert app._cwd == "/tmp/some-project"


def test_batman_app_init_cwd_path_is_stringified() -> None:
    app = BatmanApp(cwd=Path("/tmp/project-y"))
    assert app._cwd == str(Path("/tmp/project-y"))


def test_batman_app_init_auto_approve_flag_stored() -> None:
    app = BatmanApp(auto_approve=True)
    assert app._auto_approve is True


def test_batman_app_init_thread_id_stored_as_lc_thread_id() -> None:
    # The constructor renames the kwarg to `_lc_thread_id` to avoid
    # colliding with Textual's internal `App._thread_id` int.
    app = BatmanApp(thread_id="user-thread-abc")
    assert app._lc_thread_id == "user-thread-abc"


def test_batman_app_init_tools_falsy_becomes_empty_list() -> None:
    app = BatmanApp(tools=None)
    assert app._tools == []


def test_batman_app_init_tools_explicit_list_preserved() -> None:
    def _fake_tool() -> None:
        return None

    tools: list[Any] = [_fake_tool, {"name": "other"}]
    app = BatmanApp(tools=tools)
    assert app._tools == tools


def test_batman_app_init_initial_prompt_stored() -> None:
    app = BatmanApp(initial_prompt="hello agent")
    assert app._initial_prompt == "hello agent"


def test_batman_app_init_empty_message_store_starts_empty() -> None:
    app = BatmanApp()
    # MessageStore is created during init; should report empty totals.
    assert app._message_store.total_count == 0
    assert app._pending_messages == app._pending_messages.__class__()
    assert app._queued_widgets == app._queued_widgets.__class__()


# ---------------------------------------------------------------------------
# Module-level constants — sanity guards
# ---------------------------------------------------------------------------


def test_app_module_exports_remember_prompt() -> None:
    # REMEMBER_PROMPT is the agent-facing prompt sent by /remember.
    # Phase 8 commit 3 will swap deepagents-cli/path references; this
    # smoke check just confirms the constant is in place and is the
    # expected size (catches accidental deletion / catastrophic edits).
    from batman_code.app import REMEMBER_PROMPT

    assert isinstance(REMEMBER_PROMPT, str)
    assert len(REMEMBER_PROMPT) > 1000  # source is ~3.4KB
    assert "Best Practices" in REMEMBER_PROMPT


def test_app_module_input_mode_literal_values() -> None:
    # InputMode is a Literal — assert the three known values exist as
    # accepted strings on QueuedMessage. Mostly a regression guard against
    # someone renaming the mode strings in the dispatch chain.
    for mode in ("normal", "bash", "command"):
        QueuedMessage(text="x", mode=mode)  # type: ignore[arg-type]
