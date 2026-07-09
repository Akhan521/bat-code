# Deferred Work

Anything we intentionally punted while porting earlier phases. Each entry
names the **trigger phase** (when the deferred work should land), the
**touchpoints** (files/symbols to update), and **why** it was deferred so
future-us doesn't re-litigate the decision.

---

## Phase 7 — `/batsignal` core has SHIPPED

Closed in Batch 13 (`e7bf09e..613d24b`, 4 commits, 28 new tests).
See `tasks/archive/phase7-plan.md` for the historical plan and
`project_gotham_vocabulary.md` for the locked wording (`"Bat-signal
engaged."` / `"Bat-signal stood down."`).

## Phase 10 — End-to-end verification (NEXT, final phase)

Interactive terminal smoke of the assembled app. Nothing else blocks
this — full checklist:

- Install: `cd libs/batman-cli && uv sync && uv run bat-code --help`
- Each persona loads: `bat-code --persona {batman,alfred,oracle,
  nightwing,joker}`
- Splash screen plays and is keypress-skippable
- Joker warning modal appears for `--persona joker`
- Basic agent interaction (send a message, receive a streamed
  response) works
- Tool approval flow in DETECTIVE MODE
- `--auto-approve` / DARK KNIGHT MODE bypasses prompts
- Case resume: `bat-code -r` reopens most-recent case
- `--no-splash` skips animation
- `/batsignal` toggles overlay on/off without breaking chat; flicker
  feels like a real spotlight
- `~/.bat-code/sessions.db` gets created correctly

## Easter eggs backlog (unscoped)

Per `CLAUDE.md` Phase 2 spec — parked pending collaborative planning
when there's appetite:

- Villain-of-the-day easter eggs
- Gotham weather status bar (extra slot in `status.py`)
- Additional custom loading screens beyond `batcave.py`
- Additional custom slash commands beyond `/batsignal`

---

## Inherited from source — small loose threads

### approval.py: help text mentions `Esc` but no binding exists

**Where:** `libs/batman-cli/batman_code/widgets/approval.py`,
`compose()` help-text line and `BINDINGS` ClassVar.

**Current state:** help text says `"Esc deny"` but `BINDINGS` doesn't
include an `escape` binding. Inherited verbatim from source — **not a
bug we introduced**.

**Possible fix:** add `Binding("escape", "select_reject", "Deny",
show=False)` to `BINDINGS` so `Esc` actually denies. ~1 line.

**When:** opportunistic cleanup, or whenever HITL behavior is being
revisited. Not blocking anything.

---

## Implementation order (from `MEMORY.md`)

Phase 0 → 6 → 1 → 2 → 3 → 4 → 5 → 8 → 9 → 7 → **10**.
