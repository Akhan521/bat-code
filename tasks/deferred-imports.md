# Deferred Imports — RESOLVED (Phase 4 Complete)

Two files retained temporary `deepagents_cli` imports because the target modules
(`batman_code.agent` and `batman_code.ui`) didn't exist yet. Phase 4 resolved them.

---

## 1. `batman_code/non_interactive.py`

**Current (deferred):**
```python
from deepagents_cli.agent import DEFAULT_AGENT_NAME, create_cli_agent
```

**After Phase 4:**
```python
from batman_code.agent import DEFAULT_AGENT_NAME, create_batman_agent
```

Also rename any `create_cli_agent(...)` calls to `create_batman_agent(...)`.

---

## 2. `batman_code/skills/commands.py`

**Current (deferred):**
```python
from deepagents_cli.ui import build_help_parent, show_skills_detail, show_skills_list
```

**After Phase 4:**
```python
from batman_code.ui import build_help_parent, show_skills_detail, show_skills_list
```

No function renames needed — just the import path change.

---

## Checklist

- [x] Create `batman_code/agent.py` with `create_batman_agent` and `DEFAULT_AGENT_NAME`
- [x] Create `batman_code/ui.py` with `build_help_parent`, `show_skills_detail`, `show_skills_list`
- [x] Update `non_interactive.py` import
- [x] Update `skills/commands.py` import
- [x] Verify both modules import cleanly
