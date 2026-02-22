# bat-code Implementation Plan

Batman-themed AI coding TUI. Package at `libs/batman-cli/`, CLI command `bat-code`.
Architecture: Custom Textual UI (Option B, stranger-code style) + local editable deepagents SDK.

---

## Phase 0 — Scaffold Package

- [ ] Create `libs/batman-cli/` directory
- [ ] Write `libs/batman-cli/pyproject.toml`
  - Build system: hatchling
  - Package name: `batman-cli`
  - Entry point: `bat-code = "batman_code:cli_main"`
  - Dependencies: mirror `libs/cli/pyproject.toml` (textual, langchain, etc.)
  - `[tool.uv.sources]` deepagents pointing to `../deepagents` editable
  - Optional extras: all model providers (anthropic, openai, etc.)
- [ ] Create `libs/batman-cli/batman_code/` package directory
- [ ] Write `batman_code/__init__.py` — export `__version__`, `cli_main`
- [ ] Write `batman_code/__main__.py` — `python -m batman_code` support
- [ ] Write `batman_code/_version.py` — version `0.1.0`
- [ ] Run `uv sync` in `libs/batman-cli/` to verify scaffold installs cleanly
- [ ] Verify `bat-code --help` runs without error

---

## Phase 1 — Config & Color System

- [ ] Write `batman_code/config.py`
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

- [ ] Write `batman_code/app.tcss`
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

## Phase 2 — Model & Session Infrastructure

> These are near-direct ports from `libs/cli/deepagents_cli/` with Batman naming.
> Read each source file carefully before porting — do not blindly copy.

- [ ] Port `batman_code/model_config.py` from `deepagents_cli/model_config.py`
  - Rename internal references from `deepagents` → `batman_code`
- [ ] Port `batman_code/sessions.py` from `deepagents_cli/sessions.py`
  - Change DB path from `~/.deepagents/sessions.db` → `~/.bat-code/sessions.db`
  - Change table/metadata references to `bat-code`
- [ ] Port `batman_code/project_utils.py` from `deepagents_cli/project_utils.py`
- [ ] Port `batman_code/tools.py` from `deepagents_cli/tools.py`
  - Keep `fetch_url`, `http_request`, `web_search` — no Batman changes needed
- [ ] Port `batman_code/file_ops.py` from `deepagents_cli/file_ops.py`
- [ ] Port `batman_code/image_utils.py` from `deepagents_cli/image_utils.py`
- [ ] Port `batman_code/clipboard.py` from `deepagents_cli/clipboard.py`
- [ ] Port `batman_code/backends.py` from `deepagents_cli/backends.py`
- [ ] Port `batman_code/subagents.py` from `deepagents_cli/subagents.py`
- [ ] Port `batman_code/non_interactive.py` from `deepagents_cli/non_interactive.py`
- [ ] Port `batman_code/local_context.py` from `deepagents_cli/local_context.py`
- [ ] Port `batman_code/skills/` directory from `deepagents_cli/skills/`
- [ ] Port `batman_code/integrations/` directory from `deepagents_cli/integrations/`
  - Update any internal imports to point to `batman_code.*`

---

## Phase 3 — Agent Personas

- [ ] Write `batman_code/prompts/batman.md`
  - Terse, methodical, zero fluff
  - Acts first, explains only when asked
  - Max 2-sentence responses unless detail is explicitly requested
  - Signatures: "Confirmed.", "Handled.", "Don't ask again."
  - Never uses filler words or praise
  - Easter eggs: responds to "why so serious?" with a single period
  - Tool use: silent execution, reports only outcome

- [ ] Write `batman_code/prompts/alfred.md`
  - Refined British butler tone
  - Verbose, always explains what it's doing and why
  - Opens with "If I may, sir..." or "Master [user], if you'll permit me..."
  - Closes responses with gentle commentary on the user's approach
  - Flags potential issues diplomatically: "One might consider..."
  - Easter egg: responds to "where's Bruce?" with "Master Wayne is... indisposed."

- [ ] Write `batman_code/prompts/oracle.md`
  - Pure analytical mode — Barbara Gordon / Oracle persona
  - Data-driven, research-heavy, hacker aesthetic
  - Outputs structured analysis: hypothesis → evidence → conclusion
  - Uses precise technical language, no metaphors
  - Comfortable with parallel sub-agent research tasks
  - Easter egg: responds to "birds of a prey" pun with exactly one eye-roll emoji

- [ ] Write `batman_code/prompts/nightwing.md`
  - Fast, witty, collaborative — Dick Grayson energy
  - More conversational than Batman, uses light humor
  - Acknowledges the user as a partner, not a client
  - Doesn't take itself too seriously but gets the job done
  - Easter eggs: occasional Haley's Circus references, calls user "partner"

- [ ] Write `batman_code/prompts/joker.md`
  - Chaotic, theatrical, darkly funny
  - Roasts bad code with Joker-esque dramatic flair
  - Uses `--auto-approve` behavior (DARK KNIGHT MODE on by default)
  - Comments on code quality unprompted and dramatically
  - "Why so serious? It's just a memory leak."
  - Easter egg: responds to "why so serious?" with an unhinged monologue about semicolons
  - Warning shown at startup when joker persona is selected

- [ ] Write `batman_code/system_prompt.md`
  - Base behavior instructions (port from `deepagents_cli/system_prompt.md`)
  - Replace all deepagents references with Batman context
  - Add dynamic section: persona-specific instructions injected at runtime

---

## Phase 4 — Agent Wiring

- [ ] Write `batman_code/agent.py`
  - Function: `create_batman_agent()` (mirrors `create_cli_agent()`)
  - Accepts `persona: str` param, loads corresponding `prompts/{persona}.md`
  - Merges persona prompt into system_prompt.md at call time
  - Middleware stack: MemoryMiddleware → SkillsMiddleware → LocalContextMiddleware → InterruptOnConfig
  - If persona is `joker`: set `auto_approve=True` automatically + show warning
  - Returns `(agent, composite_backend)` tuple same as deepagents_cli

- [ ] Write `batman_code/ui.py`
  - Port from `deepagents_cli/ui.py`
  - Update `show_help()` with Batman-themed command descriptions
  - Mode names: DETECTIVE MODE, DARK KNIGHT MODE, THE CAVE, BATCOMPUTER

- [ ] Write `batman_code/input.py`
  - Port from `deepagents_cli/input.py`
  - Add `/batsignal` to recognized slash commands
  - Command descriptions use Batman terminology
  - Mode labels: DETECTIVE MODE (manual), DARK KNIGHT MODE (auto-approve)

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

## Phase 6 — Batman Beyond Loading Screen

> Inspired by Batman Beyond cyberpunk aesthetic: neon-lit rainy alley, silhouette walking
> toward viewer, neon signs, wet floor reflection. Replaces the original batcave/bat-swarm concept.

### Color palette (splash-only overrides)
- Background: `#0a0008` (deep purple-black)
- Neon crimson: `#cc0033` / `#ff0044`
- Neon magenta: `#ff2d7a` / `#e0007a`
- Teal accent: `#00aacc`
- Rain: `#2a2a3a` (dim blue-gray)
- Figure: `#111111` (near-black silhouette)
- Bat symbol on chest: `#cc0033`

### ASCII art assets (define as constants at top of file)

**Batman Beyond silhouette** (~12 rows, slim build, pointy ears, red symbol):
```
     /\   /\
    /  \ /  \
   /    V    \
  |   (   )   |
  |    | |    |
   \   |•|   /
    \  | |  /
     \ |_| /
      \|_|/
       | |
      /   \
     /     \
```
(The `•` char on the chest = bat symbol in `#cc0033`)

**Neon sign (left side, vertical)** — box-drawn ASCII, crimson:
```
╔═══╗
║ B ║
║ A ║
║ T ║
╚═══╝
```

**Alley perspective lines** — converge to center vanishing point using `\`, `/`, `|`, `░`, `▒`

**Rain characters**: `│`, `╎`, `'`, `.` — randomly distributed, falling each tick

**Wet floor reflection**: mirror of silhouette below a `─` horizon line, rendered at ~30% brightness

### Animation phases

- [ ] Write `batman_code/widgets/batcave.py`
  - Class: `BatcaveScreen(Screen[None])` — full-screen Textual Screen
  - Tick interval: 0.06s
  - `--no-splash`: call `self.dismiss()` immediately in `on_mount()`
  - `on_key()`: call `self._finish()` to cancel timer and dismiss

  - **Phase `rain` (~18 ticks = 1.1s):**
    - Initialize rain drop list: each drop has `(col, row, char, speed)`
    - Each tick: advance drops downward, wrap at bottom, spawn new drops at top
    - Render as full-screen grid; rain chars in `#2a2a3a`, background `#0a0008`
    - Rain density increases over the phase (more drops spawn per tick)

  - **Phase `alley` (~25 ticks = 1.5s):**
    - Rain continues in background
    - Alley perspective lines fade in from edges toward center vanishing point
    - Left wall: `\` chars descending left-to-right
    - Right wall: `/` chars descending right-to-left
    - Floor: `─` chars converging to center
    - Neon sign on left side flickers in: alternate between full bright (`#ff2d7a`) and dim (`#660022`) every 2–3 ticks to simulate neon flicker
    - Optional: small teal accent neon on right side (`#00aacc`)
    - Colors fade in gradually using linear interpolation on hex components

  - **Phase `reveal` (~16 ticks = 1.0s):**
    - Rain + alley remain
    - Batman Beyond silhouette materializes center screen, top-down (rows appear one by one)
    - Behind figure: radial glow — center columns shift from `#0a0008` → `#660022` → `#cc0033`
    - Bat symbol row (`•`) renders in `#cc0033`, pulses (alternates `#cc0033` ↔ `#ff0044`)
    - Figure rows appear with slight glitch: random chars first, then stabilize

  - **Phase `hold` (~25 ticks = 1.5s):**
    - Full scene: rain animating, neons flickering, static figure
    - Wet floor reflection: render silhouette mirrored below horizon `─` line at 30% brightness
      - Reflection color: multiply each channel by 0.3, add slight blue tint
    - "BATMAN BEYOND" title appears above figure in `#ff2d7a` with neon-glow style (bright center, dim edges)
    - "INITIALIZING..." subtitle fades in below in `#cc0033`
    - After hold ticks complete: call `self._finish()`

  - **Helper: `_render_frame(w, h) -> Text`**
    - Compose full grid each tick: background → alley → rain → figure → reflection → UI text
    - Use Rich `Text` with per-span color styling

  - **Helper: `_lerp_color(c1, c2, t) -> str`**
    - Linear interpolate between two hex colors at t∈[0,1], return hex string

  - **Helper: `_glitch_str(s, intensity) -> str`**
    - Replace random non-space chars with chars from `"▓▒░╬╫╪┼╳※▪◆◇▄▀█"`

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
