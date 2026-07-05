# Deferred Work

Anything we intentionally punted while porting earlier phases. Each entry
names the **trigger phase** (when the deferred work should land), the
**touchpoints** (files/symbols to update), and **why** it was deferred so
future-us doesn't re-litigate the decision.

---

## Phase 7 — `/batsignal` core is now PLANNED (see `tasks/phase7-plan.md`)

The three concrete deliverables previously tracked here —
`SLASH_COMMANDS` autocomplete entry, `widgets/batsignal.py` widget,
and the `app.py::_handle_command` dispatch handler — are now covered
by the Phase 7 plan doc. See `tasks/phase7-plan.md` for the full
Batch 13 shape (4 commits: widget → wiring → tests → docs closeout).

Historical note: these items lived here from the start of the port
until Phase 9 closed, since Phase 7 was blocked on Phase 8's layered
chat container and dispatch seam.

## Phase 7 — Easter eggs backlog (unscoped)

Per `CLAUDE.md` Phase 2 spec, still parked pending collaborative
planning once the `/batsignal` core lands:

- Villain-of-the-day easter eggs
- Gotham weather status bar (extra slot in `status.py`)
- Additional custom loading screens beyond `batcave.py`
- Additional custom slash commands beyond `/batsignal`

These are unscoped — to be planned collaboratively when Phase 7 core
closes.

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

## Future Phases (high-level)

- **Phase 7** — bat-signal overlay + easter eggs (see above). Next up.
- **Phase 10** — end-to-end verification, smoke-test against real
  agent, persona switching, splash skip, `/batsignal` toggle.

Implementation order (from `MEMORY.md`):
Phase 0 → 6 → 1 → 2 → 3 → 4 → 5 → 8 → 9 → **7** → 10.
