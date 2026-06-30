# bat-code Implementation Plan

Batman-themed AI coding TUI. Package at `libs/batman-cli/`, CLI command `bat-code`.
Architecture: Custom Textual UI (Option B, stranger-code style) + local editable deepagents SDK.

---

## Phase 0 — Scaffold Package

- [x] Create `libs/batman-cli/` directory
- [x] Write `libs/batman-cli/pyproject.toml`
  - Build system: hatchling
  - Package name: `batman-cli`
  - Entry point: `bat-code = "batman_code:cli_main"`
  - Dependencies: mirror `libs/cli/pyproject.toml` (textual, langchain, etc.)
  - `[tool.uv.sources]` deepagents pointing to `../deepagents` editable
  - Optional extras: all model providers (anthropic, openai, etc.)
- [x] Create `libs/batman-cli/batman_code/` package directory
- [x] Write `batman_code/__init__.py` — export `__version__`, `cli_main`
- [x] Write `batman_code/__main__.py` — `python -m batman_code` support
- [x] Write `batman_code/_version.py` — version `0.1.0`
- [x] Run `uv sync` in `libs/batman-cli/` to verify scaffold installs cleanly
- [x] Verify `bat-code --help` runs without error

---

## Phase 1 — Config & Color System — COMPLETE

- [x] Write `batman_code/config.py`
  - Batman color palette constants (`COLORS` dict):
    - `background`: `#0a0a0f`
    - `bat_gold`: `#f5c518`
    - `gotham_blue`: `#1a3a5c`
    - `error`: `#8b0000`
    - `success`: `#00ff41`
    - `tool`: `#2d2d4e`
    - `dim`: `#4a4a6a`
    - `user`: `#e8e8e8`
  - `Glyphs` frozen dataclass (same fields as deepagents_cli, bat-themed defaults)
    - `spinner_frames`: bat-wing frames `["(\\  )", "( \\ )", "( / )", "(/  )"]` cycling
    - `bat_symbol`: `">==|==<"` compact bat, and full ASCII bat for overlays
  - `CharsetMode` StrEnum (UNICODE / ASCII / AUTO)
  - `Settings` frozen dataclass with env var loading
  - `get_glyphs()` cached function
  - `get_banner()` — returns Gotham ASCII art banner text
  - `PERSONA_NAMES` list: `["batman", "alfred", "oracle", "nightwing", "joker"]`
  - `DEFAULT_PERSONA = "batman"`

- [x] Write `batman_code/app.tcss`
  - All color variables using Batman palette
  - `Screen` layer definitions (base, autocomplete, batsignal)
  - `#chat`, `#messages`, `#bottom-app-container`, `#input-area` layout
  - `.approval-menu` with bat-gold border
  - Message type styling:
    - User: white text, thin white border
    - Assistant: bat-gold left border
    - Tool: dim violet background
    - Error: dark red border
    - System: gotham blue border
  - Status bar color coding:
    - DETECTIVE MODE: `#1a3a5c` (gotham blue)
    - DARK KNIGHT MODE: `#8b0000` (danger red)
  - Bat-signal overlay layer (`#batsignal-overlay`)

---

## Phase 2 — Model & Session Infrastructure — COMPLETE

> Near-direct ports from `libs/cli/deepagents_cli/` with Batman naming.
> All `deepagents_cli.*` imports remapped to `batman_code.*`.
> SDK imports (`deepagents.*`) kept as-is.
> Two deferred imports remained until Phase 4 — resolved in commit 8842309; the
> tracking doc was removed once closed (see git history / archive).

- [x] Port `batman_code/model_config.py` from `deepagents_cli/model_config.py`
  - Rename internal references from `deepagents` → `batman_code`
- [x] Port `batman_code/sessions.py` from `deepagents_cli/sessions.py`
  - Change DB path from `~/.deepagents/sessions.db` → `~/.bat-code/sessions.db`
  - Change table/metadata references to `bat-code`
- [x] Port `batman_code/project_utils.py` from `deepagents_cli/project_utils.py`
- [x] Port `batman_code/tools.py` from `deepagents_cli/tools.py`
  - User-Agent: `BatCode/1.0`, imports from `batman_code.config`
- [x] Port `batman_code/file_ops.py` from `deepagents_cli/file_ops.py`
- [x] Port `batman_code/image_utils.py` from `deepagents_cli/image_utils.py`
- [x] Port `batman_code/clipboard.py` from `deepagents_cli/clipboard.py`
- [x] Port `batman_code/backends.py` from `deepagents_cli/backends.py`
- [x] Port `batman_code/subagents.py` from `deepagents_cli/subagents.py`
- [x] Port `batman_code/non_interactive.py` from `deepagents_cli/non_interactive.py`
  - DEFERRED: `from deepagents_cli.agent` import stays until Phase 4
- [x] Port `batman_code/local_context.py` from `deepagents_cli/local_context.py`
- [x] Port `batman_code/skills/` directory from `deepagents_cli/skills/`
  - `__init__.py`, `load.py`, `commands.py`
  - DEFERRED: `from deepagents_cli.ui` import in commands.py stays until Phase 4
- [x] Port `batman_code/integrations/` directory from `deepagents_cli/integrations/`
  - `__init__.py`, `sandbox_provider.py`, `sandbox_factory.py`
  - `modal.py`, `daytona.py`, `runloop.py`, `langsmith.py`
  - All internal imports point to `batman_code.*`

---

## Phase 3 — Agent Personas — COMPLETE

- [x] Write `batman_code/system_prompt.md`
  - Ported from `deepagents_cli/system_prompt.md` (240 lines)
  - Branding: "Deep Agents CLI" → "Bat-Code", "Deep Agent" → "Bat-Code agent"
  - Added `{persona_instructions}` placeholder for runtime injection
  - All safety rails (git, security, debugging) kept verbatim
- [x] Write `batman_code/prompts/__init__.py`
  - `load_persona(name)` utility — reads persona `.md` by name
- [x] Write `batman_code/prompts/batman.md`
  - Terse, imperative, Detective Mode debugging, max 2 sentences
  - Easter eggs: "why so serious?" → `.`, "who are you?" → "I'm Batman."
- [x] Write `batman_code/prompts/alfred.md`
  - Refined British butler, verbose, "If I may, sir...", dry wit
  - Easter eggs: "where's Bruce?" → "Master Wayne is... indisposed."
- [x] Write `batman_code/prompts/oracle.md`
  - Analytical hacker, mission briefing format (Situation/Analysis/Recommended action)
  - Easter eggs: "birds of prey" → 🙄, security vuln → "Backdoor detected."
- [x] Write `batman_code/prompts/nightwing.md`
  - Collaborative, witty, pair programming energy, "we" and "let's"
  - Easter eggs: Haley's Circus refs, "Stuck the landing! Perfect 10."
- [x] Write `batman_code/prompts/joker.md`
  - Chaotic, theatrical, DARK KNIGHT MODE (auto-approve)
  - Startup warning text defined, roasts bad code dramatically
  - Easter eggs: "why so serious?" → unhinged semicolons monologue

---

## Phase 4 — Agent Wiring — COMPLETE

> Plan: `tasks/phase4-plan.md`
> 4 commits: config prereq → agent.py → ui.py + input.py → deferred import fixups

- [x] Add `"primary_dev": "#e0a800"` to `COLORS` dict in `config.py`
  - Prerequisite for `ui.py`'s `show_help()` editable-install banner

- [x] Write `batman_code/agent.py` — port from `deepagents_cli/agent.py`
  - `DEFAULT_AGENT_NAME = "agent"` (unchanged)
  - `list_agents()` — `~/.deepagents/` → `~/.bat-code/` in empty-state text
  - `reset_agent()` — no changes (uses `settings.user_deepagents_dir`)
  - `get_system_prompt(assistant_id, sandbox_type, persona="batman")` — adds persona injection via `.replace("{persona_instructions}", load_persona(persona))`
  - Skills path: `~/.deepagents/` → `~/.bat-code/`
  - `create_batman_agent()` — mirrors `create_cli_agent` + `persona` kwarg
    - Joker enforcement: `if persona == "joker": auto_approve = True`
    - Temp dir prefixes: `deepagents_` → `batcode_`
  - All `deepagents_cli.*` imports → `batman_code.*`
  - New import: `from batman_code.prompts import load_persona`
  - All `_format_*_description` and `_add_interrupt_on` helpers ported verbatim

- [x] Write `batman_code/ui.py` — port from `deepagents_cli/ui.py`
  - Verbatim: `build_help_parent`, `_format_timeout`, `truncate_value`, `format_tool_display`, `format_tool_message_content`
  - `show_help()`: `deepagents` → `bat-code`, `-a/--agent` → `-p/--persona`, `--auto-approve` → DARK KNIGHT MODE
  - All `show_*_help()`: `deepagents` → `bat-code`, `~/.deepagents/` → `~/.bat-code/`
  - All `deepagents_cli.*` imports → `batman_code.*`

- [x] Write `batman_code/input.py` — port from `deepagents_cli/input.py`
  - Near-direct port: only import paths change
  - `INPUT_HIGHLIGHT_PATTERN` already matches `/batsignal` generically
  - No `/batsignal` registration needed (deferred to Phase 7/8)

- [x] Resolve deferred import in `batman_code/non_interactive.py`
  - `from deepagents_cli.agent import DEFAULT_AGENT_NAME, create_cli_agent`
    → `from batman_code.agent import DEFAULT_AGENT_NAME, create_batman_agent`
  - Rename `create_cli_agent(...)` calls → `create_batman_agent(...)`

- [x] Resolve deferred import in `batman_code/skills/commands.py`
  - `from deepagents_cli.ui import ...` → `from batman_code.ui import ...`

- [x] Close out deferred-imports tracking — all items resolved (the standalone
  `tasks/deferred-imports.md` was kept while items were open and removed in
  the Phase 5 docs cleanup once fully closed)

---

## Phase 5 — Core Widgets — COMPLETE

- [x] Port `batman_code/widgets/__init__.py` (incremental — re-exports added per-batch)

- [x] Write `batman_code/widgets/loading.py`
  - Port `LoadingWidget` and `Spinner` from `deepagents_cli/widgets/loading.py`
  - Replace spinner frames with bat-wing animation:
    `["(\\  )", "( \\ )", "(  /)", "( / )"]` in bat-gold color
  - Loading messages rotate through Batman references every ~5s:
    - "Analyzing with the Batcomputer..."
    - "Consulting the case files..."
    - "Scanning Gotham..."
    - "Running forensics..."
  - Paused state shows dim bat symbol: `[dim]>==<[/dim]`
  - Elapsed time display kept the same

- [x] Write `batman_code/widgets/welcome.py`
  - Port `WelcomeBanner` from `deepagents_cli/widgets/welcome.py`
  - Batman ASCII art logo rendered in bat-gold using Rich Text
  - Random welcome message chosen from Gotham-themed list:
    - "Gotham needs you."
    - "The night is darkest just before the dawn."
    - "I am vengeance."
    - "The Batcomputer is online."
  - Shows active persona name and thread ID
  - Dims to `#4a4a6a` after initial render (stays visible but not distracting)

- [x] Port `batman_code/widgets/messages.py`
  - Port from `deepagents_cli/widgets/messages.py`
  - Display-name labels (User: Gotham Citizen, Assistant: persona name,
    Tool: Batcomputer Executing, System: Gotham PD Transmission) belong
    to UI surfaces outside this widget (status bar / message metadata)
  - Error label: **"Villain Detected"** (in-widget) — APPLIED
  - Assistant message border: bat-gold (`#f5c518`) — APPLIED
  - Error border: dark red (`$error` Textual var, mapped to `#8b0000`
    in app.tcss) — already wired

- [x] Port `batman_code/widgets/approval.py`
  - Port from `deepagents_cli/widgets/approval.py`
  - Title prefix: "⚠ Gotham Requires Authorization" — APPLIED
    (single: "...: {tool_name}"; multi: "...: {count} Tool Calls")
  - Option labels: "Authorize" / "Deny" / "Auto-Authorize Session" — APPLIED
    (singular and plural forms both themed)
  - Help text: "Esc reject" → "Esc deny" for label consistency
  - Border: bat-gold (`#f5c518`) — already in app.tcss line 62, no change
  - Kept as deep import (not re-exported from `widgets/__init__.py`)
    per source convention

- [x] Port `batman_code/widgets/status.py`
  - Port from `deepagents_cli/widgets/status.py`
  - Mode labels: DETECTIVE MODE / DARK KNIGHT MODE
  - Bash label: THE CAVE
  - Command label: BATCOMPUTER
  - DARK KNIGHT MODE color: `#8b0000` (red danger)
  - DETECTIVE MODE color: `#1a3a5c` (gotham blue)
  - Token counter: bat-gold `#f5c518`

- [x] Port `batman_code/widgets/diff.py`
- [x] Port `batman_code/widgets/tool_widgets.py`
  - Update status messages: "Executing in the Cave..." / "Mission complete." / "Operation failed."
- [x] Port `batman_code/widgets/tool_renderers.py`
- [x] Port `batman_code/widgets/autocomplete.py`
  - Pure verbatim port — content-identical to source (zero `deepagents_cli`
    imports, no Batman theming surface). Pure stdlib + Textual.
  - Provides @ file-mention + / slash-command completion via the
    `CompletionController` protocol. Ships SlashCommandController,
    FuzzyFileController (aliased PathCompletionController), and
    MultiCompletionManager dispatcher.
  - `/batsignal` NOT added to `SLASH_COMMANDS` yet — handler lands in
    Phase 7 alongside the widget.
  - Kept as deep import (not re-exported from `widgets/__init__.py`).
- [x] Port `batman_code/widgets/history.py`
- [x] Port `batman_code/widgets/model_selector.py`
  - Verbatim port (630 LOC, leaf): only the two top-level imports
    remapped — `deepagents_cli.config` → `batman_code.config` and
    `deepagents_cli.model_config` → `batman_code.model_config`. Provides
    `ModelSelectorScreen` (ModalScreen) + `ModelOption` (Static) for the
    `/model` command.
  - Gotham theming APPLIED:
    - Title: "Select Model" → "Batcomputer Models" (with "active: ..."
      variant when a current model is set).
    - Active option marker: "(current)" → "(active)" for wording
      consistency with the title (and with thread_selector).
    - Extracted inline title from `compose()` into `_build_title()`
      helper to mirror thread_selector's testable seam.
  - Functional (NOT themed): credential indicators ("missing credentials"
    / "credentials unknown"), "(default)" suffix, help text key bindings,
    status messages ("Default set to ...", failure messages), provider
    headers — all operational labels, not chrome.
  - Tests: 30 unit tests in `tests/widgets/test_model_selector.py`
    covering `_format_option_label` branch combinations (selected, creds
    yellow / cyan / plain, current → "(active)" suffix, default suffix,
    combined suffixes), `__init__` registry expansion + current-index
    resolution + default-spec wiring (autouse monkeypatch fixture for
    `get_available_models` and `ModelConfig`), `_update_filtered_list`
    (case-insensitive, partial match, selection clamping, restore-on-clear),
    and `_build_title` (no-active / full-active / model-only /
    provider-only branches with regression guards). All 92 pass.
  - Kept as deep import (not re-exported from `widgets/__init__.py`) per
    source convention.
- [x] Port `batman_code/widgets/thread_selector.py`
  - Verbatim port (545 LOC, leaf): only `deepagents_cli.*` imports remapped
    to `batman_code.*`. Provides `ThreadSelectorScreen` (ModalScreen) +
    `ThreadOption` (Static) for the `/threads` command.
  - Gotham theming APPLIED:
    - Title: "Select Thread" → "Case Files" (with "active: ..." variant
      when a current thread is set).
    - Loading state: "Pulling case files from the Batcomputer..."
    - Empty state: "No case files on record"
    - Error state: "Case files unreachable: ..."
    - Active option marker: "(current)" → "(active)" for wording consistency
      with the title.
  - Column headers (Thread / Agent / Msgs / Updated) kept functional —
    they're data labels, not chrome.
  - Tests: 15 unit tests in `tests/widgets/test_thread_selector.py`
    covering `_format_header`, `_format_option_label`, `_build_title`
    (plain / current-only / linked Rich Text). All pass.
  - Kept as deep import (not re-exported from `widgets/__init__.py`) per
    source convention.
- [x] Port `batman_code/widgets/message_store.py` (verbatim — storage layer, no UI surface)
  - Two-line import remap only: `deepagents_cli.widgets.messages` →
    `batman_code.widgets.messages` (lazy imports inside `MessageData.to_widget`
    and `.from_widget`).
  - No Gotham theming (no narrative surface — pure data layer for chat
    virtualization).
  - Tests: 47 unit tests in `tests/widgets/test_message_store.py` covering
    enum values, `MessageData` validation/defaults, `MessageStore`
    append/lookup/update gating, window/prune/hydrate math, scroll-based
    `should_hydrate_above` / `should_prune_below` heuristics, and clear.
    All 62 pass (47 new + 15 thread_selector).
  - Kept as deep import (not re-exported from `widgets/__init__.py`) per
    source convention.
- [x] Port `batman_code/widgets/chat_input.py`
  - Verbatim port (749 LOC) with three surgical changes:
    - Three import remaps (`deepagents_cli.config` / `.widgets.autocomplete`
      / `.widgets.history` → `batman_code.*`).
    - History file default path: `~/.deepagents/history.jsonl` →
      `~/.bat-code/history.jsonl` (correctness fix — keeps chat history
      in bat-code's data dir alongside sessions, doesn't share state
      with deepagents-cli installs).
    - ASCII-fallback border color `"cyan"` → `"yellow"` so the ASCII
      input border matches the Unicode bat-gold one rendered via `$primary`.
  - Re-exported `ChatInput` from `widgets/__init__.py` per source
    convention (ChatTextArea / CompletionOption / CompletionPopup stay
    internal).
  - Functional (NOT themed): prompt glyph `">"` (Gotham Citizen identity
    lives on user messages in messages.py, not the input cursor), mode
    names (normal / bash / command), key bindings, DEFAULT_CSS (already
    inherits $primary / $surface from app.tcss).
  - Tests: 44 unit tests in `tests/widgets/test_chat_input.py` covering
    CompletionOption / CompletionPopup / ChatTextArea / ChatInput message
    payloads, `__init__` wiring (history path + cwd defaults + initial
    state), parametrized mode-detection signal, `_get_cursor_offset`
    row/col → linear math (all clamp paths), `replace_completion_range`
    (slash / file-mention / directory branches + space insertion +
    multi-line cursor placement + bounds clamping), `value` /
    `input_widget` properties. Full suite: **136 passed**.
  - Phase 5 complete — all 14 widgets ported.

---

## Phase 6 — Batcave Splash Screen (Multi-Phase)

### Phase 6a — "BAT CODE" Block-Letter Glitch Animation — COMPLETE

- [x] `batman_code/widgets/batcave.py` — `BatcaveScreen(Screen[None])`
  - Skippable: any keypress skips to settled state; second keypress dismisses
  - `--no-splash` flag dismisses immediately
- [x] 10-row-tall block letters using `█╔═╗║╚╝` box-drawing chars
  - ~99 chars wide, centered horizontally and vertically on screen
  - 10-shade gold gradient (`_FACE_SHADES`), letter gap 2, word gap 5
- [x] Per-cell smooth settling with `_MatCell` dataclass
  - Delay 2-7 ticks, settle 8-16 ticks
  - Character cycling decelerates with progress
  - Color lerps from dark-blue glitch → bat-gold via `progress^1.5`
- [x] Portrait feature explored and descoped — all portrait code, assets, and tools removed
- [x] User testing — glitch animation approved
- [x] Committed, pushed, and merged to main

### Phase 6b — Batcomputer CRT + Typewriter — COMPLETE

- [x] New state machine: `glitch → hold → fadeout → materialize → typewriter → dismiss`
- [x] Shortened hold phase (12 ticks / ~1s)
- [x] Fadeout phase: BAT CODE letters fade gold → glitch blue → black
  - Reverse of glitch-in: chars degrade from original → glitch pool → space
  - Color lerps from gold → glitch → BG
  - Staggered delays (0-4 ticks), settle 6-12 ticks
- [x] Dynamic Batcomputer CRT art builder (`_build_computer_cells`)
  - Full-screen: ~95% terminal width, height fills terminal (no stand)
  - Half-block chars (`▀▄█░`) for beveled CRT frame with depth
  - Dark Knight color theme: gunmetal bezel, charcoal glow, muted gold screen border
  - "BATCOMPUTER" title in 6-row block font (`_CRT_LETTERS`, 98 chars wide)
  - Symmetric centering (monitor width parity matches screen width)
  - No stand — CRT fills the terminal
- [x] Materialize phase: computer art glitch-settles in (reuses `_settle_cells`)
  - Delay 1-5, settle 6-14 ticks
  - Dark Knight glitch palette (`_CRT_GLITCH_COLORS`) — warm darks matching CRT theme
- [x] 10 dramatic/cinematic boot monologues with round-robin cycling
  - All dramatic/cinematic tone — Batman + coding + agents themed
  - Round-robin via `~/.bat-code/state/monologue_idx` (no repeats across launches)
  - Dim sage color (#8a8a6a) for system-log feel
- [x] Multi-line typewriter: types monologue across full screen width, then "Press any key..."
  - Full-width text flow — word-wraps to terminal width (no hard `\n`)
  - 2 chars per tick for snappier typing
  - Monologue lines in dim sage, prompt in brighter gold (#c49e14)
  - Blinking `█` cursor (14-tick cycle, ~0.56s on/off), waits for keypress to dismiss
- [x] Top-lit gold gradient on BATCOMPUTER title (`_CRT_FACE_SHADES`)
  - `█` blocks: 6-shade gradient (#ffe566 → #c5a530) with ** 1.4 perceptual curve
  - Edge chars (`▄▀`): flat bright gold (#f5c518)
  - Narrowed range so per-step deltas match the 10-row BAT CODE gradient smoothness
- [x] Shared `_settle_cells()` method extracted from `_tick_glitch`
- [x] Updated keypress handling for all 5 phases
- [x] `_skip_to_computer()` — instant skip from any phase to settled computer
- [x] User visual testing and approval
- [x] Committed, pushed, and merged to main

---

## Phase 7 — Bat-Signal Widget

- [ ] Write `batman_code/widgets/batsignal.py`
  - Class: `BatSignalOverlay(Widget)` — floated layer, `layer: batsignal` in CSS
  - Renders large ASCII bat-symbol centered in the terminal
  - **Flicker behavior:**
    - Uses `set_interval(random_interval, self._flicker)` with jittered timing (0.3–1.5s)
    - Each tick: randomly choose brightness level from `["dim", "normal", "bright"]`
    - Dim: render bat in `#2d2d2d`, Bright: render in `#f5c518`, Normal: `#b8960c`
    - Occasional full-off frame (blank) then snap back — simulates real spotlight flicker
  - Positioned: centered, pointer-events none (doesn't block chat interaction)
  - CSS: `layer: batsignal; opacity: 0.35;` so chat content shows through
  - Toggled by `/batsignal` command in `input.py`
  - App stores `_batsignal_active: bool` state
  - ASCII bat-symbol constant (large, ~10 rows tall):
    ```
         _  _
       _/ \/ \_
      / /\  /\ \
     / /  \/  \ \
    /_/   /\   \_\
         /  \
        /    \
    ```

---

## Phase 8 — Textual Adapter & Main App — IN PROGRESS (Batch 10 done)

Full plan: see `tasks/phase8-plan.md` (authoritative). This checklist
mirrors that doc's per-commit shape with check-offs added per commit.

### Batch 10 — `textual_adapter.py` (895 LOC) — COMPLETE

- [x] `feat(batman-cli): port textual_adapter.py (verbatim)` (`8a5de62`)
  - 5 import remaps applied: `deepagents_cli.{file_ops, image_utils,
    input, ui, widgets.messages}` → `batman_code.*`
  - Zero behavioral changes; theming deferred to commit 3
- [x] `test(batman-cli): cover textual_adapter.py pure-logic helpers` (`4504f8c`)
  - 25 tests covering `_build_stream_config`, `_is_summarization_chunk`,
    `_build_interrupted_ai_message`, `TextualUIAdapter.__init__` /
    `set_token_tracker`, `_HITL_REQUEST_ADAPTER` smoke check
- [x] `feat(batman-cli): theme textual_adapter.py narrative strings` (`95fda97`,
  theming + 3 regression tests bundled per `lessons.md` <30-LOC rule)
  - `"Thinking"` → **`"Investigating"`** (DETECTIVE MODE voice)
  - `"Interrupted by user"` → **`"Mission aborted."`** (cinematic)
  - `"Command rejected. Tell the agent what you'd like instead."` →
    **`"Order denied. Tell the Dark Knight what to do instead."`**
    (DARK KNIGHT MODE branding, instructive guidance preserved)
  - Regression tests use `inspect.getsource(execute_task_textual)` to
    assert themed strings present + upstream strings gone
- Suite: **164 passed** (3 batch-10 commits + 136 Phase 5).

### Batch 11 — `app.py` (2094 LOC)

- [x] `feat(batman-cli): port app.py (verbatim with import remaps)` —
  **single 2094-LOC commit** (matches Batch 3 messages.py shape)
  - All `deepagents_cli.*` → `batman_code.*` (~15 top-level + 1 inline
    `_version` import statement at the `/version` handler)
  - `from deepagents_cli.agent import create_cli_agent` →
    `from batman_code.agent import create_batman_agent` (incl. line 1943
    call site + the comment at line 1932)
  - `DeepAgentsApp` class name → `BatmanApp` (incl. the
    `run_textual_app` constructor call site)
  - `_COMMAND_URLS` dict: `changelog` / `feedback` →
    `https://github.com/Akhan521/bat-code/...` URLs. `/docs` keeps
    `DOCS_URL` constant (sourced from config). Correctness fix bundled
    with port, same pattern as Batch 9 chat_input history path.
  - **Approved deviation from pure verbatim**: `BatmanApp.__init__`
    accepts `no_splash: bool = False` (kw-only) and stores it as
    `self._no_splash`. Required because the pre-existing Phase 1
    `main.py` stub calls `BatmanApp(no_splash=args.no_splash)`; without
    this param, runtime breaks. The `on_mount` conditional push of
    `BatcaveScreen` deliberately stays out of commit 1 and lands in
    commit 3 alongside the joker modal (both are new on_mount
    behaviors). Temporary regression: splash won't render at runtime
    between commits 1 and 3 — accepted because CLI isn't end-to-end
    usable until Phase 9 anyway.
  - **No theming, no logic changes, no new on_mount behavior beyond
    the `no_splash` storage above.**
- [x] `test(batman-cli): cover app.py pure-logic helpers` (`46fe383`)
  - 40 unit tests in `tests/test_app.py` covering: `QueuedMessage`
    (frozen, fields, equality, all 3 InputMode literal values);
    `TextualTokenTracker` (add accumulates + notifies, overwrites
    previous, reset zeroes, hide is no-op without callback, show
    replays current_context); `TextualSessionState` (defaults, auto_
    approve persistence, reset_thread generates distinct 8-char hex,
    auto_approve survives reset); `_COMMAND_URLS` integrity (three
    keys, bat-code repo URLs with regression guards against rollback,
    /docs delegates to DOCS_URL); `_build_thread_message` async URL
    resolver (Rich Text on success, plain str on None or exception);
    `BatmanApp.__init__` (no_splash defaults False + explicit value
    preserved, all other storage defaults, cwd path handling, tools
    falsy → empty list, MessageStore + deques start empty); module-
    level smoke (REMEMBER_PROMPT size check, InputMode literal values).
  - Suite: **204 passed** (40 new + 28 textual_adapter + 136 Phase 5).
- [ ] `feat(batman-cli): theme app.py + add splash/joker on_mount
  behavior` — this is the BIG commit; nothing in commit 1 covers the
  items below. Expected to be the largest single commit of Batch 11.

  **New on_mount behavior (NOT in source):**
  - **Splash mount**: add `from batman_code.widgets.batcave import
    BatcaveScreen` import. In `on_mount`, conditionally push
    `BatcaveScreen(no_splash=self._no_splash)` early (before agent /
    adapter wiring). **No exit callback** — the splash should dismiss to
    reveal the chat UI, NOT exit the app (different behavior from the
    Phase 1 demo stub which exited on dismiss because there was nothing
    else to show).
  - **Joker startup warning modal** (NEW): add `persona: str = "batman"`
    kw-only param to `BatmanApp.__init__` (stored as `self._persona`);
    `on_mount` pushes themed modal when `persona == "joker"` (after
    splash, before chat focus). Both conditional pushes are
    unit-testable seams.

  **Theming — narrative strings (chrome → Gotham voice):**
  - App `TITLE` class variable `"Deep Agents"` → **`"bat-code"`** (line 353)
  - Help text command-list intro + footer (lines 1087-1101) — Gotham
    voice; slash names + key-binding mnemonics stay functional
  - `/version` output strings (lines 1112, 1115): `"deepagents version:
    {ver}"` and `"deepagents version: unknown"` → themed wording
  - Status messages: `"Switched to ..."` (1972) / `"Resumed thread ..."`
    (via `_build_thread_message`) / `"No active session"` (1048) /
    `"Unknown command:"` (1202) / `"Already using ..."` (1898) /
    `"Started new thread: ..."` (1133) / `"Already on thread: ..."`
    (1794) / `"Failed to switch to thread ..."` (1850) →  themed
  - Error messages: `"Model not configured"` (n/a — that's a phantom;
    the real strings are `"Agent not configured."` 1250, `"Failed to
    create model: ..."` 1928, `"Model switch failed: ..."` 1958,
    `"Could not save model preference."` 1915, `"Could not save default
    model. Check permissions for ~/.deepagents/"` 2016, `"Could not
    clear default model. Check permissions for ~/.deepagents/"` 2037,
    `"Cannot switch threads: no active agent"` 1782, `"Cannot switch
    threads: no active session"` 1788, `"Missing credentials: ..."`
    1890) → themed
  - Auto-approved shell command notice (line 829): `"✓ Auto-approved
    shell command (allow-list): {cmd}"` → themed
  - Model-preference saved-but-restart notice (line 1908): `"Model
    preference set to ... Restart the CLI for the change to take
    effect."` → themed
  - LangSmith tracing hint (line 1062): `"LangSmith tracing is not
    configured. Set LANGSMITH_API_KEY and LANGSMITH_TRACING=true to
    enable."` → themed (instructive parts kept)
  - `_COMMAND_URLS` usage flow note: `Usage: /model --default
    provider:model` (line 1190) — functional, keep verbatim
  - `"Command completed (no output)"` (line 976) → themed
  - Approval-mode toggle confirmations mirror StatusBar's
    `"DETECTIVE MODE"` / `"DARK KNIGHT MODE"` labels (already themed in
    Phase 5)
  - `"Press Ctrl+C again to quit"` notification (line 1593) → themed
  - Resume-thread label: `"Resumed thread"` prefix passed to
    `_build_thread_message` (line 1431) → themed

  **Path correctness (currently still says `~/.deepagents/`):**
  - 5 occurrences in error messages: lines 1888, 1916, 1977, 2016, 2037
    → `~/.bat-code/`
  - 3 occurrences in `REMEMBER_PROMPT` (lines ~265, 266, 284):
    `~/.deepagents/agent/AGENTS.md`, `.deepagents/AGENTS.md`,
    `~/.deepagents/agent/skills/` → `~/.bat-code/...`
  - REMEMBER_PROMPT is an agent prompt, NOT chrome — keep substance
    intact; only swap `deepagents-cli` / `~/.deepagents/` references.

  **Docstring updates (self-identifies file as bat-code, not deepagents):**
  - Line 1 module docstring: `"""Textual UI application for
    deepagents-cli."""` → `"""...for bat-code."""`
  - Line 351 class docstring: `"""Main Textual application for
    deepagents-cli."""` → `"""...for bat-code."""`
  - Line 409 init docstring: `"""Initialize the Deep Agents
    application."""` → themed (e.g. `"""Initialize the bat-code
    application."""`)

  **`UserMessage` theming touch in `widgets/messages.py`** (Phase 5
  follow-up bundled here):
  - Border-left + `> ` prefix `#10b981` → `COLORS["gotham_blue"]`
    (`#1a3a5c`)
  - Add `"Gotham Citizen:"` label above content in compose layout
    (closes CLAUDE.md Phase 1 spec item Phase 5 deferred)

- [ ] `test(batman-cli): cover app.py theming + new on_mount behavior`
  (bundle with previous commit if <30 LOC of tests)
  - Assert themed strings appear + regression guards (`"Deep Agents"
    not in TITLE`, `"deepagents version" not in source` via
    `inspect.getsource` — same pattern as Batch 10's adapter theming
    tests)
  - Test joker warning modal mounts only when `persona == "joker"`
  - Test splash mount triggers only when `no_splash=False`
  - Test `UserMessage` border color is no longer `#10b981`
- [ ] `docs: mark Phase 8 COMPLETE` — bump `tasks/todo.md` Phase 8
  header, `tasks/phase8-plan.md` scope table, `MEMORY.md` next-session
  pointer (moves on to Phase 9 — `main.py` CLI entry)

### Splash mount details (decision locked at planning)

- `BatmanApp.__init__` accepts `no_splash: bool = False`. **Param +
  storage shipped in commit 1.** Conditional `on_mount` push of
  `BatcaveScreen` (the actual rendering behavior) ships in commit 3
  alongside joker modal — both are new on_mount behaviors and bundle
  cleanly together. Phase 1 demo stub used to `self.push_screen(
  BatcaveScreen(...), callback=lambda _: self.exit(0))`; full Phase 8
  drops the exit callback so splash reveals chat instead.
- The `--no-splash` CLI flag flows from Phase 9 `main.py` → constructor

### Re-export note

`textual_adapter.py` and `app.py` aren't widgets — **no**
`widgets/__init__.py` changes expected. Import as
`from batman_code.textual_adapter import ...` and
`from batman_code.app import BatmanApp` (the latter only from Phase 9's
`main.py`).

---

## Phase 9 — CLI Entry Point

- [ ] Write `batman_code/main.py`
  - `cli_main()` function — entry for `bat-code` console script
  - `argparse` with Rich-formatted help (port pattern from `deepagents_cli/main.py`)
  - Arguments:
    - `-p/--persona` choices: `[batman, alfred, oracle, nightwing, joker]`, default: `batman`
    - `-M/--model` for model override
    - `-r/--resume [ID]` for thread resume
    - `-n/--non-interactive MESSAGE` for single-task mode
    - `--auto-approve` flag (forced on for joker persona)
    - `--no-splash` flag to skip batcave animation
    - `--sandbox TYPE` for remote execution
    - Subcommands: `list`, `reset`, `skills`, `threads`
  - Startup flow:
    1. Load `.env`
    2. Parse args
    3. Validate persona, warn if joker
    4. Set up checkpointer (SQLite at `~/.bat-code/`)
    5. Create sandbox if requested
    6. Call `create_batman_agent()`
    7. Launch `BatmanApp`

---

## Phase 10 — Verification

- [ ] Install package: `cd libs/batman-cli && uv sync && uv run bat-code --help`
- [ ] Test each persona loads: `bat-code --persona alfred`, `--persona joker`, etc.
- [ ] Test splash screen plays and is skippable with keypress
- [ ] Test `/batsignal` toggles on and off without breaking chat
- [ ] Test basic agent interaction (send a message, receive streamed response)
- [ ] Test tool approval flow in DETECTIVE MODE
- [ ] Test `--auto-approve` / DARK KNIGHT MODE
- [ ] Test session resume: `bat-code --resume`
- [ ] Test `--no-splash` skips animation
- [ ] Verify `~/.bat-code/sessions.db` is created correctly

---

## Notes

- **Port, don't copy blindly**: Read each source file, understand it, then adapt. Don't carry over bugs or dead code.
- **Persona injection**: System prompt = `system_prompt.md` contents + `\n\n` + `prompts/{persona}.md` contents. Keep them composable.
- **Joker safety**: Always show a warning when joker persona is active. Never silently enable auto-approve.
- **Bat-signal layer**: Must use Textual's `layers` CSS feature. Chat interaction must not be blocked.
- **Splash screen**: Use `Screen` not `Widget` for the splash — it needs to occupy full terminal.
- **Local deepagents**: All imports from deepagents SDK use `from deepagents import ...` — the editable install handles resolution.
- **No modifications to libs/cli or libs/deepagents** unless a specific SDK limitation is hit and documented.
