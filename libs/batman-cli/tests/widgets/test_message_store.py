"""Unit tests for `batman_code.widgets.message_store`.

Covers pure-logic helpers — enum membership, `MessageData` validation/defaults,
and `MessageStore` window/prune/hydrate arithmetic. `to_widget`/`from_widget`
round-trips depend on Textual widget construction and are covered indirectly
by the import smoke test (and end-to-end once Phase 8 wires `app.py`).
"""

from __future__ import annotations

import time

import pytest

from batman_code.widgets.message_store import (
    MessageData,
    MessageStore,
    MessageType,
    ToolStatus,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_message_type_values() -> None:
    assert MessageType.USER.value == "user"
    assert MessageType.ASSISTANT.value == "assistant"
    assert MessageType.TOOL.value == "tool"
    assert MessageType.ERROR.value == "error"
    assert MessageType.APP.value == "app"
    assert MessageType.DIFF.value == "diff"


def test_tool_status_values() -> None:
    assert ToolStatus.PENDING.value == "pending"
    assert ToolStatus.RUNNING.value == "running"
    assert ToolStatus.SUCCESS.value == "success"
    assert ToolStatus.ERROR.value == "error"
    assert ToolStatus.REJECTED.value == "rejected"
    assert ToolStatus.SKIPPED.value == "skipped"


# ---------------------------------------------------------------------------
# MessageData
# ---------------------------------------------------------------------------


def test_message_data_default_id_has_msg_prefix() -> None:
    msg = MessageData(type=MessageType.USER, content="hello")
    assert msg.id.startswith("msg-")
    # uuid4().hex[:8] → 8 chars after the prefix.
    assert len(msg.id) == len("msg-") + 8


def test_message_data_unique_default_ids() -> None:
    a = MessageData(type=MessageType.USER, content="a")
    b = MessageData(type=MessageType.USER, content="b")
    assert a.id != b.id


def test_message_data_default_timestamp_is_recent() -> None:
    before = time.time()
    msg = MessageData(type=MessageType.USER, content="hi")
    after = time.time()
    assert before <= msg.timestamp <= after


def test_message_data_explicit_id_is_preserved() -> None:
    msg = MessageData(type=MessageType.USER, content="x", id="custom-id")
    assert msg.id == "custom-id"


def test_message_data_tool_without_tool_name_raises() -> None:
    with pytest.raises(ValueError, match="tool_name"):
        MessageData(type=MessageType.TOOL, content="")


def test_message_data_tool_with_empty_tool_name_raises() -> None:
    with pytest.raises(ValueError, match="tool_name"):
        MessageData(type=MessageType.TOOL, content="", tool_name="")


def test_message_data_tool_with_tool_name_succeeds() -> None:
    msg = MessageData(type=MessageType.TOOL, content="", tool_name="bash")
    assert msg.tool_name == "bash"


def test_message_data_non_tool_types_dont_require_tool_name() -> None:
    # All non-TOOL types should accept missing tool_name without raising.
    for msg_type in (
        MessageType.USER,
        MessageType.ASSISTANT,
        MessageType.ERROR,
        MessageType.APP,
        MessageType.DIFF,
    ):
        MessageData(type=msg_type, content="x")  # must not raise


# ---------------------------------------------------------------------------
# MessageStore — initial state + simple properties
# ---------------------------------------------------------------------------


def _make_store_with(n: int) -> MessageStore:
    """Build a store with `n` USER messages sequentially indexed."""
    store = MessageStore()
    for i in range(n):
        store.append(MessageData(type=MessageType.USER, content=f"msg {i}", id=f"id-{i}"))
    return store


def test_store_initial_state_is_empty() -> None:
    store = MessageStore()
    assert store.total_count == 0
    assert store.visible_count == 0
    assert store.has_messages_above is False
    assert store.has_messages_below is False
    assert store.get_visible_range() == (0, 0)
    assert store.get_all_messages() == []
    assert store.get_visible_messages() == []


def test_store_class_level_constants() -> None:
    # Document the source values — guards against accidental retuning.
    assert MessageStore.WINDOW_SIZE == 50
    assert MessageStore.HYDRATE_BUFFER == 15


# ---------------------------------------------------------------------------
# append + lookups
# ---------------------------------------------------------------------------


def test_append_increases_total_and_visible_count() -> None:
    store = MessageStore()
    msg = MessageData(type=MessageType.USER, content="hi", id="m1")
    store.append(msg)
    assert store.total_count == 1
    assert store.visible_count == 1
    assert store.get_visible_range() == (0, 1)


def test_get_message_returns_match() -> None:
    store = _make_store_with(3)
    found = store.get_message("id-1")
    assert found is not None
    assert found.content == "msg 1"


def test_get_message_returns_none_when_missing() -> None:
    store = _make_store_with(3)
    assert store.get_message("nope") is None


def test_get_message_at_index_valid() -> None:
    store = _make_store_with(3)
    msg = store.get_message_at_index(2)
    assert msg is not None
    assert msg.id == "id-2"


def test_get_message_at_index_out_of_bounds_returns_none() -> None:
    store = _make_store_with(3)
    assert store.get_message_at_index(99) is None
    assert store.get_message_at_index(-1) is None


def test_get_all_messages_is_shallow_copy() -> None:
    store = _make_store_with(2)
    snapshot = store.get_all_messages()
    snapshot.append(MessageData(type=MessageType.USER, content="rogue"))
    # Mutating the snapshot must not affect the store.
    assert store.total_count == 2


# ---------------------------------------------------------------------------
# update_message — allowlist gating
# ---------------------------------------------------------------------------


def test_update_message_updates_allowed_field() -> None:
    store = _make_store_with(1)
    ok = store.update_message("id-0", content="new")
    assert ok is True
    assert store.get_message("id-0").content == "new"  # type: ignore[union-attr]


def test_update_message_returns_false_when_missing() -> None:
    store = _make_store_with(1)
    assert store.update_message("nope", content="x") is False


def test_update_message_rejects_unknown_field() -> None:
    store = _make_store_with(1)
    with pytest.raises(ValueError, match="unknown or protected"):
        store.update_message("id-0", bogus="x")


def test_update_message_rejects_identity_fields() -> None:
    # id / type / timestamp / tool_name / tool_args / diff_file_path are NOT
    # in _UPDATABLE_FIELDS. Even with a real message id, these must raise.
    store = _make_store_with(1)
    for protected in ("id", "type", "timestamp", "tool_name", "tool_args"):
        with pytest.raises(ValueError, match="unknown or protected"):
            store.update_message("id-0", **{protected: "anything"})


def test_update_message_updates_tool_status_field() -> None:
    store = MessageStore()
    store.append(
        MessageData(
            type=MessageType.TOOL, content="", id="t1", tool_name="bash"
        )
    )
    ok = store.update_message("t1", tool_status=ToolStatus.SUCCESS, tool_output="done")
    assert ok is True
    msg = store.get_message("t1")
    assert msg is not None
    assert msg.tool_status == ToolStatus.SUCCESS
    assert msg.tool_output == "done"


# ---------------------------------------------------------------------------
# active message tracking
# ---------------------------------------------------------------------------


def test_set_and_check_active_message() -> None:
    store = MessageStore()
    assert store.is_active("anything") is False
    store.set_active_message("active-1")
    assert store.is_active("active-1") is True
    assert store.is_active("other") is False
    store.set_active_message(None)
    assert store.is_active("active-1") is False


# ---------------------------------------------------------------------------
# window_exceeded + prune flow
# ---------------------------------------------------------------------------


def test_window_exceeded_false_below_window_size() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE)
    assert store.window_exceeded() is False


def test_window_exceeded_true_above_window_size() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 1)
    assert store.window_exceeded() is True


def test_get_messages_to_prune_returns_empty_when_under_limit() -> None:
    store = _make_store_with(10)
    assert store.get_messages_to_prune() == []


def test_get_messages_to_prune_default_count_trims_to_window_size() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 3)
    to_prune = store.get_messages_to_prune()
    assert len(to_prune) == 3
    # Prunes from the START of the visible window.
    assert [m.id for m in to_prune] == ["id-0", "id-1", "id-2"]


def test_get_messages_to_prune_explicit_count_caps_at_visible_end() -> None:
    store = _make_store_with(5)
    to_prune = store.get_messages_to_prune(count=10)
    # Only 5 messages exist, so the loop terminates at visible_end.
    assert len(to_prune) == 5


def test_get_messages_to_prune_stops_at_active_message() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 5)
    # Mark id-2 as the active streaming message — prune must stop before it.
    store.set_active_message("id-2")
    to_prune = store.get_messages_to_prune()
    assert [m.id for m in to_prune] == ["id-0", "id-1"]


def test_get_messages_to_prune_explicit_zero_returns_empty() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 5)
    assert store.get_messages_to_prune(count=0) == []


def test_mark_pruned_advances_visible_start_past_consecutive_ids() -> None:
    store = _make_store_with(5)
    store.mark_pruned(["id-0", "id-1"])
    assert store.get_visible_range() == (2, 5)
    assert store.has_messages_above is True
    assert store.visible_count == 3


def test_mark_pruned_stops_at_first_non_matching_id() -> None:
    store = _make_store_with(5)
    # id-2 not in the prune set — visible_start must stop at index 1.
    store.mark_pruned(["id-0", "id-3"])
    assert store.get_visible_range() == (1, 5)


def test_mark_pruned_ignores_unknown_ids() -> None:
    store = _make_store_with(3)
    store.mark_pruned(["never-existed"])
    assert store.get_visible_range() == (0, 3)


# ---------------------------------------------------------------------------
# hydrate flow
# ---------------------------------------------------------------------------


def test_get_messages_to_hydrate_returns_empty_when_no_archived() -> None:
    store = _make_store_with(5)
    # All messages still visible (visible_start == 0).
    assert store.get_messages_to_hydrate() == []


def test_get_messages_to_hydrate_default_count_uses_buffer() -> None:
    store = _make_store_with(100)
    # Prune the first 20 to simulate scrolled-down state.
    store.mark_pruned([f"id-{i}" for i in range(20)])
    assert store.get_visible_range() == (20, 100)
    to_hydrate = store.get_messages_to_hydrate()
    # Should pull HYDRATE_BUFFER messages immediately above visible window.
    assert len(to_hydrate) == MessageStore.HYDRATE_BUFFER
    expected_start = 20 - MessageStore.HYDRATE_BUFFER
    assert [m.id for m in to_hydrate] == [
        f"id-{i}" for i in range(expected_start, 20)
    ]


def test_get_messages_to_hydrate_explicit_count() -> None:
    store = _make_store_with(50)
    store.mark_pruned([f"id-{i}" for i in range(10)])
    to_hydrate = store.get_messages_to_hydrate(count=3)
    assert [m.id for m in to_hydrate] == ["id-7", "id-8", "id-9"]


def test_get_messages_to_hydrate_count_capped_at_archived_total() -> None:
    store = _make_store_with(10)
    store.mark_pruned(["id-0", "id-1"])
    to_hydrate = store.get_messages_to_hydrate(count=100)
    # Only 2 messages were archived — we can never hydrate more than that.
    assert len(to_hydrate) == 2
    assert [m.id for m in to_hydrate] == ["id-0", "id-1"]


def test_mark_hydrated_decreases_visible_start() -> None:
    store = _make_store_with(10)
    store.mark_pruned([f"id-{i}" for i in range(5)])
    assert store.get_visible_range()[0] == 5
    store.mark_hydrated(3)
    assert store.get_visible_range()[0] == 2


def test_mark_hydrated_floors_at_zero() -> None:
    store = _make_store_with(5)
    store.mark_pruned(["id-0", "id-1"])
    store.mark_hydrated(100)
    assert store.get_visible_range()[0] == 0


# ---------------------------------------------------------------------------
# should_hydrate_above / should_prune_below — scroll-based decisions
# ---------------------------------------------------------------------------


def test_should_hydrate_above_false_when_no_archived() -> None:
    store = _make_store_with(5)
    assert store.should_hydrate_above(scroll_position=0, viewport_height=30) is False


def test_should_hydrate_above_true_near_top_with_archived() -> None:
    store = _make_store_with(10)
    store.mark_pruned(["id-0"])
    # Within 2 * viewport_height of the top.
    assert store.should_hydrate_above(scroll_position=10, viewport_height=30) is True


def test_should_hydrate_above_false_far_from_top() -> None:
    store = _make_store_with(10)
    store.mark_pruned(["id-0"])
    # scroll_position >= 2 * viewport_height.
    assert store.should_hydrate_above(scroll_position=100, viewport_height=30) is False


def test_should_prune_below_false_when_within_window() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE)
    assert (
        store.should_prune_below(
            scroll_position=0, viewport_height=30, content_height=1000
        )
        is False
    )


def test_should_prune_below_true_when_far_from_bottom() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 5)
    # distance_from_bottom = 1000 - 0 - 30 = 970; threshold = 90 → True.
    assert (
        store.should_prune_below(
            scroll_position=0, viewport_height=30, content_height=1000
        )
        is True
    )


def test_should_prune_below_false_when_near_bottom() -> None:
    store = _make_store_with(MessageStore.WINDOW_SIZE + 5)
    # distance_from_bottom = 100 - 50 - 30 = 20; threshold = 90 → False.
    assert (
        store.should_prune_below(
            scroll_position=50, viewport_height=30, content_height=100
        )
        is False
    )


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------


def test_clear_resets_all_state() -> None:
    store = _make_store_with(10)
    store.mark_pruned(["id-0", "id-1"])
    store.set_active_message("id-5")

    store.clear()

    assert store.total_count == 0
    assert store.visible_count == 0
    assert store.has_messages_above is False
    assert store.has_messages_below is False
    assert store.get_visible_range() == (0, 0)
    assert store.is_active("id-5") is False
