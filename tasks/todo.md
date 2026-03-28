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
> Two deferred imports remain until Phase 4 — see `tasks/deferred-imports.md`.

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

- [x] Update `tasks/deferred-imports.md` — mark all items checked

---

## Phase 5 — Core Widgets

- [ ] Port `batman_code/widgets/__init__.py`

- [ ] Write `batman_code/widgets/loading.py`
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

- [ ] Write `batman_code/widgets/welcome.py`
  - Port `WelcomeBanner` from `deepagents_cli/widgets/welcome.py`
  - Batman ASCII art logo rendered in bat-gold using Rich Text
  - Random welcome message chosen from Gotham-themed list:
    - "Gotham needs you."
    - "The night is darkest just before the dawn."
    - "I am vengeance."
    - "The Batcomputer is online."
  - Shows active persona name and thread ID
  - Dims to `#4a4a6a` after initial render (stays visible but not distracting)

- [ ] Port `batman_code/widgets/messages.py`
  - Port from `deepagents_cli/widgets/messages.py`
  - Update display names:
    - User: **"Gotham Citizen"**
    - Assistant: persona-specific (e.g., **"The Dark Knight"**, **"Alfred Pennyworth"**)
    - Tool call: **"Batcomputer Executing"**
    - Error: **"Villain Detected"**
    - System: **"Gotham PD Transmission"**
  - Assistant message border: bat-gold (`#f5c518`)
  - Error border: dark red (`#8b0000`)

- [ ] Port `batman_code/widgets/approval.py`
  - Port from `deepagents_cli/widgets/approval.py`
  - Title prefix: "⚠ Gotham Requires Authorization"
  - Option labels: "Authorize" / "Deny" / "Auto-Authorize Session"
  - Border: bat-gold

- [ ] Port `batman_code/widgets/status.py`
  - Port from `deepagents_cli/widgets/status.py`
  - Mode labels: DETECTIVE MODE / DARK KNIGHT MODE
  - Bash label: THE CAVE
  - Command label: BATCOMPUTER
  - DARK KNIGHT MODE color: `#8b0000` (red danger)
  - DETECTIVE MODE color: `#1a3a5c` (gotham blue)
  - Token counter: bat-gold `#f5c518`

- [ ] Port `batman_code/widgets/diff.py`
- [ ] Port `batman_code/widgets/tool_widgets.py`
  - Update status messages: "Executing in the Cave..." / "Mission complete." / "Operation failed."
- [ ] Port `batman_code/widgets/tool_renderers.py`
- [ ] Port `batman_code/widgets/autocomplete.py`
- [ ] Port `batman_code/widgets/history.py`
- [ ] Port `batman_code/widgets/model_selector.py`
- [ ] Port `batman_code/widgets/thread_selector.py`
- [ ] Port `batman_code/widgets/message_store.py`
- [ ] Port `batman_code/widgets/chat_input.py`

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

## Phase 8 — Textual Adapter & Main App

- [ ] Port `batman_code/textual_adapter.py` from `deepagents_cli/textual_adapter.py`
  - Update all `deepagents_cli.*` imports to `batman_code.*`
  - Update message class references to Batman widget names

- [ ] Write `batman_code/app.py` — `BatmanApp(App[int])`
  - `CSS_PATH = "app.tcss"`
  - `BINDINGS`: same as deepagents_cli plus `/batsignal` binding
  - `compose()`: WelcomeBanner → VerticalScroll(messages) → ChatInput → StatusBar
  - On mount: show `BatcaveScreen` unless `--no-splash`
  - `/batsignal` command handler: mount/unmount `BatSignalOverlay`
  - Joker persona: show warning modal at startup ("Enabling DARK KNIGHT MODE. Chaos incoming.")
  - All themed string constants use config.py values

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
