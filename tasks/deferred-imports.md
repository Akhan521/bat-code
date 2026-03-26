# Deferred Imports — Fix in Phase 4

Two files retain temporary `deepagents_cli` imports because the target modules
(`batman_code.agent` and `batman_code.ui`) don't exist yet. Phase 4 creates them.

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

- [ ] Create `batman_code/agent.py` with `create_batman_agent` and `DEFAULT_AGENT_NAME`
- [ ] Create `batman_code/ui.py` with `build_help_parent`, `show_skills_detail`, `show_skills_list`
- [ ] Update `non_interactive.py` import
- [ ] Update `skills/commands.py` import
- [ ] Verify both modules import cleanly
