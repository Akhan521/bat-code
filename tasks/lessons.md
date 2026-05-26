# Lessons Learned — bat-code

Patterns to internalize so user corrections don't repeat.

---

## Testing

### Always write tests alongside new code

**Captured:** 2026-05-25, mid-port of `thread_selector.py`.

**Rule:** Every new feature, ported module, or widget gets unit tests **in the
same workstream** — not deferred, not "later." Tests verify logic and
correctness; without them we're shipping unverified code.

**How to apply:**

- **Verbatim ports** — pin down the ported logic: formatters, label builders,
  navigation math, parsers, state transitions. Skip Textual layout assertions
  (covered indirectly by import smoke test).
- **Theming changes** — assert the themed strings appear in the output of the
  themed function (e.g., `"Case Files" in title`, `"Villain Detected" in
  error_label`).
- **New widgets / features** — TDD or test-alongside; test commit lands in the
  same batch.

**Commit pattern (porting):**
```
feat(batman-cli): port X (verbatim)
test(batman-cli): cover X ported logic
feat(batman-cli): theme X with Gotham labels
test(batman-cli): cover X theming
docs: mark X complete
```
Bundle test commits with the feat commit if small (< ~30 LOC of tests).

**Test infrastructure:** `libs/batman-cli/tests/` with `pytest`. `pytest` lives
in a `[dependency-groups.dev]` group in `pyproject.toml`. Run via:
```powershell
cd libs/batman-cli
uv run --group dev pytest
```

---

## Commits

### Prefer small, digestible commits (from `feedback_commit_style.md`)

Split verbatim ports from theming from docs. One concern per commit. Makes
review and rollback surgical.

---

## Splash / animation lessons (Phase 6)

- Pre-render everything possible at startup; per-frame work should be minimal.
- Row-cache for Rich Text: only rebuild rows with active changes.
- Pre-computed color lerp tables eliminate expensive hex parsing per frame.
- Reuse animation infrastructure: same `_MatCell` system works for glitch-in,
  fadeout, and materialize.
- Dynamic ASCII art builder avoids hardcoded widths — scale to terminal.
- Monologue tone requires iteration — present options with previews, let user
  choose.
- For gradients across fewer rows, narrow the color range so per-step deltas
  stay smooth.
