# Phase 5 — Core Widgets — Consolidated Plan

This is the single source of truth for Phase 5 (porting 14 widgets from
`libs/cli/deepagents_cli/widgets/` → `libs/batman-cli/batman_code/widgets/`).

Phase 5 spans multiple sessions. Status here is **authoritative**; the
matching one-liners in `tasks/todo.md` and the per-widget memory notes in
`MEMORY.md` track the same state from different angles.

---

## Scope — all 14 widgets

| # | Widget | LOC | Internal deps | Status | Notes |
|---|--------|-----|---------------|--------|-------|
| 1 | `loading.py` | 173 | none | **DONE** (batch 1) | Bat-wing spinner, Gotham status rotation |
| 2 | `welcome.py` | 134 | none | **DONE** (batch 1) | Gotham welcome pool, bat-code utm_source |
| 3 | `status.py` | 277 | none | **DONE** (batch 1) | DETECTIVE / DARK KNIGHT, THE CAVE / BATCOMPUTER labels |
| 4 | `history.py` | 155 | none | **DONE** (batch 2) | Chat-input history (verbatim) |
| 5 | `diff.py` | 216 | none | **DONE** (batch 2) | Unified diff (verbatim — diff tints are universal, not branding) |
| 6 | `tool_widgets.py` | 245 | none | **DONE** (batch 2) | Tool-approval widgets (verbatim) |
| 7 | `tool_renderers.py` | 128 | `tool_widgets` | **DONE** (batch 2) | Renderer registry (verbatim) |
| 8 | `messages.py` | 1258 | `diff` | **DONE** (batch 3) | "Villain Detected" error label; bat-gold assistant border |
| 9 | `approval.py` | 331 | `tool_renderers` | **DONE** (batch 4) | "Gotham Requires Authorization" title; Authorize/Deny/Auto-Authorize labels |
| 10 | `autocomplete.py` | 630 | none | **DONE** (batch 5) | Verbatim — slash commands are functional IDs, no theming surface |
| 11 | `thread_selector.py` | 545 | none | **DONE** (batch 6) | "Case Files" / "(active)" theming + 15 unit tests |
| 12 | `message_store.py` | 580 | none | **DONE** (batch 7) | Pure verbatim (storage layer) + 47 unit tests |
| 13 | `model_selector.py` | 630 | none | **DONE** (batch 8) | "Batcomputer Models" title + "(active)" marker; 30 unit tests |
| 14 | `chat_input.py` | 749 | `history` + `autocomplete` + `messages` | **DONE** (batch 9) | History path fix + ASCII border align; 44 unit tests |

**Done:** 14 / 14 (~6,051 LOC). **Remaining:** 0. **Phase 5 COMPLETE.**

---

## Conventions established during Phase 5

Apply these to every remaining widget port:

### 1. Commit style (per `feedback_commit_style.md`)

- **Pure verbatim port** (no theming, no theming-tests): 1 commit —
  `feat(batman-cli): port <widget>.py (verbatim)`.
- **Verbatim port with theming**: split into 2+ commits — `feat: port` then
  `feat: theme` then `test: cover ...` then `docs: mark complete`. One
  concern per commit so review and rollback stay surgical.
- **Test infra changes**: separate `chore` commit
  (e.g., `chore(batman-cli): add pytest dev group + tests/ scaffold`).

### 2. Test-alongside policy (per `feedback_always_test.md` / `lessons.md`)

Every port ships pytest unit tests **in the same workstream**.
- Cover pure-logic helpers (formatters, label builders, parsers, state
  transitions). Skip Textual layout — covered indirectly by the import
  smoke test plus Phase 10 end-to-end verification.
- Theming changes get **explicit assertions** on themed strings, plus a
  regression guard against upstream wording.
- Run with `cd libs/batman-cli && uv run --group dev pytest`.

### 3. `widgets/__init__.py` re-export rule

Source's `widgets/__init__.py` re-exports the message/chat surface only.
Mirror that:
- **Re-exported** (used as `from batman_code.widgets import X`):
  `AppMessage`, `AssistantMessage`, `DiffMessage`, `ErrorMessage`,
  `LoadingWidget`, `Spinner`, `StatusBar`, `ToolCallMessage`,
  `UserMessage`, `WelcomeBanner`.
- **Deep import only** (selectors, approvals, controllers): `approval.py`,
  `autocomplete.py`, `thread_selector.py`, eventually `model_selector.py`,
  `chat_input.py`, `message_store.py`. Import as
  `from batman_code.widgets.<name> import <X>`.
- `FormattedOutput` and `QueuedUserMessage` stay internal — match source.

### 4. Import remapping (all widgets)

| Source | Batman |
|--------|--------|
| `from deepagents_cli.config import ...` | `from batman_code.config import ...` |
| `from deepagents_cli.sessions import ...` | `from batman_code.sessions import ...` |
| `from deepagents_cli._version import ...` | `from batman_code._version import ...` |
| `from deepagents_cli.widgets.X import ...` | `from batman_code.widgets.X import ...` |

Textual / Rich / stdlib imports stay unchanged. Run `grep -r "deepagents_cli"
libs/batman-cli/` after each port — must return zero hits.

### 5. Theming guidance (when to theme, when not to)

- **Theme**: screen titles, prompt labels, mode indicators, loading/empty/
  error states, status-bar mode names, anything narrative-facing.
- **Don't theme**: column headers (data labels), key bindings, functional
  identifiers (slash command names, tool names, file paths, error codes),
  universal diff tints (`#2d1515` / `#152d15` etc — they're conventions, not
  branding).
- When in doubt: ask "is this chrome or content?" Chrome stays functional;
  content gets the Gotham voice.

---

## Completed batches — commit log

### Batch 1 — Foundational chrome (3 widgets)

- `d18c9cd` feat: port loading.py — bat-wing spinner, 4-message Gotham
  status rotation (5s), bat-gold color, `[dim]>==<[/dim]` paused state
- `8cfaa2a` feat: port welcome.py — random Gotham welcome pool, bat-code
  utm_source for LangSmith
- `283fd2f` feat: port status.py — DETECTIVE / DARK KNIGHT MODE labels,
  THE CAVE / BATCOMPUTER mode labels, bat-gold token counter

### Batch 2 — Verbatim leaf ports (4 widgets)

- `9f981d4` feat: port history.py — chat-input HistoryManager (JSON-lines,
  append-only)
- `f6ed20c` feat: port diff.py — format_diff_textual + EnhancedDiff
  (universal +/- tints kept verbatim)
- `589b400` feat: port tool_widgets.py — ToolApprovalWidget base +
  Generic/WriteFile/EditFile widgets
- `abc5f2c` feat: port tool_renderers.py + widgets re-exports — get_renderer()
  registry (write_file, edit_file)

### Batch 3 — `messages.py` (1 widget, split per commit-style)

- `61038f4` feat: port messages.py — 1258-LOC port: UserMessage,
  QueuedUserMessage, AssistantMessage, ToolCallMessage, DiffMessage,
  ErrorMessage, AppMessage + FormattedOutput dataclass + tool-output
  formatter dispatch (todos / ls / file / search / shell / web / task)
- `01728dc` feat: apply Batman theming to messages.py — ErrorMessage
  label "Villain Detected:", AssistantMessage bat-gold (#f5c518) wide
  border-left with ASCII fallback

### Batch 4 — `approval.py` (1 widget, split per commit-style)

- `69b62ea` feat: port approval.py — 331-LOC port: ApprovalMenu HITL
  Container with focus-trapped key bindings (y/n/a quick keys, arrow nav,
  Enter select, e to expand long shell commands), three options, tool-renderer
  dispatch via `get_renderer()` for non-shell tools, minimal display for
  shell tools (command shown inline, truncated > 120 chars)
- `2d2c48c` feat: apply Batman theming to approval.py — title prefix
  "Gotham Requires Authorization: {tool/count}", option labels Authorize/
  Deny/Auto-Authorize Session (singular and plural), help text "Esc deny"

### Batch 5 — `autocomplete.py` (1 widget, pure verbatim)

- `0046a66` feat: port autocomplete.py — 630-LOC: CompletionResult enum,
  CompletionView + CompletionController Protocols, SLASH_COMMANDS list
  (12 entries), SlashCommandController, FuzzyFileController (git ls-files
  with glob fallback, fuzzy scoring via SequenceMatcher; aliased as
  PathCompletionController for backwards compat), MultiCompletionManager
  dispatcher. Content-identical to source — `/batsignal` intentionally NOT
  added to SLASH_COMMANDS (handler + widget land together in Phase 7).

### Batch 9 — `chat_input.py` (1 widget, port+fixes bundled + tests + docs)

- `253c4f5` feat: port chat_input.py + re-export from widgets/__init__.py
  — 749-LOC port: ChatInput (Vertical container with prompt + TextArea +
  completion popup), ChatTextArea (TextArea subclass with custom key
  handling for submit / newline / history / completion), CompletionOption
  (clickable popup row), CompletionPopup (VerticalScroll holding option
  rows). Three surgical changes vs source:
  (1) three import remaps (`deepagents_cli.config` /
      `.widgets.autocomplete` / `.widgets.history` → `batman_code.*`);
  (2) hardcoded history-file default `~/.deepagents/history.jsonl` →
      `~/.bat-code/history.jsonl` (correctness — keeps chat history in
      bat-code's data dir alongside sessions, doesn't share state with
      deepagents-cli);
  (3) ASCII-fallback border color `"cyan"` → `"yellow"` so ASCII users
      get a gold-toned input border consistent with the Unicode `$primary`
      rendering.
  Re-exported `ChatInput` from `widgets/__init__.py` per source
  convention (ChatTextArea / CompletionOption / CompletionPopup stay
  internal). Prompt glyph `>`, mode names, key bindings, DEFAULT_CSS
  all kept verbatim — operational, not chrome.
- `8f98625` test: cover chat_input.py ported logic — 44 unit tests
  covering CompletionOption / CompletionPopup / ChatTextArea / ChatInput
  message payloads, `__init__` wiring (history path regression guard,
  cwd defaults + promotion, initial component state), parametrized
  mode-detection signal mirroring `on_text_area_changed`'s prefix logic,
  `_get_cursor_offset` math (single/multi-line + all clamp paths),
  `replace_completion_range` (slash / file-mention / directory / bounds
  clamping / multi-line cursor placement), `value` / `input_widget`
  properties. Skips Textual-bound key handlers + async popup mounting.
  Full suite: **136 passed** (44 new + 30 model_selector + 47
  message_store + 15 thread_selector).

### Batch 8 — `model_selector.py` (1 widget, port + tests + theming + tests bundled)

- `5f361f1` feat: port model_selector.py (verbatim) — 630-LOC port:
  `ModelSelectorScreen` (ModalScreen) + `ModelOption` (Static) for the
  `/model` command. Only changes vs source: the two top-level imports
  remapped (`deepagents_cli.config` → `batman_code.config`,
  `deepagents_cli.model_config` → `batman_code.model_config`).
- `6e1f41d` test: cover model_selector.py ported logic — 26 unit tests
  covering `ModelOption` attribute storage, `ModelOption.Clicked` message,
  `_format_option_label` branch combinations (cursor/spec/current/default,
  has_creds variants including None), `__init__` registry expansion +
  current-index resolution + default-spec wiring (autouse monkeypatch
  fixture for `get_available_models` and `ModelConfig`),
  `_update_filtered_list` (case-insensitive, partial match, selection
  clamping, restore-on-clear).
- `b125378` feat: apply Gotham theming to model_selector.py + adapt tests
  — title "Select Model" → "Batcomputer Models" (with "active: ..."
  variant), `(current)` → `(active)` marker. Extracted inline title
  builder into `_build_title()` for testability (same seam pattern as
  thread_selector). Updated 2 existing tests to assert themed wording +
  added 4 new `_build_title` tests (no-active / full-active / model-only
  / provider-only) — all with explicit regression guards against upstream
  wording ("Select Model" not in title, "(current)" not in label).
  Credential indicators / "(default)" suffix / help text / status
  messages / provider headers kept functional per "chrome vs content"
  convention.

### Batch 7 — `message_store.py` (1 widget, pure verbatim + tests)

- `c59b94c` feat: port message_store.py (verbatim) — 580-LOC port:
  `MessageType` / `ToolStatus` StrEnums, `MessageData` dataclass with
  `__post_init__` validation (TOOL requires `tool_name`) and lazy
  `to_widget`/`from_widget` round-trip helpers, `MessageStore` with sliding
  visible window, active-message protection during prune, update_message
  allowlist gating, scroll-based `should_hydrate_above` /
  `should_prune_below` heuristics. Only changes vs source: the two lazy
  `from deepagents_cli.widgets.messages import ...` statements →
  `from batman_code.widgets.messages import ...`. No Gotham theming (pure
  data layer, no UI surface). Kept as deep import per source convention.
- `2fbc824` test: cover message_store.py ported logic — 47 unit tests in
  `tests/widgets/test_message_store.py` covering enum values, MessageData
  defaults + validation, MessageStore append/lookup/update gating,
  window/prune/hydrate math, scroll-based heuristics, and clear. Skips
  `to_widget`/`from_widget` (Textual widget construction — covered by
  import smoke test + Phase 10). Full suite: 62 passed.

### Batch 6 — `thread_selector.py` (1 widget, split + test infra + lessons)

- `012fae8` feat: port thread_selector.py (verbatim) — 545-LOC port:
  ThreadSelectorScreen (ModalScreen) + ThreadOption (Static) for /threads
- `e051a3a` chore: add pytest dev group + tests/ scaffold —
  [dependency-groups.dev] pytest + pytest-asyncio,
  [tool.pytest.ini_options] testpaths=['tests'] asyncio_mode='auto'
- `de14a3c` docs: capture testing lesson learned — tasks/lessons.md
- `2e91bad` test: cover thread_selector.py ported logic — 15 unit tests
- `47ee297` feat: apply Gotham case-file theming — title "Case Files"
  (active: ...), "Pulling case files from the Batcomputer...", "No case
  files on record", "Case files unreachable: ...", "(current)" → "(active)"

---

## Remaining work — none

Phase 5 is **complete**. All 14 widgets ported, 136 unit tests passing,
zero `deepagents_cli` references anywhere under `libs/batman-cli/`.

Next: Phase 8 — `textual_adapter.py` (streaming → UI bridge) +
`app.py` (BatmanApp shell, layered containers, mode toggling). All
ported widgets get wired together there.

---

## Verification recipe (per widget)

From `libs/batman-cli/`:

```powershell
# 1. Import smoke test
uv run python -c "from batman_code.widgets.<name> import <Class>; print('<name> OK')"

# 2. Re-exports (if updated)
uv run python -c "from batman_code.widgets import <Class>; print('init OK')"

# 3. Zero deepagents_cli references
grep -r "deepagents_cli" libs/batman-cli/   # must be empty

# 4. Unit tests
uv run --group dev pytest tests/widgets/test_<name>.py -v

# 5. Full suite (regression guard)
uv run --group dev pytest
```

Full visual verification deferred to Phase 10 once `app.py` (Phase 8)
wires everything into `BatmanApp`.

---

## Critical file references

| File | Role |
|------|------|
| `libs/batman-cli/batman_code/config.py` | `COLORS`, `get_banner`, `get_glyphs`, `_is_editable_install`, LangSmith helpers, `settings` |
| `libs/batman-cli/batman_code/app.tcss` | Batman palette CSS (occasional CSS additions per widget) |
| `libs/batman-cli/batman_code/widgets/__init__.py` | Re-export surface (message/chat classes only) |
| `libs/batman-cli/batman_code/sessions.py` | `ThreadInfo`, `format_timestamp`, `list_threads` (used by selectors) |
| `libs/batman-cli/tests/` | pytest suite, mirrors `batman_code/` layout |
| `tasks/todo.md` | Phase 5 checklist (lines 172-end) — kept in sync per commit |
| `tasks/lessons.md` | Standing rules captured from user corrections |
| `tasks/deferred.md` | Punted work (Phase 7 batsignal, easter eggs, approval.py Esc gap) |
| `CLAUDE.md` | Project vision and spec |
