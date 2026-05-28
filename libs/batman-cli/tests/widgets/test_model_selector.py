"""Unit tests for `batman_code.widgets.model_selector`.

Covers pure-logic helpers — `_format_option_label` variants,
`_find_current_model_index`, `_update_filtered_list` math, and screen
initialization wiring — without spinning up a Textual app. Layout-bound
methods (`_move_selection`, `_visible_page_size`, scroll handling) are
deferred to Phase 10 end-to-end verification once `app.py` is wired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from batman_code.widgets import model_selector as ms_module
from batman_code.widgets.model_selector import (
    ModelOption,
    ModelSelectorScreen,
)


# ---------------------------------------------------------------------------
# Test fixtures — monkeypatched registry + config
# ---------------------------------------------------------------------------


_FAKE_REGISTRY: dict[str, list[str]] = {
    "anthropic": ["claude-opus-4-7", "claude-sonnet-4-6"],
    "openai": ["gpt-5", "gpt-4o"],
}


@dataclass
class _FakeConfig:
    """Stand-in for `ModelConfig` so screen init doesn't read user's home."""

    default_model: str | None = None


@pytest.fixture(autouse=True)
def _patch_registry_and_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace registry + config loader so ModelSelectorScreen.__init__ is
    deterministic in test runs."""
    monkeypatch.setattr(ms_module, "get_available_models", lambda: _FAKE_REGISTRY)

    class _StubModelConfig:
        @classmethod
        def load(cls, config_path: Any = None) -> _FakeConfig:  # noqa: ARG003
            return _FakeConfig(default_model=None)

    monkeypatch.setattr(ms_module, "ModelConfig", _StubModelConfig)


def _with_default(monkeypatch: pytest.MonkeyPatch, default_spec: str | None) -> None:
    """Helper to override the default-model behaviour for a single test."""

    class _StubModelConfig:
        @classmethod
        def load(cls, config_path: Any = None) -> _FakeConfig:  # noqa: ARG003
            return _FakeConfig(default_model=default_spec)

    monkeypatch.setattr(ms_module, "ModelConfig", _StubModelConfig)


# ---------------------------------------------------------------------------
# ModelOption — attribute storage + Clicked message
# ---------------------------------------------------------------------------


def test_model_option_stores_attributes() -> None:
    opt = ModelOption(
        label="dummy",
        model_spec="anthropic:claude-opus-4-7",
        provider="anthropic",
        index=3,
        has_creds=True,
        classes="model-option",
    )
    assert opt.model_spec == "anthropic:claude-opus-4-7"
    assert opt.provider == "anthropic"
    assert opt.index == 3
    assert opt.has_creds is True


def test_model_option_has_creds_defaults_true() -> None:
    opt = ModelOption(
        label="x", model_spec="p:m", provider="p", index=0
    )
    assert opt.has_creds is True


def test_model_option_clicked_message_carries_fields() -> None:
    msg = ModelOption.Clicked(
        model_spec="openai:gpt-5", provider="openai", index=2
    )
    assert msg.model_spec == "openai:gpt-5"
    assert msg.provider == "openai"
    assert msg.index == 2


# ---------------------------------------------------------------------------
# _format_option_label — pure label builder (static method)
# ---------------------------------------------------------------------------


def test_format_option_label_unselected_uses_two_space_prefix() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=False,
        current=False,
        has_creds=True,
    )
    assert label.startswith("  ")


def test_format_option_label_selected_shows_cursor_glyph() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=True,
        current=False,
        has_creds=True,
    )
    # Cursor glyph means the label does NOT start with the two-space prefix.
    assert not label.startswith("  anthropic")


def test_format_option_label_no_creds_wraps_spec_yellow() -> None:
    label = ModelSelectorScreen._format_option_label(
        "openai:gpt-5",
        selected=False,
        current=False,
        has_creds=False,
    )
    assert "[yellow]openai:gpt-5[/yellow]" in label


def test_format_option_label_unknown_creds_wraps_yellow() -> None:
    # has_creds=None is treated as falsy by the `not has_creds` check.
    label = ModelSelectorScreen._format_option_label(
        "local:llama",
        selected=False,
        current=False,
        has_creds=None,
    )
    assert "[yellow]local:llama[/yellow]" in label


def test_format_option_label_default_wraps_cyan_when_has_creds() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=False,
        current=False,
        has_creds=True,
        is_default=True,
    )
    assert "[cyan]anthropic:claude-opus-4-7[/cyan]" in label


def test_format_option_label_plain_spec_when_has_creds_not_default() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-sonnet-4-6",
        selected=False,
        current=False,
        has_creds=True,
        is_default=False,
    )
    # No yellow wrap (creds present); no cyan wrap (not default).
    assert "[yellow]" not in label
    assert "[cyan]anthropic:claude-sonnet-4-6[/cyan]" not in label
    # Spec still appears unwrapped.
    assert "anthropic:claude-sonnet-4-6" in label


def test_format_option_label_current_appends_current_suffix() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=False,
        current=True,
        has_creds=True,
    )
    # Verbatim form — theming flips this to "(active)" in the next commit.
    assert "(current)" in label


def test_format_option_label_default_appends_default_suffix() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=False,
        current=False,
        has_creds=True,
        is_default=True,
    )
    assert "[cyan](default)[/cyan]" in label


def test_format_option_label_current_and_default_both_appear() -> None:
    label = ModelSelectorScreen._format_option_label(
        "anthropic:claude-opus-4-7",
        selected=False,
        current=True,
        has_creds=True,
        is_default=True,
    )
    assert "(current)" in label
    assert "(default)" in label


# ---------------------------------------------------------------------------
# __init__ — registry expansion + current index resolution
# ---------------------------------------------------------------------------


def test_init_builds_all_models_from_registry() -> None:
    screen = ModelSelectorScreen()
    # Two providers × two models = four entries, preserving (spec, provider).
    assert ("anthropic:claude-opus-4-7", "anthropic") in screen._all_models
    assert ("anthropic:claude-sonnet-4-6", "anthropic") in screen._all_models
    assert ("openai:gpt-5", "openai") in screen._all_models
    assert ("openai:gpt-4o", "openai") in screen._all_models
    assert len(screen._all_models) == 4
    # Filtered list starts as a copy of all_models.
    assert screen._filtered_models == screen._all_models


def test_init_no_current_selects_index_zero() -> None:
    screen = ModelSelectorScreen()
    assert screen._selected_index == 0
    assert screen._current_spec is None


def test_init_builds_current_spec_when_both_set() -> None:
    screen = ModelSelectorScreen(
        current_model="claude-opus-4-7", current_provider="anthropic"
    )
    assert screen._current_spec == "anthropic:claude-opus-4-7"


def test_init_with_current_finds_index() -> None:
    screen = ModelSelectorScreen(
        current_model="gpt-5", current_provider="openai"
    )
    # openai:gpt-5 is third in fake registry (index 2).
    assert screen._selected_index == 2


def test_init_with_current_not_in_registry_falls_back_to_zero() -> None:
    screen = ModelSelectorScreen(
        current_model="nonexistent-model", current_provider="anthropic"
    )
    assert screen._selected_index == 0


def test_init_partial_current_no_current_spec() -> None:
    # Only one of (model, provider) set → no current_spec built.
    screen_a = ModelSelectorScreen(current_model="claude-opus-4-7")
    assert screen_a._current_spec is None

    screen_b = ModelSelectorScreen(current_provider="anthropic")
    assert screen_b._current_spec is None


def test_init_loads_default_spec_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _with_default(monkeypatch, "anthropic:claude-opus-4-7")
    screen = ModelSelectorScreen()
    assert screen._default_spec == "anthropic:claude-opus-4-7"


def test_init_no_default_when_config_default_is_none() -> None:
    screen = ModelSelectorScreen()
    assert screen._default_spec is None


# ---------------------------------------------------------------------------
# _update_filtered_list — case-insensitive search + selection clamping
# ---------------------------------------------------------------------------


def test_update_filtered_list_empty_filter_resets_to_all() -> None:
    screen = ModelSelectorScreen()
    screen._filter_text = "anthropic"
    screen._update_filtered_list()
    assert len(screen._filtered_models) == 2

    # Clear the filter — list should reset to all models.
    screen._filter_text = ""
    screen._update_filtered_list()
    assert screen._filtered_models == screen._all_models


def test_update_filtered_list_filters_case_insensitively() -> None:
    screen = ModelSelectorScreen()
    # Filter text already lowercased by on_input_changed; simulate that.
    screen._filter_text = "anthropic"
    screen._update_filtered_list()
    assert all(spec.startswith("anthropic:") for spec, _ in screen._filtered_models)
    assert len(screen._filtered_models) == 2


def test_update_filtered_list_matches_partial_model_name() -> None:
    screen = ModelSelectorScreen()
    screen._filter_text = "opus"
    screen._update_filtered_list()
    assert screen._filtered_models == [
        ("anthropic:claude-opus-4-7", "anthropic")
    ]


def test_update_filtered_list_clamps_selection_to_last_when_oob() -> None:
    screen = ModelSelectorScreen()
    # Move selection past where the filtered list will end.
    screen._selected_index = 3
    screen._filter_text = "anthropic"  # 2 results → indices 0..1
    screen._update_filtered_list()
    assert screen._selected_index == 1  # clamped to len-1


def test_update_filtered_list_clamps_selection_to_zero_when_empty() -> None:
    screen = ModelSelectorScreen()
    screen._selected_index = 3
    screen._filter_text = "definitely-not-a-model"
    screen._update_filtered_list()
    assert screen._filtered_models == []
    # When the filtered list is empty, max(0, len-1) = max(0, -1) = 0.
    assert screen._selected_index == 0


def test_update_filtered_list_restores_current_index_on_clear() -> None:
    screen = ModelSelectorScreen(
        current_model="gpt-5", current_provider="openai"
    )
    # Apply a filter that drops the current model from view.
    screen._filter_text = "anthropic"
    screen._update_filtered_list()
    # ...then clear it. Selection should snap back to current model's index.
    screen._filter_text = ""
    screen._update_filtered_list()
    assert screen._selected_index == 2  # openai:gpt-5
