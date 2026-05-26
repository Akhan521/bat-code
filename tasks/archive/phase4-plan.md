# Phase 4 — Agent Wiring — Implementation Plan

## Context

Phase 4 creates the agent wiring layer that connects the deepagents SDK to Batman-themed configuration. It produces 3 new files (`agent.py`, `ui.py`, `input.py`) and resolves 2 deferred `deepagents_cli` imports that have been blocking since Phase 2 (tracked in `tasks/deferred-imports.md`).

**Why now:** Phases 0–3 are complete. The config layer has `PERSONA_NAMES`, `DEFAULT_PERSONA`, `PERSONA_DISPLAY_NAMES`. The persona loader (`load_persona()`) and system prompt with `{persona_instructions}` placeholder are ready. Phase 4 is the glue that makes these components functional.

**What this unblocks:** Phase 5 (widgets), Phase 8 (app.py), and Phase 9 (main.py) all depend on `create_batman_agent()` and `ui.py` helpers.

---

## Files to Create / Modify

| File | Action | Est. Lines | Source |
|------|--------|-----------|--------|
| `batman_code/config.py` | UPDATE | +1 line | Add `primary_dev` to COLORS |
| `batman_code/agent.py` | NEW | ~310 | `deepagents_cli/agent.py` (~587 lines) |
| `batman_code/ui.py` | NEW | ~300 | `deepagents_cli/ui.py` (~498 lines) |
| `batman_code/input.py` | NEW | ~90 | `deepagents_cli/input.py` (142 lines) |
| `batman_code/non_interactive.py` | UPDATE | 2 lines changed | Resolve deferred import |
| `batman_code/skills/commands.py` | UPDATE | 1 import block changed | Resolve deferred import |

---

## Design Decisions

### 1. Persona injection via `.replace()`, not `.format()`
The source `agent.py` uses `.replace()` for all template variables. We follow the same pattern: `.replace("{persona_instructions}", persona_content)`. This avoids issues with curly braces in markdown content.

**Template chain:**
1. `get_system_prompt()` reads `system_prompt.md`
2. Replaces `{model_identity_section}`, `{working_dir_section}`, `{skills_path}` (same as source)
3. Additionally replaces `{persona_instructions}` with output of `load_persona(persona)`

### 2. `create_batman_agent` adds `persona` parameter
Mirrors `create_cli_agent` signature exactly, plus one new kwarg: `persona: str = "batman"`. This is the only API difference.

### 3. Joker auto-approve enforced in code, not just prompt
When `persona == "joker"`, the function overrides `auto_approve=True` regardless of caller input. Warning display is a caller responsibility (Phase 8/9).

### 4. `primary_dev` color added to COLORS dict (prerequisite)
Source `ui.py` line 244 references `COLORS["primary_dev"]` for editable-install banner styling. Batman's COLORS dict is missing this key. Add `"primary_dev": "#e0a800"`.

### 5. Path branding: `~/.deepagents/` → `~/.bat-code/`
In `agent.py`, skills path changes to `~/.bat-code/{assistant_id}/skills/`. The `Settings` class already handles this (`user_deepagents_dir` at config.py:548 already points to `~/.bat-code/`).

### 6. `/batsignal` is NOT registered in `input.py` — deferred to Phase 7/8
Source `input.py` contains only `ImageTracker` and `parse_file_mentions`. The `INPUT_HIGHLIGHT_PATTERN` regex already matches any `/command` generically, so `/batsignal` highlights automatically. Actual command dispatch is a Phase 8 (Textual app) concern.

### 7. `ui.py` changes are text-only — no structural changes
All functions are display-only. The port changes string literals for Batman branding but not control flow.

---

## Detailed Changes

### 4.0 Prerequisite: `batman_code/config.py` — Add `primary_dev` color

Add one entry to the `COLORS` dict (after `"user": "#ffffff"` at line 57):

```python
"primary_dev": "#e0a800",  # Darker gold for editable/dev installs
```

---

### 4.1 `batman_code/agent.py` (NEW — ~310 lines)

**Port from:** `libs/cli/deepagents_cli/agent.py`

**Import remapping:**

| Source | Batman |
|--------|--------|
| `from deepagents_cli.config import COLORS, config, console, get_default_coding_instructions, get_glyphs, settings` | `from batman_code.config import ...` |
| `from deepagents_cli.backends import CLIShellBackend, patch_filesystem_middleware` | `from batman_code.backends import ...` |
| `from deepagents_cli.integrations.sandbox_factory import get_default_working_dir` | `from batman_code.integrations.sandbox_factory import ...` |
| `from deepagents_cli.local_context import LocalContextMiddleware` | `from batman_code.local_context import ...` |
| `from deepagents_cli.subagents import list_subagents` | `from batman_code.subagents import ...` |
| *(new)* | `from batman_code.prompts import load_persona` |

All SDK imports (`from deepagents import ...`, `from langchain...`, `from langgraph...`) stay unchanged.

**Key function changes:**

`DEFAULT_AGENT_NAME` — Keep as `"agent"`.

`list_agents()` — Change empty-state text: `"~/.deepagents/"` → `"~/.bat-code/"`.

`reset_agent()` — No changes needed (uses `settings.user_deepagents_dir` which already points to `~/.bat-code/`).

`get_system_prompt()` — New signature adds `persona` param:

```python
def get_system_prompt(
    assistant_id: str,
    sandbox_type: str | None = None,
    persona: str = "batman",
) -> str:
```

After the existing 3 `.replace()` calls, add persona injection:

```python
persona_content = load_persona(persona)
return (
    template.replace("{model_identity_section}", model_identity_section)
    .replace("{working_dir_section}", working_dir_section)
    .replace("{skills_path}", skills_path)
    .replace("{persona_instructions}", persona_content)
)
```

Skills path string: `"~/.deepagents/{assistant_id}/skills/"` → `"~/.bat-code/{assistant_id}/skills/"`.

`create_batman_agent()` — New signature:

```python
def create_batman_agent(
    model: str | BaseChatModel,
    assistant_id: str,
    *,
    persona: str = "batman",
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    sandbox: SandboxBackendProtocol | None = None,
    sandbox_type: str | None = None,
    system_prompt: str | None = None,
    auto_approve: bool = False,
    enable_memory: bool = True,
    enable_skills: bool = True,
    enable_shell: bool = True,
    checkpointer: BaseCheckpointSaver | None = None,
) -> tuple[Pregel, CompositeBackend]:
```

Differences from `create_cli_agent`:
1. Joker enforcement at top of body: `if persona == "joker": auto_approve = True`
2. System prompt generation passes persona: `get_system_prompt(assistant_id, sandbox_type, persona=persona)`
3. Temp directory prefixes: `deepagents_large_results_` → `batcode_large_results_`, `deepagents_conversation_history_` → `batcode_conversation_history_`

All internal `_format_*_description` and `_add_interrupt_on` helper functions — port verbatim.

---

### 4.2 `batman_code/ui.py` (NEW — ~300 lines)

**Port from:** `libs/cli/deepagents_cli/ui.py`

**Import remapping:**

| Source | Batman |
|--------|--------|
| `from deepagents_cli._version import __version__` | `from batman_code._version import __version__` |
| `from deepagents_cli.backends import DEFAULT_EXECUTE_TIMEOUT` | `from batman_code.backends import DEFAULT_EXECUTE_TIMEOUT` |
| `from deepagents_cli.config import COLORS, DOCS_URL, MAX_ARG_LENGTH, _is_editable_install, console, get_glyphs` | `from batman_code.config import ...` |

**Functions ported verbatim** (no text changes):
- `build_help_parent()` — pure argparse utility
- `_format_timeout()` — pure formatting
- `truncate_value()` — pure formatting
- `format_tool_display()` — pure formatting (tool names are SDK-level)
- `format_tool_message_content()` — pure formatting

**`show_help()` — Batman branding:**

| Source text | Batman text |
|-------------|-------------|
| `deepagents-cli` | `bat-code` |
| `deepagents [OPTIONS]` | `bat-code [OPTIONS]` |
| `deepagents list` | `bat-code list` |
| `deepagents reset ...` | `bat-code reset ...` |
| `deepagents skills ...` | `bat-code skills ...` |
| `deepagents threads ...` | `bat-code threads ...` |
| `deepagents -n '...'` | `bat-code -n '...'` |
| `-a, --agent NAME` | `-p, --persona NAME       Persona (batman, alfred, oracle, nightwing, joker)` |
| `--auto-approve` description | `"Auto-approve all tool calls — DARK KNIGHT MODE (toggle: Shift+Tab)"` |
| `-v, --version  Show deepagents CLI version` | `-v, --version  Show bat-code version` |

**All other `show_*_help()` functions — same pattern:**
- `deepagents` → `bat-code` in all usage/example lines
- `~/.deepagents/` → `~/.bat-code/` in path references
- `.deepagents/skills/` → `.bat-code/skills/` in skills directory listing

---

### 4.3 `batman_code/input.py` (NEW — ~90 lines)

**Port from:** `libs/cli/deepagents_cli/input.py`

**Near-direct port.** Only import paths change:

| Source | Batman |
|--------|--------|
| `from deepagents_cli.config import console` | `from batman_code.config import console` |
| `from deepagents_cli.image_utils import ImageData` | `from batman_code.image_utils import ImageData` |

Everything else is verbatim: `PATH_CHAR_CLASS`, `FILE_MENTION_PATTERN`, `EMAIL_PREFIX_PATTERN`, `INPUT_HIGHLIGHT_PATTERN`, `ImageTracker` class, `parse_file_mentions()` function.

---

### 4.4 Update `batman_code/non_interactive.py`

**Line ~41** — Change deferred import:
```python
# FROM:
from deepagents_cli.agent import DEFAULT_AGENT_NAME, create_cli_agent
# TO:
from batman_code.agent import DEFAULT_AGENT_NAME, create_batman_agent
```

**Line ~640** — Rename function call:
```python
# FROM:
agent, composite_backend = create_cli_agent(
# TO:
agent, composite_backend = create_batman_agent(
```

Remove any `# DEFERRED` / `# Phase 4` comments on those lines.

---

### 4.5 Update `batman_code/skills/commands.py`

**Lines ~20-29** — Change deferred import block:
```python
# FROM:
from deepagents_cli.ui import (
    build_help_parent,
    show_skills_create_help,
    show_skills_help,
    show_skills_info_help,
    show_skills_list_help,
)
# TO:
from batman_code.ui import (
    build_help_parent,
    show_skills_create_help,
    show_skills_help,
    show_skills_info_help,
    show_skills_list_help,
)
```

Remove any `# DEFERRED` / `# Phase 4` comments.

---

## Commit Strategy (4 commits)

### Commit 1: `feat(batman-cli): add primary_dev color to config COLORS dict`
- **File:** `batman_code/config.py` (+1 line)
- **Why separate:** Prerequisite for ui.py. Tiny, zero risk.

### Commit 2: `feat(batman-cli): port agent.py with persona injection`
- **File:** `batman_code/agent.py`
- **Why separate:** Core of Phase 4. Contains `create_batman_agent`, persona loading, joker auto-approve. Most complex file — benefits from isolated review.

### Commit 3: `feat(batman-cli): port ui.py and input.py with batman branding`
- **Files:** `batman_code/ui.py`, `batman_code/input.py`
- **Why together:** Both are display/utility modules with minimal logic changes.

### Commit 4: `fix(batman-cli): resolve deferred deepagents_cli imports from Phase 2`
- **Files:** `batman_code/non_interactive.py`, `batman_code/skills/commands.py`
- **Why separate:** Import fixups, not new code. Easy to verify.

---

## Verification

After all 4 commits, run from `libs/batman-cli/`:

```bash
# 1. agent.py imports cleanly, persona injection works
uv run python -c "
from batman_code.agent import DEFAULT_AGENT_NAME, create_batman_agent, get_system_prompt
print(f'DEFAULT_AGENT_NAME = {DEFAULT_AGENT_NAME!r}')
sp = get_system_prompt('test-agent', persona='batman')
assert '{persona_instructions}' not in sp, 'Persona placeholder not replaced!'
print(f'System prompt length: {len(sp)} chars — OK')
"

# 2. ui.py exports accessible
uv run python -c "
from batman_code.ui import (
    build_help_parent, truncate_value, format_tool_display,
    format_tool_message_content, show_help, show_skills_help,
    show_skills_list_help, show_skills_create_help, show_skills_info_help,
    show_list_help, show_reset_help, show_threads_help
)
print('ui.py OK')
"

# 3. input.py exports accessible
uv run python -c "
from batman_code.input import ImageTracker, parse_file_mentions, INPUT_HIGHLIGHT_PATTERN
tracker = ImageTracker()
print(f'ImageTracker next_id: {tracker.next_id}')
print('input.py OK')
"

# 4. Deferred imports resolved
uv run python -c "from batman_code.non_interactive import run_non_interactive; print('non_interactive.py OK')"
uv run python -c "from batman_code.skills.commands import setup_skills_parser; print('skills/commands.py OK')"

# 5. Zero remaining deepagents_cli references in batman_code/
grep -r 'deepagents_cli' batman_code/ --include='*.py' | grep -v __pycache__ || echo 'Clean — no deepagents_cli imports remain'

# 6. Lint
uv run ruff check batman_code/agent.py batman_code/ui.py batman_code/input.py
```

---

## Risks & Notes

1. **`primary_dev` missing from COLORS** — Must be added in Commit 1 before ui.py is created. Without it, `show_help()` raises `KeyError` at runtime.

2. **Non-interactive mode doesn't pass persona** — `create_batman_agent` defaults to `"batman"` when called without `persona`. This is correct for Phase 4. Phase 9 will thread `--persona` through.

3. **Joker auto-approve unreachable in non-interactive** — Since non-interactive doesn't pass persona, the joker path is unreachable until Phase 9. Intentional and safe.

4. **`DOCS_URL` still points to deepagents** — `config.py:45` has `DOCS_URL = "https://docs.langchain.com/oss/python/deepagents/cli"`. Not a Phase 4 concern — note for future.

5. **`deferred-imports.md` completion** — After Phase 4, update `tasks/deferred-imports.md` to mark all items checked.

---

## Critical Files Reference

| File | Role |
|------|------|
| `libs/cli/deepagents_cli/agent.py` | Source to port for `agent.py` |
| `libs/cli/deepagents_cli/ui.py` | Source to port for `ui.py` |
| `libs/cli/deepagents_cli/input.py` | Source to port for `input.py` |
| `libs/batman-cli/batman_code/config.py` | `COLORS`, `settings`, `console`, `get_default_coding_instructions()` |
| `libs/batman-cli/batman_code/prompts/__init__.py` | `load_persona()` used by `agent.py` |
| `libs/batman-cli/batman_code/system_prompt.md` | Template with `{persona_instructions}` |
| `libs/batman-cli/batman_code/non_interactive.py` | Deferred import to resolve |
| `libs/batman-cli/batman_code/skills/commands.py` | Deferred import to resolve |
| `tasks/deferred-imports.md` | Checklist to mark complete |
