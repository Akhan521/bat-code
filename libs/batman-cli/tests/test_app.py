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


# ---------------------------------------------------------------------------
# Theming — Gotham voice + bat-code paths + persona/splash on_mount behavior
#
# Method-body strings can't be reached without mounting the app, so we
# inspect the source with `inspect.getsource` (same pattern as Batch 10's
# adapter theming tests). Each assertion asserts the themed string is
# present AND the upstream wording is gone (regression guard).
# ---------------------------------------------------------------------------


def _method_source(cls: type, name: str) -> str:
    import inspect

    return inspect.getsource(getattr(cls, name))


# ---- TITLE + module/class docstrings -------------------------------------


def test_title_is_bat_code() -> None:
    assert BatmanApp.TITLE == "bat-code"


def test_title_regression_guard_no_deep_agents() -> None:
    assert "Deep Agents" not in BatmanApp.TITLE


def test_class_docstring_says_bat_code_not_deepagents_cli() -> None:
    assert BatmanApp.__doc__ is not None
    assert "bat-code" in BatmanApp.__doc__
    assert "deepagents-cli" not in BatmanApp.__doc__


def test_module_docstring_says_bat_code_not_deepagents_cli() -> None:
    assert app_module.__doc__ is not None
    assert "bat-code" in app_module.__doc__
    assert "deepagents-cli" not in app_module.__doc__


def test_init_docstring_says_bat_code_not_deep_agents() -> None:
    src = _method_source(BatmanApp, "__init__")
    assert "bat-code application" in src
    assert "Deep Agents application" not in src


# ---- /version handler + REMEMBER_PROMPT paths ----------------------------


def test_version_handler_reports_bat_code_not_deepagents() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert '"bat-code version:' in src or "'bat-code version:" in src
    assert '"deepagents version:' not in src
    assert "'deepagents version:" not in src


def test_remember_prompt_paths_are_bat_code_not_deepagents() -> None:
    from batman_code.app import REMEMBER_PROMPT

    assert "~/.bat-code/agent/AGENTS.md" in REMEMBER_PROMPT
    assert ".bat-code/AGENTS.md" in REMEMBER_PROMPT
    assert "~/.bat-code/agent/skills/" in REMEMBER_PROMPT
    # Regression: no stale deepagents paths anywhere in the prompt.
    assert "~/.deepagents/" not in REMEMBER_PROMPT
    assert ".deepagents/AGENTS.md" not in REMEMBER_PROMPT


# ---- _handle_command Gotham voice ---------------------------------------


def test_handle_command_help_text_says_batcomputer_commands() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "Batcomputer Commands:" in src
    # Upstream label gone.
    assert '"Commands: /quit' not in src


def test_handle_command_help_mentions_dark_knight_mode() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "DARK KNIGHT MODE" in src


def test_handle_command_help_mentions_the_cave() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "THE CAVE" in src


def test_handle_command_unknown_command_uses_batcomputer_wording() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "Unrecognized Batcomputer command:" in src
    assert "Unknown command:" not in src


def test_handle_command_new_thread_uses_new_case_opened() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "New case opened:" in src
    assert "Started new thread:" not in src


def test_handle_command_tokens_idle_message_themed() -> None:
    src = _method_source(BatmanApp, "_handle_command")
    assert "Batcomputer idle. No token usage yet." in src
    assert '"No token usage yet"' not in src


# ---- _handle_bash_command Gotham voice ----------------------------------


def test_handle_bash_command_mission_complete_no_output() -> None:
    src = _method_source(BatmanApp, "_handle_bash_command")
    assert "Mission complete. No output." in src
    assert "Command completed (no output)" not in src


# ---- Auto-approve shell notice ------------------------------------------


def test_request_approval_auto_authorized_batcave_wording() -> None:
    src = _method_source(BatmanApp, "_request_approval")
    assert "Auto-authorized (Batcave allow-list):" in src
    assert "Auto-approved shell command (allow-list):" not in src


# ---- _handle_trace_command -----------------------------------------------


def test_handle_trace_command_no_active_patrol() -> None:
    src = _method_source(BatmanApp, "_handle_trace_command")
    assert "No active patrol." in src
    assert "No active session." not in src


# ---- Agent lifecycle -----------------------------------------------------


def test_handle_user_message_dark_knight_standing_down() -> None:
    src = _method_source(BatmanApp, "_handle_user_message")
    assert "The Dark Knight is standing down" in src
    assert '"Agent not configured. "' not in src


def test_run_agent_task_villain_detected_error_wording() -> None:
    src = _method_source(BatmanApp, "_run_agent_task")
    assert "Villain detected:" in src
    assert "Agent error:" not in src


# ---- Thread history loading ---------------------------------------------


def test_load_thread_history_case_reopened_prefix() -> None:
    src = _method_source(BatmanApp, "_load_thread_history")
    assert '"Case reopened"' in src
    assert '"Resumed thread"' not in src


# ---- Quit hint -----------------------------------------------------------


def test_action_quit_or_interrupt_leave_the_batcave() -> None:
    src = _method_source(BatmanApp, "action_quit_or_interrupt")
    assert "leave the Batcave" in src
    assert '"Press Ctrl+C again to quit"' not in src


# ---- Thread switching (_resume_thread) ----------------------------------


def test_resume_thread_case_wording() -> None:
    src = _method_source(BatmanApp, "_resume_thread")
    assert "Cannot switch cases: no active Dark Knight" in src
    assert "Cannot switch cases: no active patrol" in src
    assert "Already on this case:" in src
    assert "Case switch failed:" in src
    # Upstream user-facing wording gone.
    assert "Cannot switch threads: no active agent" not in src
    assert "Cannot switch threads: no active session" not in src
    assert "Already on thread:" not in src
    # NOTE: `logger.exception("Failed to switch to thread %s", ...)` stays
    # in the source — that's an internal diagnostic, not user-facing chrome.
    # We only guard against the AppMessage-embedded upstream wording:
    assert 'f"Failed to switch to thread {thread_id}' not in src


# ---- Model switching (_switch_model) -------------------------------------


def test_switch_model_batcomputer_wording() -> None:
    src = _method_source(BatmanApp, "_switch_model")
    assert "Batcomputer already deployed:" in src
    assert "Batcomputer preference set to" in src
    assert "Could not save Batcomputer preference." in src
    assert "Failed to load Batcomputer model:" in src
    assert "Batcomputer redeploy failed:" in src
    assert "Batcomputer deployed:" in src
    # Upstream gone.
    assert '"Already using ' not in src
    assert '"Model preference set to ' not in src
    assert "Could not save model preference." not in src
    assert "Failed to create model:" not in src
    assert "Model switch failed:" not in src
    assert '"Switched to ' not in src


def test_switch_model_paths_are_bat_code() -> None:
    src = _method_source(BatmanApp, "_switch_model")
    assert "~/.bat-code/" in src
    assert "~/.deepagents/" not in src


# ---- Default model management -------------------------------------------


def test_set_default_model_batcomputer_wording() -> None:
    src = _method_source(BatmanApp, "_set_default_model")
    assert "Default Batcomputer set to" in src
    assert "Default model set to" not in src
    assert "~/.bat-code/" in src
    assert "~/.deepagents/" not in src


def test_clear_default_model_batcomputer_wording() -> None:
    src = _method_source(BatmanApp, "_clear_default_model")
    assert "Default Batcomputer cleared." in src
    assert "Could not clear default Batcomputer." in src
    assert "Default model cleared." not in src
    assert "Could not clear default model." not in src
    assert "~/.bat-code/" in src
    assert "~/.deepagents/" not in src


# ---------------------------------------------------------------------------
# on_mount new behavior — persona + splash conditional pushes
# ---------------------------------------------------------------------------


def test_batman_app_init_persona_defaults_to_batman() -> None:
    app = BatmanApp()
    assert app._persona == "batman"


def test_batman_app_init_persona_explicit_value_preserved() -> None:
    app = BatmanApp(persona="joker")
    assert app._persona == "joker"


def test_batman_app_init_persona_stores_arbitrary_name() -> None:
    # Constructor doesn't validate persona name — that's main.py's job.
    app = BatmanApp(persona="alfred")
    assert app._persona == "alfred"


def test_on_mount_source_pushes_joker_modal_when_persona_matches() -> None:
    src = _method_source(BatmanApp, "on_mount")
    assert 'self._persona == "joker"' in src
    assert "JokerWarningModal" in src


def test_on_mount_source_pushes_splash_when_no_splash_false() -> None:
    src = _method_source(BatmanApp, "on_mount")
    assert "not self._no_splash" in src
    assert "BatcaveScreen" in src


def test_on_mount_source_uses_batcavescreen_without_exit_callback() -> None:
    # The Phase 1 demo stub pushed BatcaveScreen with a `callback=lambda _:
    # self.exit(0)` — full Phase 8 must drop that so splash reveals chat
    # instead of exiting.
    src = _method_source(BatmanApp, "on_mount")
    assert "self.exit(0)" not in src


# ---------------------------------------------------------------------------
# JokerWarningModal — themed title + body
# ---------------------------------------------------------------------------


def test_joker_warning_modal_class_exists() -> None:
    from batman_code.app import JokerWarningModal

    assert JokerWarningModal is not None


def test_joker_warning_modal_title_dark_knight_mode_engaged() -> None:
    import inspect

    from batman_code.app import JokerWarningModal

    src = inspect.getsource(JokerWarningModal)
    assert "DARK KNIGHT MODE ENGAGED" in src


def test_joker_warning_modal_body_chaos_incoming() -> None:
    import inspect

    from batman_code.app import JokerWarningModal

    src = inspect.getsource(JokerWarningModal)
    assert "Chaos incoming" in src


def test_joker_warning_modal_body_mentions_auto_approve_bypass() -> None:
    import inspect

    from batman_code.app import JokerWarningModal

    src = inspect.getsource(JokerWarningModal)
    assert "auto-approves" in src or "auto-approve" in src.lower()


# ---------------------------------------------------------------------------
# UserMessage widget theming (Phase 5 deferred-spec closeout)
# ---------------------------------------------------------------------------


def test_user_message_border_left_uses_gotham_blue() -> None:
    import inspect

    from batman_code.widgets.messages import UserMessage

    src = inspect.getsource(UserMessage)
    # Border color themed to gotham_blue (#1a3a5c).
    assert "border-left: wide #1a3a5c" in src
    # Regression guard against upstream green.
    assert "border-left: wide #10b981" not in src


def test_user_message_ascii_fallback_uses_gotham_blue() -> None:
    import inspect

    from batman_code.widgets.messages import UserMessage

    src = inspect.getsource(UserMessage)
    assert '("ascii", "#1a3a5c")' in src
    assert '("ascii", "#10b981")' not in src


def test_user_message_has_gotham_citizen_label() -> None:
    import inspect

    from batman_code.widgets.messages import UserMessage

    src = inspect.getsource(UserMessage)
    assert "Gotham Citizen:" in src


def test_user_message_prefix_arrow_uses_gotham_blue() -> None:
    import inspect

    from batman_code.widgets.messages import UserMessage

    src = inspect.getsource(UserMessage)
    # The "> " prefix should be styled bold gotham_blue.
    assert 'style="bold #1a3a5c"' in src


# ---------------------------------------------------------------------------
# run_textual_app — persona + no_splash pass-through (Phase 9 wiring)
# ---------------------------------------------------------------------------


def test_run_textual_app_accepts_persona_and_no_splash_params() -> None:
    import inspect

    sig = inspect.signature(app_module.run_textual_app)
    assert "persona" in sig.parameters
    assert "no_splash" in sig.parameters
    # Defaults match BatmanApp's constructor.
    assert sig.parameters["persona"].default == "batman"
    assert sig.parameters["no_splash"].default is False


def test_run_textual_app_forwards_persona_and_no_splash_to_batman_app() -> None:
    import inspect

    src = inspect.getsource(app_module.run_textual_app)
    # Both params should be threaded into the BatmanApp constructor call.
    assert "persona=persona" in src
    assert "no_splash=no_splash" in src
