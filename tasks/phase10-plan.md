# Phase 10 — End-to-End Verification

## Status

**Not started.** Kickoff commit (this doc + `todo.md` bump) is the
first commit of Batch 14. Phase 10 is the **final phase** — after
close, the bat-code port is fully shipped.

Prior state: 316 tests passing on `main` (`f5e0196`), all 14 widgets
ported, `bat-code` end-to-end launchable, `/batsignal` shipped in
Batch 13.

## Context

Phase 10 is fundamentally different from Phases 5–9. Those were
mechanical ports with unit tests. **Phase 10 is interactive smoke
in a live terminal** — the only way to catch bugs that unit tests
miss: real Textual rendering, real agent streaming, real SQLite
persistence, real animation timing, real keypress handling.

The prior 316 tests cover pure logic, not runtime integration.
Every port-phase closeout said "end-to-end deferred to Phase 10."
This is where those cheques get cashed.

## Scope

### In scope — verify each of these against a live `bat-code` process

1. **Install works**: `cd libs/batman-cli && uv sync && uv run bat-code --help`
   renders the persona flag with 5 choices.
2. **Each persona loads**: `bat-code --persona {batman, alfred,
   oracle, nightwing, joker}`. Each launches without error and the
   persona voice is visible in the first agent response.
3. **Splash screen** plays through all 5 phases (glitch → hold →
   fadeout → materialize → typewriter) and is keypress-skippable
   at every phase.
4. **Joker warning modal** appears BEFORE splash for `--persona
   joker`; any key dismisses it. Splash then plays as normal.
5. **`--no-splash`** dismisses the animation immediately (or skips it
   entirely) and lands directly in the chat UI.
6. **Basic agent interaction**: send a message, watch a streamed
   response render token-by-token in the assistant message widget.
7. **`/batsignal` toggle**: overlay mounts, flickers (dim / normal /
   bright / off cycle feels like a real spotlight), does NOT block
   chat input or scroll behind it, un-mounts cleanly on second
   toggle. Themed messages: `"Bat-signal engaged."` /
   `"Bat-signal stood down."`.
8. **Tool approval — DETECTIVE MODE**: agent runs a tool that triggers
   HITL approval. Menu shows `"⚠ Gotham Requires Authorization"` +
   Authorize / Deny / Auto-Authorize buttons.
9. **DARK KNIGHT MODE** (`--auto-approve`): tool calls proceed without
   prompting. StatusBar shows the mode label in red.
10. **Case (thread) resume**: run a session, exit, then
    `bat-code -r` reopens the most-recent case. Messages restore.
    Themed wording: `"Reopening case: <hex>"`.
11. **`~/.bat-code/sessions.db`** gets created on first launch; a
    row appears after the first message.
12. **`Ctrl+C`** exits cleanly with `"Left the Batcave."` message.
13. **Splash monologue rotation**: `~/.bat-code/state/monologue_idx`
    increments between launches (round-robin through the 10
    monologues).

### Out of scope

- **Fixing anything unrelated to the checklist** — Phase 10 is
  verification, not a broad cleanup sweep. If a bug is found and
  it's a Phase-10-adjacent regression, fix it as a scoped commit.
  Unrelated tech debt goes to `tasks/deferred.md`.
- **New features**. All Phase 1 spec items shipped in Phases 0–9 +
  Batch 13. Easter eggs (villain-of-the-day, Gotham weather, extra
  loading screens, extra slash commands) stay parked.
- **Provider matrix**: verify against Anthropic (the default). Other
  providers already have unit-test coverage; live agent integration
  against all providers isn't blocking.
- **Sandbox providers** (Modal / Daytona / Runloop / LangSmith
  Studio): unit-tested; live provider integration is out of scope
  for Phase 10.
- **Windows-specific edge cases** past what breaks the checklist.
  If a terminal quirks the animation (e.g., PowerShell rendering
  half-blocks weirdly), file it under `tasks/deferred.md` unless it
  blocks the checklist.

## Batch 14 — commit shape

Phase 10 produces very little code — mostly observations. Realistic
commit range: **2–5**, depending on what verification surfaces.

### Commit 1 — kickoff (this commit)

**`docs: kick off Phase 10 with plan doc + todo checklist`**

- Add `tasks/phase10-plan.md` (this file).
- Bump `tasks/todo.md` Phase 10 header: `NEXT (final phase)` → `IN
  PROGRESS` with plan-doc pointer at `tasks/phase10-plan.md`.

No source or test changes. Establishes the plan-as-contract shape
matching Phase 5/7/8/9 kickoffs.

### Commit 2+ — bug fixes surfaced during smoke (0–3 commits, variable)

Each bug that surfaces gets its own scoped commit:

- **`fix(batman-cli): <one-line summary of what broke>`** — targeted
  fix, with a regression test if the failure surface is
  unit-testable (source inspection, pure-helper, etc.).
- **`test(batman-cli): ...`** — bundled with the fix if <30 LOC per
  `feedback_always_test.md` bundling rule.

If the deferred **`approval.py` Esc binding** gap
(`Binding("escape", "select_reject", ...)`, ~1 line) shows up as
in-the-way during DETECTIVE MODE verification, land it here too.

### Commit N — closeout (final)

**`docs: mark Phase 10 COMPLETE — project shipped`**

- Flip `tasks/todo.md` Phase 10 header IN PROGRESS → COMPLETE with
  every checkbox marked and the runtime-observed behavior recorded
  (one line per item).
- Flip this file's status banner Not started → COMPLETE with the
  commit range + tally.
- `git mv tasks/phase10-plan.md tasks/archive/phase10-plan.md` —
  matches Phase 5/7/8/9 archive pattern.
- Update `tasks/archive/README.md` with the Phase 10 row +
  close-out commit hash.
- Update `libs/batman-cli/README.md` status footer: "Phase 10
  complete — bat-code is fully shipped."
- Refresh memory topic files:
  - `project_status.md`: all phases COMPLETE, no "Next up".
  - `project_deferred_work.md`: remove Phase 10 checklist (it's
    done); leave easter-eggs backlog + approval.py gap (if not
    fixed above).
  - `MEMORY.md` one-liner: "All 10 phases complete. bat-code is
    shipped."

## How to execute (per-checklist procedure)

Run each item in order. For each: **observe**, **note behavior**,
and decide `PASS` / `FAIL (bug filed)` / `PARTIAL (fix next
commit)`. Keep a scratch log in the scratchpad — the final closeout
commit body captures the summary.

```powershell
# 0. Install + smoke
cd libs/batman-cli
uv sync
uv run bat-code --help                # should render -p/--persona with 5 choices

# 1. Each persona
uv run bat-code --persona batman      # observe: greeting terse, no fluff
uv run bat-code --persona alfred      # observe: verbose, "If I may, sir..."
uv run bat-code --persona oracle      # observe: mission-briefing format
uv run bat-code --persona nightwing   # observe: witty, "we"/"let's" collaborative
uv run bat-code --persona joker       # observe: warning modal → splash → chaos

# 2. Splash phases
uv run bat-code --persona batman      # let splash play through all 5 phases
uv run bat-code --persona batman      # try skip at each phase (glitch/hold/fadeout/mat/type)

# 3. --no-splash
uv run bat-code --no-splash           # lands directly in chat

# 4. Basic interaction (requires ANTHROPIC_API_KEY set)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
uv run bat-code                       # send "hello", observe streamed response

# 5. /batsignal
# type: /batsignal   → overlay engages, flicker cycles
# type another message → chat still works, doesn't scroll behind overlay
# type: /batsignal   → overlay stood down cleanly

# 6. HITL approval — DETECTIVE MODE
uv run bat-code                       # DETECTIVE MODE is default
# ask agent to write a file → approval menu shows
# test Authorize / Deny / Auto-Authorize paths

# 7. DARK KNIGHT MODE
uv run bat-code --auto-approve        # tool calls proceed without prompt

# 8. Case resume
uv run bat-code                       # send a message, Ctrl+C
uv run bat-code -r                    # reopens most-recent case

# 9. Data dir
ls ~/.bat-code/                       # sessions.db, config.toml, state/, etc.
```

## Verification recipe (per-fix commit)

If Phase 10 surfaces a fix commit:

```powershell
# 1. Unit tests (regression guard)
cd libs/batman-cli
uv run --group dev pytest -k "<affected area>" -v

# 2. Re-run the failing checklist item in the live terminal
uv run bat-code <flags that reproduced the bug>

# 3. Full suite (no other regressions)
uv run --group dev pytest
```

## Risks & notes

1. **Bugs are expected**. 316 unit tests + zero live runs since the
   port started = the surface area for animation timing, streaming,
   and persistence bugs is real. The `2–5 commits` range assumes at
   least one live-terminal bug surfaces.
2. **Terminal quirks on Windows** — the splash renders half-blocks
   and box-drawing chars. Windows Terminal / PowerShell / Git Bash
   may render differently. If one rendering is broken and another
   is fine, note the environment; don't force-fix if it's a
   terminal limitation.
3. **API-key-dependent items** (6, 7, 8, 10) require
   `ANTHROPIC_API_KEY` set. If unavailable, mark those items as
   `DEFERRED (no key)` and close on the API-independent portion.
4. **`joker` persona auto-approves tools** — verify that agent-side.
   Any tool call should proceed without prompting because
   `create_batman_agent(persona="joker")` forces `auto_approve=True`.
5. **Case resume without prior session** — should print
   `"No prior case for '<persona>'"` cleanly, not crash. If
   `sessions.db` doesn't exist yet, `bat-code -r` should print the
   themed empty-state message and exit gracefully.

## Success criteria

Phase 10 closes when:

- **Every in-scope checklist item is PASS or DEFERRED (no key)**.
- **Any fix commits shipped with a regression test where applicable**.
- **`origin/main` matches the local state** — all Phase 10 commits
  pushed.
- **Docs reflect completion**: `todo.md` Phase 10 = COMPLETE with
  observed behaviors noted; `libs/batman-cli/README.md` status
  footer says shipped; this plan doc is archived; memory topic
  files reflect "all phases complete."

Once success criteria are met, **bat-code is fully shipped**.
