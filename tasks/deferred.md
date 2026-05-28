# Deferred Work

Anything we intentionally punted while porting earlier phases. Each entry
names the **trigger phase** (when the deferred work should land), the
**touchpoints** (files/symbols to update), and **why** it was deferred so
future-us doesn't re-litigate the decision.

---

## Phase 7 — Bat-Signal & Easter Eggs

### 1. `/batsignal` slash command — autocomplete entry

**Where:** `libs/batman-cli/batman_code/widgets/autocomplete.py`,
`SLASH_COMMANDS` constant.

**Current state:** intentionally absent. Source's 12 commands ported
verbatim:
```python
SLASH_COMMANDS = [
    ("/help", ...), ("/changelog", ...), ("/clear", ...),
    ("/docs", ...), ("/feedback", ...), ("/model", ...),
    ("/remember", ...), ("/quit", ...), ("/tokens", ...),
    ("/threads", ...), ("/trace", ...), ("/version", ...),
]
```

**When to add:** Phase 7 — alongside the `widgets/batsignal.py` widget
and the dispatch handler.

**What to add:**
```python
("/batsignal", "Toggle bat-signal overlay"),
```

**Why deferred:** adding the autocomplete entry without the handler/widget
would surface a broken command (user picks `/batsignal`, nothing happens
or it errors). Ship them together.

### 2. `widgets/batsignal.py` widget

**Where:** `libs/batman-cli/batman_code/widgets/batsignal.py` (NEW).

**Spec (from `CLAUDE.md` Phase 1):** flickering ASCII bat-symbol overlay
rendered as a background layer behind the chat. Flickers at irregular
intervals simulating a real spotlight. Pulses between dim and bright
gold.

**Dependencies:** none (pure Textual widget). Can be built once
`app.py` has a layered chat container (Phase 8).

### 3. `/batsignal` dispatch handler

**Where:** wherever slash-command dispatch lives (likely `app.py` or a
new `batman_code/commands.py` module — TBD in Phase 8/9).

**What it does:** toggles the BatSignalOverlay widget's visibility.

### 4. Other Phase 7 nice-to-haves (per `CLAUDE.md` Phase 2 spec)

- Villain-of-the-day easter eggs
- Gotham weather status bar (extra slot in `status.py`)
- Additional custom loading screens beyond `batcave.py`
- Additional custom slash commands beyond `/batsignal`

These are unscoped — to be planned collaboratively when Phase 7 starts.

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

- **Phase 8** — `textual_adapter.py` (streaming → UI bridge) + `app.py`
  (BatmanApp shell, layered containers, mode toggling). All widgets get
  wired together here.
- **Phase 9** — `main.py` CLI entry, `--persona` flag, `--no-splash`,
  argparse, `bat-code` console-scripts entry point.
- **Phase 7** — bat-signal overlay + easter eggs (see above).
- **Phase 10** — end-to-end verification, smoke-test against real
  agent, persona switching, splash skip, `/batsignal` toggle.

Implementation order (from `MEMORY.md`):
Phase 0 → 6 → 1 → 2 → 3 → 4 → **5** → 8 → 9 → 7 → 10.
