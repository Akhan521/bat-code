# Phase 8 — Textual Adapter & Main App — COMPLETE

**Status**: Both batches landed and pushed to `origin/main`.
**Suite: 243 passed** (zero `deepagents_cli` refs anywhere under
`libs/batman-cli/`; only remaining `deepagents.*` refs are SDK imports
`from deepagents.backends import ...` which reference the first-party
deepagents package, not deepagents-cli).

Batch 10 (`textual_adapter.py`, 895 LOC): 4 commits `8a5de62..07227ed`.
Batch 11 (`app.py`, 2094 LOC + messages.py touchup): 8 commits
`da674a3..ef567d2`.

Next: **Phase 9 — `main.py` CLI entry** (see `tasks/todo.md` Phase 9
section for the checklist).

---

# Phase 8 — Textual Adapter & Main App — Implementation Plan

This is the **single source of truth for Phase 8** (porting the streaming
→ UI bridge + main Textual application). Mirrors the structure of
`tasks/phase5-plan.md`. Status here is **authoritative**; matching
one-liners in `tasks/todo.md` Phase 8 section and per-batch memory
notes track the same state from different angles.

---

## Context

Phase 5 closed with all 14 widgets ported + 136 unit tests passing.
Phase 8 wires the ported widgets + `create_batman_agent()` (Phase 4)
into a runnable Textual app. This is the **first phase where bat-code
becomes actually launchable** (after Phase 9 adds the CLI entry).

Implementation order per `MEMORY.md`:
`0 → 6 → 1 → 2 → 3 → 4 → 5 → 8 → 9 → 7 → 10`

---

## Scope — 2 source files, ~3,000 LOC

| # | Source | LOC | Target | Notes |
|---|--------|-----|--------|-------|
| 1 | `libs/cli/deepagents_cli/textual_adapter.py` | 895 | `batman_code/textual_adapter.py` | Streaming bridge; narrow theming surface (3 strings) |
| 2 | `libs/cli/deepagents_cli/app.py` | 2094 | `batman_code/app.py` | Main App shell; large theming surface (~15+ strings) |

**Total to port:** ~2,989 LOC across 2 files. **Plus** small touchup
to `batman_code/widgets/messages.py` to close the deferred `UserMessage`
"Gotham Citizen" item from Phase 5.

---

## Confirmed decisions (locked at planning time)

| # | Decision | Choice |
|---|----------|--------|
| 1 | App title (replaces `"Deep Agents"`) | **`"bat-code"`** — matches CLI command + package + repo |
| 2 | `UserMessage` theming scope | Color swap (`#10b981` → `COLORS["gotham_blue"]` `#1a3a5c`) **+** `"Gotham Citizen:"` prefix above content |
| 3 | Joker startup warning modal | Lands in **Phase 8 / app.py** — `BatmanApp(persona=...)` + conditional mount in `on_mount` |
| 4 | `app.py` port commit shape | **Single 2094-LOC verbatim commit** — matches Batch 3 messages.py shape (1258 LOC, also one commit) |
| 5 | `REMEMBER_PROMPT` (347 lines) | Verbatim port + minimal `s/deepagents-cli/bat-code/g` substitution — it's an agent-facing prompt, not display chrome |
| 6 | Splash mount | `BatmanApp(no_splash: bool = False)` + conditional push in `on_mount`; flag flows from Phase 9 main.py → constructor |

---

## Exploration findings (from parallel Explore agents during planning)

### `textual_adapter.py` is straightforward

- **All 4 non-widget deps already in `batman_code/`**: `file_ops`,
  `image_utils`, `input`, `ui`. **No deferred imports.**
- **All 4 message widgets** it imports (`AssistantMessage`,
  `ToolCallMessage`, `DiffMessage`, `AppMessage`) ported + re-exported.
- **Three hardcoded user-facing strings only**: `"Thinking"`
  (lines 295, 414), `"Interrupted by user"` (lines 774, 817),
  `"Command rejected. Tell the agent what you'd like instead."` (line 757).
- **Public surface**: `TextualUIAdapter` class (callback container) +
  `execute_task_textual()` async function (main dispatch entry).
- **Pure-logic seams** (unit-testable without mounting):
  - `_build_stream_config` (line 46) — config dict builder
  - `_is_summarization_chunk` (line 78) — metadata predicate
  - `_build_interrupted_ai_message` (line 181) — text/tool reconstruction

### `app.py` is much bigger but well-mapped

- **4 classes**: `QueuedMessage` (dataclass), `TextualTokenTracker`,
  `TextualSessionState`, `DeepAgentsApp(App)`.
- **Module helpers**: iTerm2 cursor escape hooks, `_COMMAND_URLS`
  dict (changelog/docs/feedback → URLs — needs repointing to bat-code
  repo), `REMEMBER_PROMPT` (347-line prompt).
- **Slash-command dispatch**: clean if-elif chain at line 1075 —
  matches `tasks/deferred.md`'s wish that `/batsignal` plug in as a
  one-line elif in Phase 7. **No dispatch refactor needed.**
- **Modal screen wiring**: `push_screen(callback)` pattern (not
  `push_screen_wait`). `ModelSelectorScreen` + `ThreadSelectorScreen`
  both already ported.
- **Theming surface**: ~15+ user-facing strings — app `TITLE`, help
  text, command confirmations, error messages, etc.
- **All 10 widget imports** are ported and ready to slot in.

### `UserMessage` theming gap (discovered during planning)

`batman_code/widgets/messages.py` `UserMessage` still uses upstream
green (`#10b981`) for the `> ` prefix + wide `border-left`. Phase 5
messages.py theming only touched `ErrorMessage` label +
`AssistantMessage` border. Closing this gap is a small Phase 8
follow-up bundled with the app.py theming commit.

---

## Conventions (unchanged from Phase 5)

All Phase 5 conventions apply verbatim — see `tasks/phase5-plan.md`
Conventions section for the full text. Quick reminders:

1. **Commit style** (`feedback_commit_style.md`): split port from
   theming from tests from docs. One concern per commit.
2. **Test-alongside** (`feedback_always_test.md`): every port ships
   pytest unit tests in the same workstream.
3. **Re-export rule**: `textual_adapter.py` and `app.py` aren't
   widgets, so **no** `widgets/__init__.py` change. Import as
   `from batman_code.textual_adapter import TextualUIAdapter,
   execute_task_textual` and `from batman_code.app import BatmanApp`
   (the latter only from Phase 9's `main.py`).
4. **Import remap**: all `deepagents_cli.*` → `batman_code.*`. Run
   `grep -r "deepagents_cli" libs/batman-cli/` after each port — must
   return zero.
5. **Theming guidance**: chrome (titles, modal labels, mode names,
   status confirmations, error messages) gets Gotham voice; functional
   IDs (slash command names, key bindings, dict keys, env-var names)
   stay verbatim. Ask: "is this chrome or content?"

---

## Batch 10 — `textual_adapter.py` (small, narrow theming)

**Expected commit shape**: 3-4 commits.

1. **`feat(batman-cli): port textual_adapter.py (verbatim)`** —
   895-LOC port. Only changes:
   - 5 import remaps: `deepagents_cli.{file_ops, image_utils, input,
     ui, widgets.messages}` → `batman_code.*`.
   - Behavioral: zero changes.
   - Theming: deferred to commit 3.
2. **`test(batman-cli): cover textual_adapter.py pure-logic helpers`**
   — ~15-25 tests for:
   - `_build_stream_config` — config dict shape, thread_id /
     assistant_id pass-through.
   - `_is_summarization_chunk` — metadata predicate truth table.
   - `_build_interrupted_ai_message` — text/tool reconstruction edge
     cases (no pending text, no tool calls, both present).
   - Skips `execute_task_textual` (640-line async loop — Phase 10
     end-to-end).
3. **`feat(batman-cli): theme textual_adapter.py narrative strings`**
   — three string replacements (Gotham wording for `"Thinking"`,
   `"Interrupted by user"`, command rejection message). Exact wording
   chosen at implementation time — surface options to user if
   uncertain.
4. **`test(batman-cli): cover textual_adapter.py theming`** — assert
   themed strings appear + regression guards against upstream wording.
   **Bundle with commit 3** if total tests stay <30 LOC (per
   `tasks/lessons.md`).

---

## Batch 11 — `app.py` (large, big theming surface, 5+ commits)

**Expected commit shape**: 5-6 commits.

1. **`feat(batman-cli): port app.py (verbatim with import remaps)`** —
   single 2094-LOC commit. Big diff but reviewable as "did import
   remaps + class rename + `no_splash` deviation apply correctly."
   Changes:
   - All `deepagents_cli.*` imports → `batman_code.*` (~15 top-level +
     1 inline `_version` import at the `/version` handler).
   - `from deepagents_cli.agent import create_cli_agent` →
     `from batman_code.agent import create_batman_agent` (and the
     call site at source line 1943 + the comment at line 1932 updated).
   - `DeepAgentsApp` class name → `BatmanApp` (incl. the
     `run_textual_app` constructor call site).
   - `_COMMAND_URLS` dict targets repointed: `changelog` / `feedback`
     → bat-code repo URLs (`https://github.com/Akhan521/bat-code/...`).
     `/docs` keeps `DOCS_URL` constant. Same correctness-fix-bundled-
     with-port pattern as Batch 9's chat_input history path.
   - **Approved deviation from pure verbatim**: `BatmanApp.__init__`
     accepts `no_splash: bool = False` (kw-only) and stores as
     `self._no_splash`. The pre-existing Phase 1 `main.py` stub already
     calls `BatmanApp(no_splash=args.no_splash)`; without this param,
     runtime breaks. The `on_mount` conditional push of `BatcaveScreen`
     deliberately stays out of commit 1 (deferred to commit 3
     alongside joker modal — both are new on_mount behavior).
     Temporary regression accepted: between commits 1 and 3, launching
     `bat-code` skips splash. CLI isn't end-to-end usable until Phase 9
     anyway.
   - **No theming, no logic changes, no new on_mount behavior beyond
     the `no_splash` storage above.**
2. **`test(batman-cli): cover app.py pure-logic helpers`** —
   ~25-40 tests:
   - `QueuedMessage` dataclass (init, equality, mode field).
   - `TextualTokenTracker` (add accumulates, reset zeroes, hide/show
     don't error without mount).
   - `TextualSessionState` (`reset_thread` produces 8-char hex,
     `auto_approve` flag persistence).
   - `_COMMAND_URLS` dict integrity (keys present, URLs match
     bat-code repo).
   - `_build_thread_message` URL fallback (with URL → linked Text,
     without → plain str).
   - `BatmanApp.__init__` smoke: `no_splash` defaults to False, stored
     as `self._no_splash`; explicit value preserved through init.
   - Skip lifecycle hooks, action handlers, modal wiring — those need
     a mounted Textual app and are covered by Phase 10.
3. **`feat(batman-cli): theme app.py + add splash/joker on_mount
   behavior`** — the BIG commit. This is where everything deferred
   from commit 1 lands. Expected to be the largest single commit of
   the batch. Four concern groups:

   **A. New on_mount behavior (NOT in source — bat-code-specific):**
   - **Splash mount**: add `from batman_code.widgets.batcave import
     BatcaveScreen` import. In `on_mount`, conditionally push
     `BatcaveScreen(no_splash=self._no_splash)` early (before agent /
     adapter wiring). **No exit callback** — splash dismisses to
     reveal chat UI, NOT exit the app (different from Phase 1 demo
     stub which exited on dismiss because nothing else was wired).
   - **Joker startup warning modal** (NEW): add `persona: str =
     "batman"` kw-only param to `BatmanApp.__init__` (stored as
     `self._persona`); `on_mount` pushes themed modal when
     `persona == "joker"` (after splash, before chat focus). Both
     conditional pushes are unit-testable seams.

   **B. Theming — narrative strings (chrome → Gotham voice):**
   - App `TITLE` `"Deep Agents"` → **`"bat-code"`** (line 353).
   - Help text command-list intro + footer (lines 1087-1101) — Gotham
     voice; slash names + key-binding mnemonics stay functional.
   - `/version` output: `"deepagents version: ..."` (lines 1112,
     1115) → themed.
   - Status messages: `"Switched to ..."` / `"Resumed thread ..."` /
     `"No active session"` / `"Unknown command:"` / `"Already using
     ..."` / `"Started new thread: ..."` / `"Already on thread: ..."`
     / `"Failed to switch to thread ..."` → themed.
   - Error messages: `"Agent not configured."` (1250) / `"Failed to
     create model: ..."` (1928) / `"Model switch failed: ..."` (1958)
     / `"Could not save model preference."` (1915) / `"Cannot switch
     threads: ..."` (1782, 1788) / `"Missing credentials: ..."`
     (1890) → themed.
   - Auto-approved shell command notice (line 829), model-preference
     restart notice (line 1908), LangSmith tracing hint (line 1062),
     `"Command completed (no output)"` (line 976), `"Press Ctrl+C
     again to quit"` notification (1593) → themed.
   - Resume-thread label `"Resumed thread"` prefix (line 1431) →
     themed.
   - Approval-mode toggle confirmations mirror StatusBar's
     `"DETECTIVE MODE"` / `"DARK KNIGHT MODE"` labels (already
     themed in Phase 5).
   - Class + module + `__init__` docstrings that say "deepagents-cli"
     → "bat-code" (lines 1, 351, 409).

   **C. Path correctness (currently still says `~/.deepagents/`):**
   - 5 occurrences in error messages (lines 1888, 1916, 1977, 2016,
     2037) → `~/.bat-code/`.
   - 3 occurrences in `REMEMBER_PROMPT` (lines ~265, 266, 284):
     `~/.deepagents/agent/AGENTS.md`, `.deepagents/AGENTS.md`,
     `~/.deepagents/agent/skills/` → `~/.bat-code/...`.
   - `REMEMBER_PROMPT` (347-line agent prompt, NOT chrome): verbatim
     + minimal `s/deepagents-cli/bat-code/g` swap. Keep substance
     intact.

   **D. `UserMessage` theming touch in `widgets/messages.py`** (Phase
   5 follow-up bundled here):
   - Border-left + `> ` prefix `#10b981` → `COLORS["gotham_blue"]`
     (`#1a3a5c`).
   - Add `"Gotham Citizen:"` label above content in compose layout
     (closes the CLAUDE.md Phase 1 spec item Phase 5 deferred).

4. **`test(batman-cli): cover app.py theming + new on_mount behavior`**
   — assert themed strings appear + regression guards (`"Deep Agents"
   not in TITLE`, `"deepagents version" not in source` via
   `inspect.getsource` — same pattern as Batch 10's adapter theming
   tests). Test joker warning modal mounts only when `persona ==
   "joker"`. Test splash mount triggers only when `no_splash=False`.
   Test `UserMessage` border color is no longer `#10b981`. **Bundle
   with commit 3** if tests stay <30 LOC.
5. **`docs: mark Phase 8 COMPLETE`** — bump `tasks/todo.md` Phase 8
   section, this `tasks/phase8-plan.md` scope table, `MEMORY.md`
   next-session pointer (which moves on to Phase 9 — `main.py` CLI
   entry).

**Total expected commits across both batches: 8-10**. Roughly Batch 8
(model_selector) shape × 2.

---

## Critical files

### NEW (`batman_code/`)

- `batman_code/textual_adapter.py` — port (895 LOC + theming).
- `batman_code/app.py` — port (2094 LOC + theming).

### NEW tests

- `tests/test_textual_adapter.py` — ~15-30 tests for helpers + theming.
- `tests/test_app.py` — ~25-50 tests for helpers + theming + joker
  modal conditional.

Both live at `tests/` (not `tests/widgets/`) because they test
module-level code, not widget code — mirrors source layout.

### MODIFIED

- `batman_code/widgets/messages.py` — small `UserMessage` styling
  touch (Phase 5 deferred-spec closeout). Only commit alongside
  app.py theming commit.
- `batman_code/widgets/__init__.py` — **likely no changes** (re-exports
  already cover everything needed).

---

## Reuse — already in `batman_code/`

The port should call these directly — no re-implementation:

- `batman_code.agent.create_batman_agent` (Phase 4)
- `batman_code.config.*` — `COLORS`, `DOCS_URL`, `SHELL_TOOL_NAMES`,
  `CharsetMode`, `_detect_charset_mode`, `build_langsmith_thread_url`,
  `create_model`, `detect_provider`, `is_shell_command_allowed`,
  `settings` (Phase 1/2)
- `batman_code.model_config.*` — `ModelConfigError`, `ModelSpec`,
  `clear_default_model`, `get_credential_env_var`,
  `has_provider_credentials`, `save_default_model`, `save_recent_model`
  (Phase 2)
- `batman_code.file_ops.FileOpTracker` (Phase 2)
- `batman_code.image_utils.create_multimodal_content` (Phase 2)
- `batman_code.input.{ImageTracker, parse_file_mentions}` (Phase 4)
- `batman_code.ui.format_tool_message_content` (Phase 4)
- `batman_code.clipboard.copy_selection_to_clipboard` (Phase 2)
- All **14 Phase 5 widgets** — composed/mounted by app, dispatched to
  by adapter
- `batman_code.skills.*` — referenced via `/remember` command in app

---

## Verification recipe

From `libs/batman-cli/`:

```powershell
# 1. Import smoke test (after port commits)
uv run python -c "from batman_code.textual_adapter import TextualUIAdapter, execute_task_textual; print('adapter OK')"
uv run python -c "from batman_code.app import BatmanApp; print('app OK')"

# 2. Zero deepagents_cli references (after every port-related commit)
grep -r "deepagents_cli" libs/batman-cli/   # must be empty

# 3. Unit tests
uv run --group dev pytest tests/test_textual_adapter.py -v
uv run --group dev pytest tests/test_app.py -v

# 4. Full suite (regression guard)
uv run --group dev pytest
```

**End-to-end visual verification deferred to Phase 10** (post-Phase 9
when CLI entry lands and the app can launch via `bat-code`). Phase 8
by itself produces an importable but not-yet-runnable `BatmanApp` class.

---

## Risks & notes

1. **2094-LOC single port commit**: large diff. Mitigation: it's
   verbatim, so reviewer pattern is "scan import-remap diff + spot-
   check class structure." Same shape as Batch 3 messages.py port
   (1258 LOC, also one commit). Confirmed by user during planning.
2. **`REMEMBER_PROMPT` (347 lines)**: verbatim + minimal
   `s/deepagents-cli/bat-code/g`. Don't rewrite — it's an LLM prompt,
   not chrome.
3. **`UserMessage` theming**: touches a Phase 5 file. Justified
   because Phase 5 left it intentionally pristine per memory notes.
   Mention this in the commit message.
4. **Joker warning modal**: NEW addition not in source. Tested via
   pure-logic test for "mount conditional" branch.
5. **Splash mount**: source has no splash logic (BatcaveScreen is
   bat-code-specific). Decision: `BatmanApp.__init__` accepts
   `no_splash: bool = False`; `on_mount` conditionally pushes
   `BatcaveScreen` if not set. The flag flows from Phase 9 `main.py`
   into the constructor.
6. **`/batsignal` slash command**: stays deferred to Phase 7 per
   `tasks/deferred.md`. The if-elif dispatch in app.py is the right
   seam; adding it later is a one-line registration.
7. **Async/Textual integration tests**: possible via `App.run_test()`
   but heavyweight. Per `tasks/lessons.md`, skip Textual layout
   assertions; rely on import smoke + Phase 10. Unit-test pure logic
   only.

---

## Out of scope for Phase 8

- **Phase 9** — `main.py` (CLI entry, argparse, `bat-code` console-
  script). Separate phase, planned after Phase 8.
- **Phase 7** — `/batsignal` widget + dispatch (deferred per
  `tasks/deferred.md`). Lands after Phase 9.
- **Phase 10** — end-to-end verification (post-Phase 9).
- **Themed-language additions beyond what's in the source** — villain-
  of-the-day, Gotham weather, more loading screens, more slash
  commands. All `tasks/deferred.md` items.

---

## Critical file references

| File | Role |
|------|------|
| `libs/batman-cli/batman_code/agent.py` | `create_batman_agent` — called by app's model hot-swap (line 1943 in source) |
| `libs/batman-cli/batman_code/config.py` | App-wide settings, colors, glyphs, model creation, LangSmith helpers |
| `libs/batman-cli/batman_code/model_config.py` | Model spec parsing, credential checks, default persistence |
| `libs/batman-cli/batman_code/widgets/__init__.py` | Existing re-export surface — no Phase 8 change expected |
| `libs/batman-cli/batman_code/widgets/messages.py` | UserMessage touchup target (Phase 5 deferred-spec closeout) |
| `libs/batman-cli/batman_code/widgets/batcave.py` | Splash screen — pushed by app's `on_mount` if `no_splash=False` |
| `tasks/todo.md` | Phase 8 checklist — kept in sync per commit |
| `tasks/phase5-plan.md` | Phase 5 conventions (commit style, test-alongside, theming guidance) — still in force |
| `tasks/deferred.md` | Punted work (`/batsignal`, easter eggs, approval.py Esc gap) |
| `tasks/lessons.md` | Standing rules (always test, small commits) |
| `CLAUDE.md` | Project vision and full Batman color palette + themed-language table |
