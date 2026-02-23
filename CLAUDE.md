## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update 'tasks/lessons.md' with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests -> then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management
1. **Plan First**: Write plan to 'tasks/todo.md' with checkable items
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review to 'tasks/todo.md'
6. **Capture Lessons**: Update 'tasks/lessons.md' after corrections

## Core Principles
- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

## Project: bat-code — Batman-Themed AI Coding TUI

### Vision
A Batman-themed AI coding assistant TUI built as a standalone package (`libs/batman-cli/`) inside this deepagents monorepo fork. Inspired by [stranger-code](https://github.com/vtrivedy/stranger-code/tree/main), which wraps deepagents with Stranger Things theming. bat-code does the same with a Gotham/Batman aesthetic — but with full ownership of the UI layer and access to the local deepagents SDK for deeper customization when needed.

CLI command: `bat-code`
Package location: `libs/batman-cli/`
Package name: `batman-cli`
Python package: `batman_code/`

### Architecture
- **Option B (stranger-code style)**: Custom Textual app + widgets, reusing deepagents SDK (`libs/deepagents/`) via local editable install. The original `libs/cli/` is never touched.
- **Local editable dependency**: `deepagents = { path = "../deepagents", editable = true }` — allows modifying the SDK if needed (advantage over stranger-code which pins PyPI).
- **No fork of libs/cli**: All Batman UI code lives exclusively in `libs/batman-cli/batman_code/`.

### Features (Phase 1)

#### 1. Batcave Loading Screen (`widgets/batcave.py`)
Batman ASCII portrait materializes from full-screen glitch noise. Skippable with `--no-splash` or any keypress.

**Color palette (splash only):**
- Background: `#050008` (deep purple-black)
- Glitch colors: crimson/red spectrum (`#ff0000`, `#cc0000`, `#8b0000`, etc.) with rare white flash
- Final portrait: character-density shading — deep crimson (`#3d0000`) for sparse chars → vivid red (`#ff1400`) for dense chars

**Unified grid materialization — every cell on screen is alive:**
- On mount, a `_MatCell` is created for **every screen position** (not just art cells)
- Art cells settle toward their final character and crimson color
- Non-art cells settle toward `(" ", background)` — they fade to blank
- The entire screen starts as a wall of glitching characters; the Batman portrait **reveals in-place** as non-art cells fade out and art cells lock in
- No random scatter overlay — all noise is persistent per-cell state, eliminating flicker

**Per-cell smooth settling:**
- Each cell tracks `progress` (0→1) over its lifetime (`_GLITCH_MIN` to `_GLITCH_MAX` ticks)
- Character cycling decelerates: every tick at 0–30% → every 5 ticks at 80–95% → frozen at 95%+
- Probability of showing final char increases with progress (blended, not binary)
- Color lerps smoothly from glitch crimson → final color using `progress^1.5` (shift weighted toward end)

**Phases:**
- **Chaos intro** (`_CHAOS_TICKS`): Brief pure full-screen noise before any cells start settling
- **Materialization**: Art cells settle into portrait while non-art cells fade to black. Unified, smooth, no competing visual layers
- **Hold** (`_HOLD_TICKS`): Final portrait displayed for ~2s, then auto-dismiss

#### 2. Five Agent Personas (`prompts/`)
Selected at launch with `--persona <name>`. Each is a `.md` prompt file defining communication style, signature phrases, and easter eggs:
- **batman.md** — Terse, methodical, zero fluff. Acts first, explains only when asked.
- **alfred.md** — Verbose, refined butler. Explains everything, "If I may suggest, sir..."
- **oracle.md** — Pure analysis mode. Data-driven, research-heavy, hacker aesthetic.
- **nightwing.md** — Fast, witty, collaborative. More conversational than Batman.
- **joker.md** — Chaotic, theatrical. Roasts bad code, auto-approves everything (use with caution).

#### 3. Bat-Signal Toggle (`/batsignal`, `widgets/batsignal.py`)
A `/batsignal` slash command toggles a flickering ASCII bat-symbol overlay rendered as a background layer behind the chat. Flickers at irregular intervals simulating a real spotlight. Pulses between dim and bright gold.

#### 4. Batman Color Palette (`app.tcss`)
- Background: `#0a0a0f` (near-black Gotham night)
- Primary accent: `#f5c518` (Bat-gold)
- Secondary: `#1a3a5c` (Gotham blue-grey)
- Error: `#8b0000` (dark red)
- Success: `#00ff41` (terminal green)
- Tool calls: `#2d2d4e` (dim violet)

#### 5. Themed Language Throughout
- User messages label: **"Gotham Citizen"**
- AI messages label: persona name (e.g., "The Dark Knight", "Alfred Pennyworth")
- Errors: **"Villain Detected"** / **"The Rogues Gallery"**
- Manual approval mode: **"DETECTIVE MODE"**
- Auto-approve mode: **"DARK KNIGHT MODE"** (dangerous)
- Bash passthrough: **"THE CAVE"**
- Slash commands: **"BATCOMPUTER"**

### Features (Phase 2 — Future)
- Additional custom loading screens (beyond batcave)
- Additional custom commands beyond `/batsignal`
- Villain-of-the-day easter eggs
- Gotham weather status bar
- To be planned collaboratively

### Key Files Reference
```
libs/batman-cli/
├── pyproject.toml                  # entry: bat-code = "batman_code:cli_main"
├── batman_code/
│   ├── __init__.py
│   ├── __main__.py
│   ├── _version.py
│   ├── main.py                     # CLI entry, argparse, --persona flag
│   ├── agent.py                    # wraps create_deep_agent + middleware
│   ├── app.py                      # BatmanApp(App[int])
│   ├── app.tcss                    # Batman color palette
│   ├── config.py                   # COLORS, Glyphs, Settings
│   ├── system_prompt.md            # Base agent behavior
│   ├── textual_adapter.py          # Streaming → UI bridge
│   ├── ui.py                       # UI helpers
│   ├── sessions.py                 # Thread persistence
│   ├── tools.py                    # fetch_url, http_request, web_search
│   ├── input.py                    # Command parsing, slash commands
│   ├── file_ops.py
│   ├── image_utils.py
│   ├── clipboard.py
│   ├── project_utils.py
│   ├── local_context.py
│   ├── model_config.py
│   ├── non_interactive.py
│   ├── backends.py
│   ├── subagents.py
│   ├── widgets/
│   │   ├── batcave.py              # Splash screen animation (Act 1+2)
│   │   ├── batsignal.py            # /batsignal overlay widget
│   │   ├── loading.py              # Bat-themed spinner
│   │   ├── welcome.py              # Gotham welcome banner
│   │   ├── messages.py             # Themed message widgets
│   │   ├── chat_input.py
│   │   ├── approval.py
│   │   ├── status.py               # DETECTIVE MODE / DARK KNIGHT MODE
│   │   ├── diff.py
│   │   ├── history.py
│   │   ├── tool_widgets.py
│   │   ├── tool_renderers.py
│   │   ├── autocomplete.py
│   │   ├── model_selector.py
│   │   └── thread_selector.py
│   ├── prompts/
│   │   ├── batman.md
│   │   ├── alfred.md
│   │   ├── oracle.md
│   │   ├── nightwing.md
│   │   └── joker.md
│   ├── skills/
│   │   ├── commands.py
│   │   └── load.py
│   └── integrations/
│       ├── sandbox_factory.py
│       ├── modal.py
│       ├── daytona.py
│       └── runloop.py
```

### Implementation Order
See `tasks/todo.md` for the full phased checklist.
