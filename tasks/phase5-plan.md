# Phase 5 — Core Widgets — Implementation Plan

## Context

Phase 5 ports 14 widget files from `libs/cli/deepagents_cli/widgets/` → `libs/batman-cli/batman_code/widgets/`. Phases 0-4 are complete; the agent layer (`agent.py`, `ui.py`, `input.py`) is wired and verified. Phase 5 is the largest phase by file count, so it spans **multiple sessions**.

**This session lands the first 3 widgets.** All three are leaf widgets (zero `widgets.*` internal dependencies), so they can be ported, verified, and committed independently without half-finished imports. They're also the highest-impact / lowest-risk picks: once Phase 8 wires `app.py`, the user immediately sees the bat-spinner, Gotham welcome, and DETECTIVE / DARK KNIGHT mode indicator working together.

**Out of scope for this session, deferred to future Phase 5 sessions:**
- `messages.py` (1,257 LOC) + `diff.py` (its dependency) — large, central, deserves a dedicated session.
- Approval chain: `approval.py` → `tool_renderers.py` → `tool_widgets.py`
- Input chain: `chat_input.py` → `autocomplete.py` + `history.py`
- Standalone selectors / store: `model_selector.py`, `thread_selector.py`, `message_store.py`

---

## Files to Create / Modify (this session)

| File | Action | Source | Source LOC |
|------|--------|--------|-----------|
| `batman_code/widgets/loading.py` | NEW | `deepagents_cli/widgets/loading.py` | 173 |
| `batman_code/widgets/welcome.py` | NEW | `deepagents_cli/widgets/welcome.py` | 134 |
| `batman_code/widgets/status.py` | NEW | `deepagents_cli/widgets/status.py` | 277 |
| `batman_code/widgets/__init__.py` | UPDATE | mirror source export shape, but only export ported classes | currently 1 line |

---

## Per-Widget Theming Decisions

### `loading.py`
- **Spinner frames**: Hardcoded `("( \\  )", "(  \\ )", "(  / )", "( /  )")` bat-wing flutter directly in the widget (do not modify `Glyphs.spinner_frames` in config; the unicode glyph set retains its Braille spinner for any other potential consumers).
- **Spinner color**: Replace hardcoded `[#FFD800]` with `COLORS["bat_gold"]` (`#f5c518`).
- **Status messages rotate every 5s** through Gotham pool:
  - "Analyzing with the Batcomputer"
  - "Consulting the case files"
  - "Scanning Gotham"
  - "Running forensics"
- **Default status**: First message in the rotation (`"Analyzing with the Batcomputer"`) instead of `"Thinking"`.
- **Paused state**: `[dim]>==<[/dim]` using compact bat-symbol from `get_glyphs().bat_symbol` (`>==|==<`) — keep verbatim but render dim.
- **Elapsed-time / pause / resume / stop**: verbatim port.

### `welcome.py`
- **Banner**: Reuse `get_banner()` (already returns BAT CODE ASCII art from config).
- **Welcome message**: Random pick from Gotham pool replaces `"Ready to code! What would you like to build?"`:
  - "Gotham needs you."
  - "The night is darkest just before the dawn."
  - "I am vengeance."
  - "The Batcomputer is online."
- **LangSmith utm_source**: `?utm_source=deepagents-cli` → `?utm_source=bat-code` (2 occurrences).
- **Bottom hint line**: keep verbatim (`Enter send • Ctrl+J newline • @ files • / commands`).
- **Persona display**: NOT shown in welcome banner this session (welcome.py source doesn't take persona; persona display will land with `app.py` in Phase 8 or via a small follow-up if needed). Plan doc for that session can add it.

### `status.py`
- **Mode labels** (`watch_mode`):
  - `"bash"` mode: indicator text `"BASH"` → `"THE CAVE"`
  - `"command"` mode: indicator text `"CMD"` → `"BATCOMPUTER"`
- **Auto-approve labels** (`watch_auto_approve`):
  - On: `"auto | shift+tab to cycle"` → `"DARK KNIGHT MODE | shift+tab to cycle"`
  - Off: `"manual | shift+tab to cycle"` → `"DETECTIVE MODE | shift+tab to cycle"`
- **CSS color overrides** (in `DEFAULT_CSS`):
  - `.status-mode.bash` background `#ff1493` → `#1a3a5c` (gotham_blue) — THE CAVE feels like a bat-cave, not pink.
  - `.status-mode.command` background `#8b5cf6` → `#2d2d4e` (tool/violet) — BATCOMPUTER stays slightly violet.
  - `.status-auto-approve.on` background `#10b981` (green) → `#8b0000` (error red, danger) — DARK KNIGHT MODE is dangerous.
  - `.status-auto-approve.off` background `#f59e0b` (amber) → `#1a3a5c` (gotham_blue) — DETECTIVE MODE is calm.
  - Token color: append `color: #f5c518` to `.status-tokens` for bat-gold counter.
- **Everything else** (counters, key handlers, refresh logic, watchers): verbatim.

### `widgets/__init__.py`
After all 3 widgets land, update from:
```python
"""bat-code UI widgets."""
```
to:
```python
"""bat-code UI widgets."""

from __future__ import annotations

from batman_code.widgets.loading import LoadingWidget, Spinner
from batman_code.widgets.status import StatusBar
from batman_code.widgets.welcome import WelcomeBanner

__all__ = ["LoadingWidget", "Spinner", "StatusBar", "WelcomeBanner"]
```
The remaining source exports (`AppMessage`, `AssistantMessage`, `ChatInput`, `DiffMessage`, `ErrorMessage`, `ToolCallMessage`, `UserMessage`) will be added in subsequent Phase 5 sessions.

---

## Import Remapping (applies to all 3 files)

| Source | Batman |
|--------|--------|
| `from deepagents_cli.config import COLORS, _is_editable_install, fetch_langsmith_project_url, get_banner, get_glyphs, get_langsmith_project_name` | `from batman_code.config import ...` |
| `from deepagents_cli.config import settings` | `from batman_code.config import settings` |
| `from deepagents_cli.config import get_glyphs` | `from batman_code.config import get_glyphs` |

Textual / Rich / stdlib imports stay unchanged.

---

## Commit Strategy (matches user's small-commit preference)

4 commits, each independently verifiable:

1. `docs: add tasks/phase5-plan.md` — this file.
2. `feat(batman-cli): port loading.py with bat-wing spinner` — file 1 + smoke test.
3. `feat(batman-cli): port welcome.py with Gotham banner` — file 2 + smoke test.
4. `feat(batman-cli): port status.py with DETECTIVE/DARK KNIGHT modes` — file 3 + `__init__.py` re-exports + smoke test.

Per user preference: pause for approval before each commit; commit only when user asks.

---

## Verification

After each widget lands, from `libs/batman-cli/`:

```bash
# Import smoke test (per widget)
uv run python -c "from batman_code.widgets.loading import LoadingWidget, Spinner; print('loading OK')"
uv run python -c "from batman_code.widgets.welcome import WelcomeBanner; print('welcome OK')"
uv run python -c "from batman_code.widgets.status import StatusBar; print('status OK')"

# After __init__.py update — re-exports work
uv run python -c "from batman_code.widgets import LoadingWidget, WelcomeBanner, StatusBar; print('init OK')"

# Lint
uv run ruff check batman_code/widgets/loading.py batman_code/widgets/welcome.py batman_code/widgets/status.py

# Confirm theming constants resolve
uv run python -c "from batman_code.config import COLORS; assert COLORS['bat_gold'] == '#f5c518'; assert COLORS['gotham_blue'] == '#1a3a5c'; assert COLORS['error'] == '#8b0000'; print('palette OK')"
```

Visual verification deferred until Phase 8 (`app.py`) wires these into a runnable Textual app — same pattern used for Phase 4.

---

## Risks / Notes

1. **`Glyphs.spinner_frames` (UNICODE) is Braille, not bat-wing.** Decision: hardcode bat-wing frames in `loading.py` rather than mutate config. Keeps phase scope tight; config can be revisited later if other consumers need glyph parity.
2. **Status message rotation is a NEW feature** not in source `loading.py`. Implemented via a second `set_interval` (5s) that advances a rotation index and calls `set_status`. Resets the index on `pause` / `resume` / `set_status` so caller-set status sticks.
3. **Welcome banner is post-splash header.** It coexists with `batcave.py`'s splash (Phases 6a/6b). Keep welcome compact; the cinematic ASCII lives in batcave, not here.
4. **`__init__.py` partial export.** Only exports the 4 names that exist after this session. The full source has 9. Subsequent Phase 5 sessions extend the export list.

---

## Critical Files Reference

| File | Role |
|------|------|
| `libs/cli/deepagents_cli/widgets/loading.py` | Source for `loading.py` |
| `libs/cli/deepagents_cli/widgets/welcome.py` | Source for `welcome.py` |
| `libs/cli/deepagents_cli/widgets/status.py` | Source for `status.py` |
| `libs/cli/deepagents_cli/widgets/__init__.py` | Source for export shape reference |
| `libs/batman-cli/batman_code/config.py` | `COLORS`, `get_banner`, `get_glyphs`, `_is_editable_install`, LangSmith helpers, `settings` |
| `libs/batman-cli/batman_code/app.tcss` | Existing Batman palette CSS (no changes expected this session) |
| `tasks/todo.md` | Phase 5 checklist (lines 172-235) |
