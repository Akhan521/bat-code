# bat-code

Batman-themed AI coding assistant TUI. Custom Textual UI on top of the
[deepagents](../deepagents/) SDK.

```
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
    ██████╗  █████╗ ████████╗    ██████╗ ██████╗ ██████╗ ███████╗
    ██╔══██╗██╔══██╗╚══██╔══╝   ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██████╔╝███████║   ██║      ██║     ██║   ██║██║  ██║█████╗
    ██╔══██╗██╔══██║   ██║      ██║     ██║   ██║██║  ██║██╔══╝
    ██████╔╝██║  ██║   ██║      ╚██████╗╚██████╔╝██████╔╝███████╗
    ╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
```

## Install

From the monorepo root:

```powershell
cd libs/batman-cli
uv sync
```

Uses local editable installs of `deepagents` and `deepagents-cli`. No PyPI
publish — this is the fork.

## Quickstart

Set an API key (Anthropic, OpenAI, Google, or any LangChain-compatible
provider), then launch:

```powershell
export ANTHROPIC_API_KEY="sk-ant-..."
uv run bat-code
```

The Batcave splash animates in, then hands off to the chat UI. Any
keypress skips the animation.

## Personas

Selected at launch with `-p/--persona <name>`. Each is a Markdown
prompt overlay that reshapes the agent's voice. Persona also namespaces
memory — every persona has its own case files.

| Persona | Voice | Signature |
|---------|-------|-----------|
| `batman` (default) | Terse, imperative, zero fluff. Acts first, explains only when asked. | *"Handled."* / *"The mission continues."* |
| `alfred` | Refined British butler. Verbose, courteous, dry wit. Explains everything. | *"If I may suggest, sir..."* |
| `oracle` | Pure analysis mode. Data-driven, mission-briefing format. Hacker aesthetic. | *"Situation. Analysis. Recommended action."* |
| `nightwing` | Fast, witty, collaborative. Pair-programming energy. | *"Let's stick the landing."* |
| `joker` | Chaotic, theatrical, roasts bad code. **Auto-approves everything.** Use with care. | *"Why so serious?"* |

Constrained to these 5 canonicals. Custom agent configs at
`~/.bat-code/agents/{name}/` are available for `list` / `reset`
subcommands but aren't reachable via `-p`.

## Usage

```
bat-code [OPTIONS]

Options:
  -p, --persona {batman,alfred,oracle,nightwing,joker}
                          Persona to adopt (default: batman)
  -M, --model MODEL       Model override (e.g. claude-sonnet-4-5-20250929)
  -m, --message TEXT      Initial prompt to auto-submit on start
  -r, --resume [ID]       Resume a case; -r for most recent, -r <ID> for
                          a specific one
  -n, --non-interactive TEXT
                          Run a single task and exit
  --auto-approve          DARK KNIGHT MODE — approve every tool call
                          without prompting (dangerous)
  --no-splash             Skip the Batcave loading animation
  --sandbox {none,modal,daytona,runloop,langsmith}
                          Remote sandbox for code execution
  --sandbox-id ID         Reuse an existing sandbox
  --sandbox-setup PATH    Setup script for the sandbox
  --shell-allow-list LIST Comma-separated shell commands to auto-approve
  --model-params JSON     Extra kwargs for the model as JSON
  --default-model [MODEL] Set / show the default model
  --clear-default-model   Clear the saved default model
  -q, --quiet             Clean output for piping (requires -n or stdin)
  --no-stream             Buffer full response before writing to stdout
  -v, --version           Show bat-code version
```

### Subcommands

- `bat-code list` — list available agent configs
- `bat-code reset --agent NAME` — reset an agent's prompt
- `bat-code skills <list|create|info>` — manage agent skills
- `bat-code threads <list|delete>` — manage case files (threads)

## Features

**Batcave splash** — Multi-phase intro that glitches "BAT CODE" into
place, fades to a Batcomputer CRT, then types a cinematic boot
monologue. Skippable via any keypress or `--no-splash`.

**DETECTIVE MODE** (manual approval) vs **DARK KNIGHT MODE**
(auto-approve). Toggle with `Shift+Tab` mid-session. Joker persona
forces DARK KNIGHT MODE on startup with an explicit warning modal.

**THE CAVE** (bash passthrough) vs **BATCOMPUTER** (slash-command mode)
— toggle input mode from the chat prompt.

**Case files** — Conversation threads persist to SQLite. Resume the
most recent case with `bat-code -r`, or list them with
`bat-code threads list --persona alfred`. Cases are namespaced per
persona.

**LangSmith tracing** — Set `LANGSMITH_API_KEY` and
`LANGSMITH_TRACING=true` to trace agent runs. The teardown banner
prints a `View this case in LangSmith:` link.

**Remote sandboxes** — Point `--sandbox` at Modal, Daytona, Runloop,
or LangSmith Studio for isolated code execution.

**Slash commands** (typed at the chat prompt):
`/help`, `/clear`, `/model`, `/threads`, `/remember`, `/tokens`,
`/trace`, `/version`, `/docs`, `/changelog`, `/feedback`, `/quit`,
`/batsignal` (toggles a flickering ASCII bat-symbol overlay).

## Data directory

Everything bat-code writes lives at `~/.bat-code/`:

```
~/.bat-code/
├── sessions.db          # SQLite case-file persistence
├── config.toml          # default-model preferences
├── history.jsonl        # chat input history
├── state/               # splash monologue rotation, etc.
└── agents/{name}/       # custom persona/agent configs
```

## Palette

Batman color palette (defined in `batman_code/config.py`):

- Background: `#0a0a0f` (Gotham night)
- Bat-gold: `#f5c518` (primary accent)
- Gotham blue: `#1a3a5c` (secondary)
- Dark red: `#8b0000` (errors, DARK KNIGHT MODE)
- Terminal green: `#00ff41` (success)
- Dim violet: `#2d2d4e` (tool calls)

## Development

Run the test suite (316 tests, ~3s):

```powershell
uv run --group dev pytest
```

Test conventions live in [`tests/README.md`](tests/README.md).
Verify no upstream `deepagents_cli` refs slipped in:

```powershell
grep -r "deepagents_cli" libs/batman-cli/
```

Should match only test regression-guard function names, not any source
imports.

## Project docs

- [`CLAUDE.md`](../../CLAUDE.md) — full project vision, Phase 1 feature
  spec, personas + palette details
- [`tasks/todo.md`](../../tasks/todo.md) — master phased checklist
- [`tasks/deferred.md`](../../tasks/deferred.md) — punted work
  (easter-eggs backlog, Phase 10 verification checklist)
- [`tasks/archive/`](../../tasks/archive/) — historical phase plans

## Status

Phases 0–9 complete. **Phase 10** (end-to-end verification) is the
final phase — interactive smoke of each persona, splash, `/batsignal`
toggle, tool approval, and case resume in a live terminal.
