# Phase 5b — Next 4 Core Widgets

## Context

Phase 5 first batch (loading, welcome, status) shipped in commits `d18c9cd`, `8cfaa2a`, `283fd2f`. 11 widgets remain.

This session lands the **next 4 widgets**, all small/medium leafs, picked to unlock the bigger chain widgets in future sessions.

## Scope (this session)

| # | Widget | Source LOC | Internal deps | Why this one |
|---|--------|-----------|---------------|--------------|
| 1 | `history.py` | 155 | none | Smallest leaf — chat input history navigation. Unlocks `chat_input.py`. |
| 2 | `diff.py` | 216 | none | Leaf. Unlocks `messages.py` (next session). |
| 3 | `tool_widgets.py` | 245 | none | Leaf base classes for tool-call rendering. Unlocks `tool_renderers.py`. |
| 4 | `tool_renderers.py` | 128 | `tool_widgets.py` | Pairs with #3 — registry/factory for per-tool renderers. Unlocks `approval.py`. |

Source total: 744 LOC. Internal-dep order: 1, 2, 3, 4 (4 depends on 3 within this session).

After this session, only single files block each remaining chain:
- `messages.py` (1257 LOC) — its dep `diff.py` is now ported
- `approval.py` — its chain `tool_renderers.py` → `tool_widgets.py` is now ported
- `chat_input.py` — needs `autocomplete.py` + `history.py` (history now ported, autocomplete still pending)

Plus update `widgets/__init__.py` to re-export new public classes.

## Critical Files

**Sources:**
- `libs/cli/deepagents_cli/widgets/history.py`
- `libs/cli/deepagents_cli/widgets/diff.py`
- `libs/cli/deepagents_cli/widgets/tool_widgets.py`
- `libs/cli/deepagents_cli/widgets/tool_renderers.py`

**Targets (NEW):**
- `libs/batman-cli/batman_code/widgets/history.py`
- `libs/batman-cli/batman_code/widgets/diff.py`
- `libs/batman-cli/batman_code/widgets/tool_widgets.py`
- `libs/batman-cli/batman_code/widgets/tool_renderers.py`

**Targets (UPDATE):**
- `libs/batman-cli/batman_code/widgets/__init__.py` — add new re-exports.

## Per-Widget Theming Decisions

### `history.py` — verbatim port
No color references in source. Pure keyboard-history logic. Just remap imports.

### `diff.py` — verbatim port
Source uses `#2d1515` / `#152d15` background tints for removed/added lines. These are universal diff conventions (not branding) — leave verbatim. Project palette `error`/`success` colors are foreground; these are background tints, different role.

### `tool_widgets.py` — verbatim port
Same diff-tint hardcodes as `diff.py` (`#4a2020`, `#1e4620`, `#ff8787`, `#8ce99a`). Universal +/− conventions. Leave verbatim.

### `tool_renderers.py` — verbatim port
Pure dispatch registry. Only widget dep is `tool_widgets` (now in batman_code).

## Import Remapping (applies to all 4 files)

| Source | Batman |
|--------|--------|
| `from deepagents_cli.config import ...` | `from batman_code.config import ...` |
| `from deepagents_cli.widgets.tool_widgets import ...` | `from batman_code.widgets.tool_widgets import ...` |
| `from deepagents_cli._version ...` | `from batman_code._version ...` |

## Commit Strategy

5 commits:

1. `docs: add tasks/phase5b-plan.md` — plan doc.
2. `feat(batman-cli): port history.py` — file 1 + import smoke test.
3. `feat(batman-cli): port diff.py` — file 2 + import smoke test.
4. `feat(batman-cli): port tool_widgets.py` — file 3 + import smoke test.
5. `feat(batman-cli): port tool_renderers.py + widgets re-exports` — file 4, plus `__init__.py` update.

## Verification

After each port, from `libs/batman-cli/`:

```bash
uv run python -c "from batman_code.widgets.history import HistoryManager; print('history OK')"
uv run python -c "from batman_code.widgets.diff import format_diff_textual; print('diff OK')"
uv run python -c "from batman_code.widgets.tool_widgets import *; print('tool_widgets OK')"
uv run python -c "from batman_code.widgets.tool_renderers import get_renderer; print('tool_renderers OK')"
```

Visual verification deferred until Phase 8 (`app.py` wiring).

## Out of Scope (deferred)

- `messages.py` (1257 LOC) — dedicated session
- `approval.py` (331 LOC)
- `chat_input.py` (749 LOC) + `autocomplete.py` (630 LOC)
- `model_selector.py` (630 LOC), `thread_selector.py` (545 LOC)
- `message_store.py` (580 LOC)

## Final Doc Updates (end of session)

- Update `tasks/todo.md` — mark Phase 5 progress (7 of 14 widgets ported).
- Update memory `MEMORY.md` — bump Phase 5 status, list newly ported files, set NEXT for next session.
