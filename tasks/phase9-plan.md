# Phase 9 — CLI Entry Point (`main.py`) — IN PROGRESS

**Status**: 5 of 6 planned commits landed and pushed to `origin/main`
(`09b56eb..a40ba9e`). **Suite: 288 passed** (43 new + 245 prior; zero
`deepagents_cli` references anywhere under `libs/batman-cli/`; only
remaining `deepagents.*` refs are SDK imports `from deepagents.backends
import ...` which reference the first-party deepagents package).

Commits landed this batch (Batch 12 so far):

- `09b56eb` `feat(batman-cli): extend run_textual_app with persona +
  no_splash params` — prep work on `app.py`; both params were added to
  `BatmanApp.__init__` in Phase 8 but the wrapper still had the old
  signature, so main.py could not reach them.
- `cf543d7` `feat(batman-cli): port main.py with import remaps +
  persona flag + no_splash` — big 800-LOC verbatim port replacing the
  Phase 0/1 stub. Identity fixes bundled: description, version string,
  `~/.deepagents/` → `~/.bat-code/`, `deepagents` → `bat-code` in
  hint strings, `create_batman_agent` wired with `persona=`,
  `-a/--agent` replaced by `-p/--persona` (choices=PERSONA_NAMES,
  default="batman"), `--no-splash` threaded through
  `run_textual_cli_async` → `run_textual_app` → `BatmanApp`.
- `a1889f7` `test(batman-cli): cover main.py pure-logic helpers` —
  33 unit tests covering `check_cli_dependencies`, `parse_args` shape
  (persona choices, no_splash, dropped -a/--agent, subparser presence,
  version output), `apply_stdin_pipe` (all six branches with an
  `_StdinStub` fixture), `run_textual_cli_async` signature +
  `create_batman_agent` regression + persona/no_splash forwarding, and
  identity regression guards.
- `259bd22` `feat(batman-cli): theme main.py narrative strings with
  Gotham voice` — 10 themed surfaces across `run_textual_cli_async` +
  `cli_main`. Applied Phase 8's locked vocabulary: Cases (thread
  banner + resume errors + LangSmith + resume hints), Batcomputer
  (default-model status strings), Villain detected (application
  error), Left the Batcave (Ctrl+C). Argparse `help=` strings +
  operational failure prefixes kept verbatim.
- `a40ba9e` `test(batman-cli): cover main.py theming regression
  guards` — 10 unit tests using `inspect.getsource(...)` pattern.
  For each themed string: assert Gotham wording present + upstream
  wording gone.

Next (commit 6, next session): **docs closeout** — bump this file's
status banner to COMPLETE with final tally, bump `tasks/todo.md`
Phase 9 header, rewrite `MEMORY.md` (Current Status → Phase 9
COMPLETE, NEXT SESSION pointer → Phase 7 `/batsignal` widget).

---

# Phase 9 — CLI Entry Point — Implementation Plan

Single source of truth for Phase 9 (porting `main.py`). Same shape as
`tasks/phase8-plan.md`. Status here is **authoritative**; matching
one-liners in `tasks/todo.md` Phase 9 section and per-batch memory
notes track the same state from different angles.

---

## Context

Phase 8 closed with `textual_adapter.py` + `app.py` ported (~3,000 LOC)
and full Gotham theming applied to the Textual UI layer. **`BatmanApp`
is importable but not launchable** — the `bat-code` console-script
target still resolved to the Phase 0/1 stub which just called
`BatmanApp(no_splash=args.no_splash).run()` with no argparse, no
sessions, no sandbox, no persona, no LangSmith, no thread resume.

Phase 9 replaces that stub with a full port of `libs/cli/deepagents_cli/
main.py` (~880 LOC). This is the **first commit where `bat-code`
becomes end-to-end runnable** as a proper CLI (subject to Phase 10
verification).

---

## Recommended approach (Batch 12 — 6 commits)

Same shape as Phase 8's Batch 10 (four commits: port → tests → theme →
docs, plus one prep). Bundle test commits with feat when tests are
<30 LOC per `tasks/lessons.md`.

### Commit 1 — `feat: extend run_textual_app with persona + no_splash` ✅

Small `app.py` change: `run_textual_app` gains `persona: str = "batman"`
and `no_splash: bool = False` kwargs, threaded straight into the
`BatmanApp` constructor. Both params were added to `BatmanApp` in
Phase 8 (commit `84098a0`) but the wrapper wasn't updated, so `main.py`
couldn't reach them. Bundled 2 signature/forwarding tests since they're
small.

### Commit 2 — `feat: port main.py verbatim + persona flag + no_splash` ✅

800-LOC replacement of the Phase 0/1 stub. Three categories of change
vs. source (`libs/cli/deepagents_cli/main.py`):

**Mechanical port (identity + imports):**
- All `deepagents_cli.*` imports remapped to `batman_code.*` (10 top-
  level + ~7 inline lazy imports inside `cli_main` and
  `run_textual_cli_async`).
- `from deepagents_cli._version import __version__` →
  `from batman_code._version import __version__`.
- `create_cli_agent(...)` call site → `create_batman_agent(...)` with
  `persona=` kwarg threaded through.
- `run_textual_app(...)` call site → adds `persona=` and `no_splash=`
  kwargs.
- Argparse `description`: `"Deep Agents - AI Coding Assistant"` →
  `"bat-code — Batman-themed AI Coding Assistant"`.
- Version: `f"deepagents-cli {__version__}"` → `f"bat-code {__version__}"`.
- 5 `~/.deepagents/` paths in error messages → `~/.bat-code/`.
- Hint strings: `deepagents -r <id>` / `deepagents threads list` →
  `bat-code -r <id>` / `bat-code threads list`.
- `apply_stdin_pipe` docstring examples: `| deepagents` → `| bat-code`.
- `check_cli_dependencies` messages: "deepagents CLI" → "bat-code",
  install command → `cd libs/batman-cli && uv sync`.
- LANGSMITH_PROJECT comment: `DEEPAGENTS_LANGSMITH_PROJECT` →
  `BATCODE_LANGSMITH_PROJECT`.

**CLI surface change (bat-code semantics):**
- `-a/--agent NAME` (default `"agent"`, unconstrained) **replaced** by
  `-p/--persona NAME` (`choices=PERSONA_NAMES`,
  `default=DEFAULT_PERSONA="batman"`). The persona value feeds both
  `create_batman_agent(persona=...)` (prompt overlay) AND is used as
  `assistant_id` (memory namespace) — one flag drives both.
- `threads list --agent` filter → `threads list --persona` (renamed for
  consistency; internal `list_threads_command(agent_name=...)` param
  stays verbatim since sessions.py stores threads with an "agent"
  column).
- `reset --agent` subcommand flag stays verbatim (it's a subcommand-
  scoped identifier for the target of the reset, not a global concept).
- **New: `--no-splash`** flag added. Threaded through
  `run_textual_cli_async(..., no_splash=args.no_splash)` →
  `run_textual_app(..., no_splash=...)` → `BatmanApp(no_splash=...)`.
- `run_textual_cli_async` gains `persona: str = "batman"` and
  `no_splash: bool = False` kwargs.

**No narrative Gotham theming yet** — chrome strings like `"Resuming
thread: "`, `"No previous thread"`, `"Application error:"`, `"View this
thread in LangSmith"`, `"Interrupted"` stay verbatim. Deferred to commit
4 to keep the port diff scoped to structural + identity fixes.

### Commit 3 — `test: cover main.py pure-logic helpers` ✅

33 unit tests in `tests/test_main.py`:

- `check_cli_dependencies`: all-present passthrough, single-missing
  exit path (asserts "bat-code" wording, guards against upstream
  "deepagents CLI" text), all-missing enumeration.
- `parse_args` argparse surface: defaults (persona=batman, no_splash=
  False, sandbox=none, etc.), `-p` accepts all 5 canonical personas
  and rejects unknown ones, dropped `-a/--agent` flag no longer parses,
  `--no-splash` toggles, `-r` bare vs. `-r <id>`, sandbox choice
  constraint, subcommand presence (help/list/reset/skills/threads),
  `reset --agent` required, `threads list --persona` filter rename +
  `threads ls` alias + `threads delete` positional. Version output
  regression guard: prints "bat-code" not "deepagents-cli".
- `apply_stdin_pipe`: `sys.stdin=None` passthrough, TTY passthrough,
  empty piped passthrough, no-flag branch sets non_interactive_message,
  existing `-n` prepends piped text, existing `-m` prepends piped text,
  docstring examples reference `| bat-code` not `| deepagents`. Uses a
  small `_StdinStub` (StringIO + settable isatty) and patches `os.open`
  to raise so TTY restoration doesn't touch the real terminal.
- `run_textual_cli_async`: signature exposes persona + no_splash with
  correct defaults, calls `create_batman_agent` (regression against
  `create_cli_agent`), forwards persona to BOTH the agent factory and
  `run_textual_app`, forwards no_splash to `run_textual_app`.
- Identity regression guards: main module has no `from deepagents_cli`
  imports, `parse_args` description says "bat-code" not "Deep Agents",
  `cli_main` paths point at `~/.bat-code/` (not `~/.deepagents/`), hint
  strings use `bat-code -r` / `bat-code threads list`.

### Commit 4 — `feat: theme main.py narrative strings` ✅ (`259bd22`)

Gotham voice on user-facing chrome only (mirror the pattern from
Batch 10 / Batch 11):

- `run_textual_cli_async` thread banner: `"Resuming thread: "` /
  `"Starting with thread: "` → case-based Gotham voice (proposed:
  `"Reopening case: "` / `"Opening new case: "`). Confirm wording
  against Phase 8's locked "Cases" vocabulary before applying.
- `cli_main` interrupted branch: `"\n\n[yellow]Interrupted[/yellow]"` →
  proposed `"\n\n[yellow]Left the Batcave.[/yellow]"` (mirrors the
  StatusBar "Ctrl+C to leave the Batcave" hint from Phase 8).
- `cli_main` resume errors: `"No previous thread for '{persona}',
  starting new."` → case vocabulary; `"No previous threads, starting
  new."` → case vocabulary; `"Thread '{X}' not found."` →
  `"Case '{X}' not on file."` proposed.
- `cli_main` similar-thread hint: `"Did you mean?"` → keep or theme;
  `"Use 'bat-code threads list' to see available threads."` →
  case vocabulary; `"Use 'bat-code -r' to resume the most recent
  thread."` → case vocabulary.
- `cli_main` exception handler: `"\nApplication error: "` → proposed
  `"\nVillain detected: "` (mirrors `app.py`'s runtime error prefix
  themed in Phase 8 commit `b307c67`).
- LangSmith teardown hint: `"View this thread in LangSmith: "` →
  case vocabulary (proposed `"View this case in LangSmith: "`).
- Resume hint on exit: `"Resume this thread with:"` → case vocabulary
  (proposed `"Reopen this case with:"`).
- `Default model set to X` / `Default model cleared.` / `No default
  model set.` — these strings appear both in `main.py` (headless) and
  `app.py` (interactive `/model` command). Phase 8 themed the app.py
  copies to "Batcomputer" vocabulary. Decision: **align main.py** to
  the same wording for consistency ("Default Batcomputer set to X",
  etc.). Confirm before applying.
- `check_cli_dependencies` header: `"❌ Missing required CLI
  dependencies!"` — leave functional or theme? Leaning functional (it's
  a startup-time diagnostic, not chrome).

**Not themed** (functional, not chrome):
- Argparse `help=` strings for flags — they're operational descriptions
  users see with `-h`; theming them would obscure the actual behavior.
  Phase 8's `app.py` themed the "Batcomputer Commands" help block
  because that was in-app chrome; argparse's `-h` output is a different
  surface and stays functional.
- Subcommand names (`list` / `reset` / `skills` / `threads`) — CLI
  identifiers.
- Sandbox choices (`none` / `modal` / `daytona` / etc.) — internal.
- Error format prefixes like `[bold red]Error:[/bold red]` — Rich
  markup convention.

### Commit 5 — `test: cover main.py theming` ✅ (`a40ba9e`)

Regression tests using `inspect.getsource(cli_main)` +
`inspect.getsource(run_textual_cli_async)` pattern (same as Batch 10
and Batch 11 theming). For each themed string:
- Assert the new Gotham wording appears in the source.
- Assert the upstream wording is gone.

### Commit 6 — `docs: mark Phase 9 COMPLETE` ⏳

- Bump `tasks/todo.md` Phase 9 section with all 6 commit hashes.
- Update this file's status banner to "COMPLETE" with the final tally.
- Update `MEMORY.md`:
  - Current Status: `[x] Phase 9: CLI Entry Point — COMPLETE`.
  - Session summary block with commit list + vocabulary decisions +
    key learnings.
  - NEXT SESSION pointer rewritten for **Phase 7** (`/batsignal` widget
    — the last widget still deferred).

---

## Verification recipe

From `libs/batman-cli/`:

```powershell
# 1. Import smoke test (after port commit)
uv run python -c "from batman_code.main import cli_main; print('main OK')"

# 2. bat-code CLI smoke tests
uv run bat-code -v            # prints "bat-code 0.1.0"
uv run bat-code --help        # shows -p/--persona with 5 choices
uv run bat-code -p invalid    # argparse rejects

# 3. Zero deepagents_cli references
grep -r "deepagents_cli" libs/batman-cli/   # test file names only

# 4. Unit tests
uv run --group dev pytest tests/test_main.py -v

# 5. Full suite (regression guard)
uv run --group dev pytest
```

**End-to-end interactive verification deferred to Phase 10** (launching
`bat-code` in a real terminal, sending a prompt, exercising each
persona, verifying splash + joker modal + thread resume).

---

## Locked decisions

1. **Persona semantics**: `-p/--persona` value feeds BOTH the prompt
   overlay (`create_batman_agent(persona=...)`) AND `assistant_id`
   (memory namespace). One flag, one mental model. Each persona has its
   own case files.
2. **Persona choices constrained** to the 5 canonicals (batman, alfred,
   oracle, nightwing, joker). Users can still create custom agent
   configs under `~/.bat-code/agents/{name}/` for `list`/`reset`
   subcommands — those are unrelated to `-p`.
3. **`-a/--agent` dropped** at the top level. Renamed to `--persona` in
   `threads list` (filter). Kept verbatim in `reset --agent` (target of
   reset — subcommand-scoped identifier).
4. **`--no-splash` flag added** (not in upstream). Threads through
   `run_textual_cli_async` → `run_textual_app` → `BatmanApp`.

---

## What this plan does NOT cover (out of scope)

- **Phase 7** (`/batsignal` widget + dispatch): deferred per
  `tasks/deferred.md`. The dispatch seam in `app.py` is already
  identified; adding it later is a one-line registration.
- **Phase 10** (end-to-end verification): interactive terminal testing.
