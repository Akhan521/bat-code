"""Unit tests for `batman_code.textual_adapter`.

Covers pure-logic helpers that don't require a running LangGraph stream
or a mounted Textual app:

- `_build_stream_config` — LangGraph config dict shape.
- `_is_summarization_chunk` — metadata-source predicate.
- `_build_interrupted_ai_message` — state reconstruction on cancellation.
- `TextualUIAdapter.__init__` / `set_token_tracker` — callback wiring.

Skips `execute_task_textual` (640-line async loop binding to LangGraph
streaming + Textual widget mounts — covered by Phase 10 end-to-end).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from batman_code.textual_adapter import (
    TextualUIAdapter,
    _build_interrupted_ai_message,
    _build_stream_config,
    _is_summarization_chunk,
)


# ---------------------------------------------------------------------------
# _build_stream_config — LangGraph config dict builder
# ---------------------------------------------------------------------------


def test_build_stream_config_basic_shape() -> None:
    config = _build_stream_config(thread_id="t-123", assistant_id=None)
    # Top-level keys are stable: configurable + metadata.
    assert set(config.keys()) == {"configurable", "metadata"}
    assert config["configurable"] == {"thread_id": "t-123"}


def test_build_stream_config_no_assistant_empty_metadata() -> None:
    config = _build_stream_config(thread_id="t-123", assistant_id=None)
    assert config["metadata"] == {}


def test_build_stream_config_empty_string_assistant_empty_metadata() -> None:
    # Falsy assistant_id (empty string) should NOT populate metadata.
    config = _build_stream_config(thread_id="t-123", assistant_id="")
    assert config["metadata"] == {}


def test_build_stream_config_with_assistant_populates_metadata() -> None:
    config = _build_stream_config(thread_id="t-123", assistant_id="batman")
    metadata = config["metadata"]
    assert metadata["assistant_id"] == "batman"
    assert metadata["agent_name"] == "batman"
    assert "updated_at" in metadata


def test_build_stream_config_updated_at_is_iso_format() -> None:
    config = _build_stream_config(thread_id="t-123", assistant_id="batman")
    updated_at = config["metadata"]["updated_at"]
    # Must round-trip through datetime.fromisoformat without raising.
    parsed = datetime.fromisoformat(updated_at)
    # Timestamp must be timezone-aware (UTC was used).
    assert parsed.tzinfo is not None


def test_build_stream_config_thread_id_passthrough_preserves_value() -> None:
    config = _build_stream_config(thread_id="abc-XYZ-1", assistant_id=None)
    assert config["configurable"]["thread_id"] == "abc-XYZ-1"


# ---------------------------------------------------------------------------
# _is_summarization_chunk — metadata predicate truth table
# ---------------------------------------------------------------------------


def test_is_summarization_chunk_true_when_lc_source_matches() -> None:
    assert _is_summarization_chunk({"lc_source": "summarization"}) is True


def test_is_summarization_chunk_false_when_lc_source_different() -> None:
    assert _is_summarization_chunk({"lc_source": "agent"}) is False


def test_is_summarization_chunk_false_when_key_missing() -> None:
    assert _is_summarization_chunk({"other_key": "value"}) is False


def test_is_summarization_chunk_false_when_metadata_none() -> None:
    assert _is_summarization_chunk(None) is False


def test_is_summarization_chunk_false_when_metadata_empty() -> None:
    assert _is_summarization_chunk({}) is False


# ---------------------------------------------------------------------------
# _build_interrupted_ai_message — state reconstruction on cancellation
# ---------------------------------------------------------------------------


class _StubToolWidget:
    """Stand-in for `ToolCallMessage` exposing only the attributes the
    builder reads (`_tool_name`, `_args`). Avoids constructing real Textual
    widgets in unit tests."""

    def __init__(self, tool_name: str, args: dict[str, Any]) -> None:
        self._tool_name = tool_name
        self._args = args


def test_build_interrupted_ai_message_returns_none_when_both_empty() -> None:
    assert _build_interrupted_ai_message({}, {}) is None


def test_build_interrupted_ai_message_returns_none_when_only_whitespace_text() -> None:
    # Whitespace-only text is stripped, so the no-content branch is hit.
    msg = _build_interrupted_ai_message({(): "   \n  "}, {})
    assert msg is None


def test_build_interrupted_ai_message_with_text_only() -> None:
    msg = _build_interrupted_ai_message({(): "hello world"}, {})
    assert isinstance(msg, AIMessage)
    assert msg.content == "hello world"
    assert msg.tool_calls == []


def test_build_interrupted_ai_message_with_tool_calls_only() -> None:
    tools = {
        "call-1": _StubToolWidget(tool_name="bash", args={"cmd": "ls"}),
    }
    msg = _build_interrupted_ai_message({}, tools)
    assert isinstance(msg, AIMessage)
    assert msg.content == ""
    assert len(msg.tool_calls) == 1
    tc = msg.tool_calls[0]
    assert tc["id"] == "call-1"
    assert tc["name"] == "bash"
    assert tc["args"] == {"cmd": "ls"}


def test_build_interrupted_ai_message_with_both_text_and_tools() -> None:
    tools = {
        "call-1": _StubToolWidget(tool_name="read_file", args={"path": "a.py"}),
    }
    msg = _build_interrupted_ai_message({(): "let me check"}, tools)
    assert msg is not None
    assert msg.content == "let me check"
    assert len(msg.tool_calls) == 1


def test_build_interrupted_ai_message_strips_text_whitespace() -> None:
    msg = _build_interrupted_ai_message({(): "  hi  \n"}, {})
    assert msg is not None
    assert msg.content == "hi"


def test_build_interrupted_ai_message_reconstructs_multiple_tool_calls() -> None:
    tools = {
        "call-1": _StubToolWidget("bash", {"cmd": "ls"}),
        "call-2": _StubToolWidget("write_file", {"path": "out.txt", "content": "x"}),
    }
    msg = _build_interrupted_ai_message({}, tools)
    assert msg is not None
    assert len(msg.tool_calls) == 2
    by_id = {tc["id"]: tc for tc in msg.tool_calls}
    assert by_id["call-1"]["name"] == "bash"
    assert by_id["call-2"]["name"] == "write_file"
    assert by_id["call-2"]["args"]["path"] == "out.txt"


def test_build_interrupted_ai_message_uses_main_namespace_key_for_text() -> None:
    # Only text at the main namespace (empty tuple) is captured. Subagent
    # namespace text is intentionally ignored for state recovery.
    msg = _build_interrupted_ai_message(
        {("subagent",): "subagent text"}, {}
    )
    assert msg is None  # main namespace has no text → strip → empty → None


# ---------------------------------------------------------------------------
# TextualUIAdapter — callback wiring + state initialization
# ---------------------------------------------------------------------------


def _make_required_callbacks() -> tuple[Any, Any, Any]:
    """Build the three required callback stubs used by the adapter."""

    async def mount(*_a: Any, **_kw: Any) -> None:
        return None

    def update_status(_msg: str) -> None:
        return None

    async def request_approval(*_a: Any, **_kw: Any) -> Any:
        return None

    return mount, update_status, request_approval


def test_adapter_init_stores_required_callbacks() -> None:
    mount, update_status, request_approval = _make_required_callbacks()
    adapter = TextualUIAdapter(
        mount_message=mount,
        update_status=update_status,
        request_approval=request_approval,
    )
    assert adapter._mount_message is mount
    assert adapter._update_status is update_status
    assert adapter._request_approval is request_approval


def test_adapter_init_optional_callbacks_default_none() -> None:
    mount, update_status, request_approval = _make_required_callbacks()
    adapter = TextualUIAdapter(
        mount_message=mount,
        update_status=update_status,
        request_approval=request_approval,
    )
    assert adapter._on_auto_approve_enabled is None
    assert adapter._scroll_to_bottom is None
    assert adapter._set_spinner is None
    assert adapter._set_active_message is None
    assert adapter._sync_message_content is None


def test_adapter_init_optional_callbacks_stored_when_provided() -> None:
    mount, update_status, request_approval = _make_required_callbacks()

    sentinels: dict[str, Any] = {
        "on_auto_approve_enabled": lambda: None,
        "scroll_to_bottom": lambda: None,
        "set_spinner": lambda _x: None,  # type: ignore[unused-ignore]
        "set_active_message": lambda _x: None,
        "sync_message_content": lambda _a, _b: None,
    }

    adapter = TextualUIAdapter(
        mount_message=mount,
        update_status=update_status,
        request_approval=request_approval,
        **sentinels,  # type: ignore[arg-type]
    )
    assert adapter._on_auto_approve_enabled is sentinels["on_auto_approve_enabled"]
    assert adapter._scroll_to_bottom is sentinels["scroll_to_bottom"]
    assert adapter._set_spinner is sentinels["set_spinner"]
    assert adapter._set_active_message is sentinels["set_active_message"]
    assert adapter._sync_message_content is sentinels["sync_message_content"]


def test_adapter_init_starts_with_empty_state() -> None:
    mount, update_status, request_approval = _make_required_callbacks()
    adapter = TextualUIAdapter(
        mount_message=mount,
        update_status=update_status,
        request_approval=request_approval,
    )
    assert adapter._current_tool_messages == {}
    assert adapter._token_tracker is None


def test_adapter_set_token_tracker_assigns_value() -> None:
    mount, update_status, request_approval = _make_required_callbacks()
    adapter = TextualUIAdapter(
        mount_message=mount,
        update_status=update_status,
        request_approval=request_approval,
    )
    sentinel_tracker = object()
    adapter.set_token_tracker(sentinel_tracker)
    assert adapter._token_tracker is sentinel_tracker


# ---------------------------------------------------------------------------
# Module-level constants — sanity guards
# ---------------------------------------------------------------------------


def test_hitl_request_adapter_is_initialized() -> None:
    """Smoke check that the TypeAdapter import + initialization didn't break
    on import (catches regressions if langchain HITL types move)."""
    from batman_code.textual_adapter import _HITL_REQUEST_ADAPTER
    assert _HITL_REQUEST_ADAPTER is not None


# ---------------------------------------------------------------------------
# Theming — Gotham narrative strings inside execute_task_textual
#
# These strings live inside an async generator body that's only reachable
# through a running LangGraph stream. We inspect the function source to
# assert the themed wording is present + guard against rollback to upstream.
# ---------------------------------------------------------------------------


def _adapter_source() -> str:
    import inspect

    from batman_code.textual_adapter import execute_task_textual

    return inspect.getsource(execute_task_textual)


def test_spinner_label_uses_themed_investigating() -> None:
    src = _adapter_source()
    assert '"Investigating"' in src
    # Regression guard against rollback to upstream wording.
    assert '"Thinking"' not in src


def test_cancellation_message_uses_themed_mission_aborted() -> None:
    src = _adapter_source()
    assert '"Mission aborted."' in src
    # Regression guard.
    assert '"Interrupted by user"' not in src


def test_hitl_reject_message_uses_themed_order_denied() -> None:
    src = _adapter_source()
    assert "Order denied. Tell the Dark Knight what to do instead." in src
    # Regression guard.
    assert "Command rejected. Tell the agent what you'd like instead." not in src
