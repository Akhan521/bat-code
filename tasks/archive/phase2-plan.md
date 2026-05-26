# Plan: Phase 2 — Model & Session Infrastructure — COMPLETE

> Completed 2026-03-25. All 15 modules ported, imports verified, path remappings confirmed.

## Context

Phase 2 ports the ~15 infrastructure modules from `libs/cli/deepagents_cli/` to `libs/batman-cli/batman_code/`. These modules handle model configuration, sessions, file operations, backends, skills, and sandbox integrations — everything the TUI needs beneath the UI layer.

## Import remapping pattern

All files follow the same rules:
- `deepagents_cli.*` → `batman_code.*` (our code, being ported)
- `deepagents.*` → kept as-is (SDK dependency, not ported)
- `~/.deepagents/` → `~/.bat-code/` (user config dir)
- `.deepagents/` → `.bat-code/` (project-level config dir)

Two exceptions deferred to Phase 4 — see `tasks/deferred-imports.md`.

## Source reference

| Source (`deepagents_cli/`) | Target (`batman_code/`) |
|----------------------------|------------------------|
| `model_config.py` | `model_config.py` |
| `sessions.py` | `sessions.py` |
| `project_utils.py` | `project_utils.py` |
| `tools.py` | `tools.py` |
| `file_ops.py` | `file_ops.py` |
| `image_utils.py` | `image_utils.py` |
| `clipboard.py` | `clipboard.py` |
| `backends.py` | `backends.py` |
| `local_context.py` | `local_context.py` |
| `subagents.py` | `subagents.py` |
| `non_interactive.py` | `non_interactive.py` |
| `skills/__init__.py` | `skills/__init__.py` |
| `skills/load.py` | `skills/load.py` |
| `skills/commands.py` | `skills/commands.py` |
| `integrations/__init__.py` | `integrations/__init__.py` |
| `integrations/sandbox_provider.py` | `integrations/sandbox_provider.py` |
| `integrations/sandbox_factory.py` | `integrations/sandbox_factory.py` |
| `integrations/modal.py` | `integrations/modal.py` |
| `integrations/daytona.py` | `integrations/daytona.py` |
| `integrations/runloop.py` | `integrations/runloop.py` |
| `integrations/langsmith.py` | `integrations/langsmith.py` |

---

## Per-module changes vs. verbatim port

### Commit 1: model_config.py
- Verbatim port — no `deepagents_cli` imports to remap
- Loads TOML config from `~/.bat-code/config.toml`
- Also updated `config.py` to import from `batman_code.model_config` instead of `deepagents_cli.model_config`

### Commit 2: sessions.py
- DB path: `~/.deepagents/sessions.db` → `~/.bat-code/sessions.db`
- All imports: `batman_code.config`

### Commit 3: 5 utility modules
| Module | Key changes |
|--------|-------------|
| `project_utils.py` | `.deepagents/agent.md` → `.bat-code/agent.md` |
| `tools.py` | User-Agent: `BatCode/1.0`, imports from `batman_code.config` |
| `file_ops.py` | `batman_code.config` import, SDK imports kept |
| `image_utils.py` | No deepagents imports at all — direct port |
| `clipboard.py` | `batman_code.config` import |

### Commit 4: backends + local_context + subagents
| Module | Key changes |
|--------|-------------|
| `backends.py` | No `deepagents_cli` imports — only SDK imports |
| `local_context.py` | `.deepagents` → `.bat-code` in file filter, `batman_code.config` import |
| `subagents.py` | `.deepagents/agents/` → `.bat-code/agents/` in docstrings |

### Commit 5: non_interactive.py
- **DEFERRED**: `from deepagents_cli.agent import DEFAULT_AGENT_NAME, create_cli_agent` stays until Phase 4
- All other imports changed to `batman_code.*`
- Sandbox import: `batman_code.integrations.sandbox_factory`

### Commit 6: skills/ and integrations/
| Module | Key changes |
|--------|-------------|
| `skills/__init__.py` | Re-exports from `batman_code.skills.commands` |
| `skills/load.py` | `bat-code-version` metadata key, `~/.bat-code/` paths |
| `skills/commands.py` | **DEFERRED**: `deepagents_cli.ui` import stays; all other imports → `batman_code.*` |
| `integrations/__init__.py` | Package marker |
| `integrations/sandbox_provider.py` | Abstract interface, `batman_code` imports |
| `integrations/sandbox_factory.py` | All `batman_code.integrations.*` imports |
| `integrations/modal.py` | `app_name` default: `bat-code-sandbox` |
| `integrations/daytona.py` | `batman_code.integrations.sandbox_provider` import |
| `integrations/runloop.py` | Same import pattern |
| `integrations/langsmith.py` | `DEFAULT_TEMPLATE_NAME`: `bat-code-cli` |

### Commit 7: Tracking docs
- Updated `tasks/todo.md` — all Phase 2 checkboxes marked complete
- Created `tasks/deferred-imports.md` with Phase 4 checklist
- Updated project memory

---

## Deferred imports (Phase 4 dependency)

Two files retain `deepagents_cli` imports because `batman_code.agent` and `batman_code.ui` don't exist yet:

1. **`non_interactive.py`** — `from deepagents_cli.agent import DEFAULT_AGENT_NAME, create_cli_agent`
   → Phase 4: `from batman_code.agent import DEFAULT_AGENT_NAME, create_batman_agent`

2. **`skills/commands.py`** — `from deepagents_cli.ui import build_help_parent, show_skills_detail, show_skills_list`
   → Phase 4: `from batman_code.ui import build_help_parent, show_skills_detail, show_skills_list`

Full checklist in `tasks/deferred-imports.md`.

---

## Dependency added

- `Pillow>=10.0.0` added to `pyproject.toml` (required by `image_utils.py`)

---

## Verification results (2026-03-25)

### Module imports: 21/21 PASS
All modules import cleanly via `uv run python -c "import batman_code.<module>"`.

### Path remappings: PASS
- `settings.user_deepagents_dir` → `~/.bat-code` (correct)
- `get_db_path()` → `~/.bat-code/sessions.db` (correct)

### Stale reference check: PASS
Grep for `deepagents_cli` across all Phase 2 files found references only in the 2 known deferred-import files. No unexpected remnants.

### Key exports verified
| Module | Export | Status |
|--------|--------|--------|
| `config` | `COLORS, settings, get_glyphs, console` | PASS |
| `tools` | `fetch_url, http_request, web_search` | PASS |
| `local_context` | `LocalContextMiddleware` | PASS |
| `skills.load` | `list_skills` | PASS |
| `sandbox_factory` | `create_sandbox, get_default_working_dir` | PASS |
| `sandbox_provider` | `SandboxProvider` | PASS |

---

## Commit strategy (executed)

7 commits, grouped by dependency and logical scope:
1. `model_config.py` + `config.py` import update
2. `sessions.py`
3. 5 utility modules (tools, file_ops, image_utils, clipboard, project_utils)
4. 3 infrastructure modules (backends, local_context, subagents)
5. `non_interactive.py` (with deferred import)
6. `skills/` (3 files) + `integrations/` (7 files)
7. Tracking docs update
