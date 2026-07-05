# Phase 7 — Bat-Signal Overlay (`/batsignal`) — Implementation Plan

## Status

**Not started.** All prerequisites are in place — this plan is the
kickoff. Locked at planning: `tasks/deferred.md` is the historical
source of truth for what got deferred and why; this doc is the
authoritative Phase 7 plan going forward.

## Context

Phase 9 closed with `bat-code` end-to-end launchable (`09b56eb..
65e68fd`). All 14 widgets are ported, the Textual UI + main app are
themed, and the CLI entry point is wired. **Phase 7 is the last piece
of Phase 1 spec** — the `/batsignal` bat-symbol overlay + slash
command. After Phase 7 lands, only Phase 10 (end-to-end interactive
verification) remains.

Phase 7 was deferred until after Phases 8 + 9 because the dispatch
seam (`app.py::_handle_command`) and the layered chat container
didn't exist yet. Both landed in Phase 8. This work now unblocks.

## Prerequisites — all met

- ✅ **CSS layer**: `Screen { layers: base autocomplete batsignal; }`
  and `#batsignal-overlay { layer: batsignal; ... opacity: 0.35; }`
  are already in `app.tcss` (lines 7 and 234-242). Phase 5 shipped
  them ahead of Phase 7.
- ✅ **Dispatch seam**: `app.py::_handle_command` is a clean
  if-elif chain at line 1148+ (Phase 8 exploration confirmed this
  is the one-line registration point).
- ✅ **Autocomplete registration point**: `SLASH_COMMANDS` list in
  `widgets/autocomplete.py` at line 95 has 12 commands. Adding
  `/batsignal` is a single-line append.
- ✅ **Color palette**: `#f5c518` (bat-gold), `#b8960c` (mid), and
  `#2d2d2d` (dim) are already in the palette.
- ✅ **App lifecycle**: `on_mount` composes the initial widgets;
  slash-command dispatch runs in async context; `mount`/`remove`
  patterns exist elsewhere (e.g., approval menu).

## Scope

**In scope for Phase 7:**

1. `BatSignalOverlay(Widget)` widget in `batman_code/widgets/
   batsignal.py`
2. `/batsignal` entry in `SLASH_COMMANDS` (autocomplete.py)
3. `/batsignal` dispatch handler in `app.py::_handle_command`
4. `_batsignal_active: bool` state on `BatmanApp` + mount/unmount
   helpers
5. Unit tests covering the widget + the dispatch wiring

**Out of scope (parked for future planning):**

- Phase 7 easter eggs (villain-of-the-day, Gotham weather status
  slot, additional loading screens, additional slash commands). These
  stay in `tasks/deferred.md` under an "Easter eggs backlog" heading —
  to be planned collaboratively when the core `/batsignal` lands.
- Any refactor to `_handle_command`. The if-elif chain stays as-is
  per Phase 8's exploration finding — Phase 7 adds one elif branch,
  full stop.

## Spec

Per CLAUDE.md § Phase 1 Bat-Signal Toggle:

> A `/batsignal` slash command toggles a flickering ASCII bat-symbol
> overlay rendered as a background layer behind the chat. Flickers at
> irregular intervals simulating a real spotlight. Pulses between dim
> and bright gold.

**ASCII art (from CLAUDE.md):**

```
     _  _
   _/ \/ \_
  / /\  /\ \
 / /  \/  \ \
/_/   /\   \_\
     /  \
    /    \
```

**Behavior:**

- Toggled by `/batsignal` — first invocation mounts, second unmounts.
- Renders centered on screen, in the `batsignal` CSS layer (behind
  chat).
- Flicker mechanic:
  - `set_interval(random_interval, self._flicker)` with jittered
    timing in `[0.3, 1.5]` seconds
  - Each tick picks brightness at random from `["dim", "normal",
    "bright"]`
  - Occasional full-off frame (blank) then snap back — simulates
    real spotlight flicker
- Colors (all in the bat-gold family so it reads as a spotlight):
  - `dim`: `#2d2d2d`
  - `normal`: `#b8960c`
  - `bright`: `#f5c518`
- Overlay stays fully non-interactive (opacity 0.35 already in CSS;
  pointer-events don't block chat interaction since it's on a lower
  layer).

## Recommended approach — Batch 13, 4 commits

Mirrors the pattern from Phase 5 leaf-widget batches (single widget
+ wiring + tests + docs).

### Commit 1 — `feat: add BatSignalOverlay widget`

Ship the widget in isolation. No wiring to app.py or autocomplete.py
yet — just a standalone importable class.

- Create `batman_code/widgets/batsignal.py`:
  - `BAT_SYMBOL_ASCII` constant — the multi-line string from CLAUDE.md
  - `_FLICKER_COLORS = {"dim": "#2d2d2d", "normal": "#b8960c", "bright": "#f5c518"}`
  - `_FLICKER_STATES = ("dim", "normal", "bright", "off")` — includes
    an "off" state for the occasional blank frame
  - `_FLICKER_INTERVAL_RANGE = (0.3, 1.5)` — seconds
  - `class BatSignalOverlay(Widget)`:
    - `DEFAULT_CSS` — inherits from `#batsignal-overlay` in
      app.tcss, so minimal here (maybe just `layer: batsignal;` for
      when instantiated without id)
    - `_pick_next_state()` — pure function, returns a state key from
      the weighted pool ("off" is rare, others equal-weight)
    - `_next_interval()` — pure function, returns random float in
      the interval range
    - `render()` — returns a `Text` of the ASCII art in the current
      state's color, or empty string if state == "off"
    - `on_mount()` — sets up the `set_interval` loop
    - Public attribute `state: str` — starts at `"normal"` on mount
- **No re-export** from `widgets/__init__.py` — kept as deep import
  per source convention (matches approval.py, autocomplete.py,
  thread_selector.py).
- **Bundled tests** if under 30 LOC (per `tasks/lessons.md`):
  - `_pick_next_state()` returns a valid state
  - `_next_interval()` stays within `[0.3, 1.5]`
  - `render()` uses the right color for each state + returns empty
    for "off"
  - `BAT_SYMBOL_ASCII` is the exact 7-line string from the spec

### Commit 2 — `feat: wire /batsignal command dispatch + autocomplete`

Register the command + hook it up. This is the "make it toggle" commit.

- `widgets/autocomplete.py::SLASH_COMMANDS` — append
  `("/batsignal", "Toggle bat-signal overlay")` at the end
  (keeps the 12 existing entries intact + adds the 13th).
- `app.py`:
  - Import `BatSignalOverlay` from `batman_code.widgets.batsignal`.
  - Add `self._batsignal_overlay: BatSignalOverlay | None = None` in
    `__init__`.
  - Add elif branch to `_handle_command`:
    ```python
    elif cmd == "/batsignal":
        await self._toggle_batsignal(command)
    ```
  - Implement `_toggle_batsignal(command: str)` helper:
    - Mount `UserMessage(command)` first (matches sibling handlers'
      pattern).
    - If `self._batsignal_overlay is None`: create overlay, mount to
      Screen, store reference, mount an `AppMessage` confirming
      "Bat-signal engaged. Gotham has your back." (or similar
      themed line — confirm wording during code review).
    - Else: remove overlay via `.remove()`, clear reference, mount
      `AppMessage` "Bat-signal stood down." (themed).
- **Deliberate: no batsignal-active flag** on `BatmanApp` — the
  overlay reference itself is the state (None = off, else = on).
  Simpler than tracking a bool + a widget.

### Commit 3 — `test: cover /batsignal wiring + autocomplete registration`

Regression tests for the dispatch + registration seam. Follows
Batch 10/11 `inspect.getsource(...)` pattern for slash-command
handlers.

- `tests/widgets/test_autocomplete.py` (**NEW file** — none exists
  yet since autocomplete.py was deep-import verbatim in Phase 5):
  - `/batsignal` is in `SLASH_COMMANDS` with the exact description
  - `SLASH_COMMANDS` length is 13 (regression against accidental
    entry removal)
- `tests/test_app.py` (extend existing file):
  - `inspect.getsource(BatmanApp._handle_command)` contains
    `"/batsignal"` and the `_toggle_batsignal` call
  - `inspect.getsource(BatmanApp._toggle_batsignal)` contains the
    themed messages (regression guards for wording)
  - `BatmanApp.__init__` initializes `_batsignal_overlay` to None
    (signature check via source inspection — matches the pattern for
    other kw-only param defaults in test_app.py)

### Commit 4 — `docs: mark Phase 7 COMPLETE`

Docs-only closeout, matches Phase 9's commit-6 pattern.

- Bump `tasks/todo.md` Phase 7 section:
  - Header → COMPLETE
  - Check off all 4 commits with their hashes
- Bump this file's status banner to COMPLETE with the final commit
  range and total tally.
- Update `MEMORY.md`:
  - Current Status in `project_status.md`: Phase 7 → COMPLETE
  - Update `project_deferred_work.md`: `/batsignal` core moves out
    of "deferred" — leave only the easter-eggs backlog + Phase 10
    verification
  - Update `project_key_files.md`: add `widgets/batsignal.py` entry
  - Update MEMORY.md index if any of the topic-file one-liners need
    refreshing (Phase 7 → Phase 10 as the "NEXT" pointer)
- Move `tasks/phase7-plan.md` → `tasks/archive/phase7-plan.md`
  (matches Phase 5/8/9 archive pattern). Bump
  `tasks/archive/README.md` with the Phase 7 row.

## Verification recipe

From `libs/batman-cli/`:

```powershell
# 1. Import smoke test (after commit 1)
uv run python -c "from batman_code.widgets.batsignal import BatSignalOverlay; print('OK')"

# 2. Command surface (after commit 2)
uv run bat-code --help    # help text unchanged (batsignal is in-app, not CLI)

# 3. Zero deepagents_cli references (any commit that touches source)
grep -r "deepagents_cli" libs/batman-cli/    # test names only

# 4. Unit tests (after each test commit)
uv run --group dev pytest tests/widgets/test_autocomplete.py -v
uv run --group dev pytest tests/test_app.py -k "batsignal" -v

# 5. Full suite (regression guard on every commit)
uv run --group dev pytest
```

**Interactive verification** (deferred to Phase 10):
- Launch `bat-code`, type `/batsignal`, watch the overlay flicker in
- Type `/batsignal` again, watch it disappear
- Verify chat interaction still works with overlay active (typing,
  scrolling, sending messages)
- Verify keyboard input isn't captured by the overlay
- Confirm the flicker feels like a real spotlight (not too regular,
  not too chaotic)

## Locked decisions

1. **Overlay lifecycle**: Mount on first `/batsignal`, remove on
   second. No pooled instance kept alive. Simpler + matches the
   toggle semantics.
2. **State representation**: `self._batsignal_overlay: Widget | None`
   on `BatmanApp` — no separate bool. Reference itself is the state.
3. **No re-export**: `BatSignalOverlay` stays deep-import per source
   convention (matches other Phase 5 deep-import widgets).
4. **Autocomplete entry description**: `"Toggle bat-signal overlay"`
   (matches the terse style of existing SLASH_COMMANDS entries).
5. **Confirm messages themed**: mount confirmation uses Gotham voice
   (e.g. "Bat-signal engaged."); dismiss confirmation likewise
   ("Bat-signal stood down."). Exact wording confirmed during
   commit 2 review — mirror Phase 8's chrome-vs-content distinction.

## Risks & notes

1. **Flicker overhead**: `set_interval` with 0.3s minimum means up to
   ~3 renders/sec. Should be trivial for Textual, but worth watching
   during interactive verification (Phase 10). If it stutters, widen
   the interval range.
2. **Textual `Widget.render()` return type**: needs to be
   `RenderableType`. Use `rich.text.Text` for colored ASCII art.
3. **Mount/remove race**: `_toggle_batsignal` should await
   `.remove()` before nulling the reference, so a rapid double-toggle
   doesn't leak an overlay.
4. **CSS layer already declared** — do NOT edit `app.tcss` unless
   the interactive verification shows a rendering issue. If the
   overlay renders incorrectly, first check the widget's DEFAULT_CSS
   before touching the app-level stylesheet.

## What this plan does NOT cover

- **Phase 7 easter eggs** (villain-of-the-day, Gotham weather,
  more loading screens, more slash commands). These stay unscoped
  in `tasks/deferred.md` under "Easter eggs backlog" — to be planned
  collaboratively after `/batsignal` core lands.
- **Phase 10** (end-to-end interactive verification) — separate
  phase, planned after Phase 7 closes.
