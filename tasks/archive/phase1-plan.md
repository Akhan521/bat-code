# Plan: Phase 1 — Config & Color System — COMPLETE

> Completed 2026-03-24. All items implemented and verified.

## Context
bat-code currently only has a splash screen (Phase 6). To build the actual agentic TUI (Phases 2–9), we need the foundational config and CSS layer first. This phase ports `deepagents_cli/config.py` (1448 lines) and `deepagents_cli/app.tcss` (182 lines) with Batman theming.

## Files to create/modify

| File | Action | Size |
|------|--------|------|
| `libs/batman-cli/batman_code/config.py` | **Create** | ~1400 lines |
| `libs/batman-cli/batman_code/app.tcss` | **Expand** (replace 14-line placeholder) | ~200 lines |

## Source reference
- `libs/cli/deepagents_cli/config.py` — port from this
- `libs/cli/deepagents_cli/app.tcss` — port from this

---

## 1. `config.py` — What changes vs. verbatim port

### Port verbatim (no changes needed)
- `CharsetMode` StrEnum
- `Glyphs` dataclass structure (23 existing fields)
- `UNICODE_GLYPHS` values (all the same unicode chars)
- `_detect_charset_mode()`, `get_glyphs()`, `reset_glyphs_cache()`
- `parse_shell_allow_list()`, `is_shell_command_allowed()`, `contains_dangerous_patterns()`
- `SHELL_TOOL_NAMES`, `DANGEROUS_SHELL_PATTERNS`, `RECOMMENDED_SAFE_SHELL_COMMANDS`
- `detect_provider()`, `create_model()`, `validate_model_capabilities()` and model helpers
- `ModelResult` dataclass
- `SessionState` dataclass
- `MAX_ARG_LENGTH`, `config` RunnableConfig, `console` Console
- `_find_project_root()`, `_find_project_agent_md()`
- LangSmith helpers (`get_langsmith_project_name`, `fetch_langsmith_project_url`, `build_langsmith_thread_url`)
- dotenv loading + LangChain imports

### Change values (same structure, different content)
| Item | Original | Batman |
|------|----------|--------|
| `COLORS` dict | `primary`, `agent`, `thinking`, etc. | `background`, `bat_gold`, `gotham_blue`, `error`, `success`, `tool`, `dim`, `user` |
| `ASCII_GLYPHS.spinner_frames` | `(-), (\), (\|), (/)` | `(\\  ), ( \\ ), ( / ), (/  )` bat-wing |
| `get_banner()` | DEEP AGENTS block art | BAT CODE block art |
| `COMMANDS` dict descriptions | Neutral | Batman-themed ("Wipe the Batcomputer's screen", etc.) |
| `Settings.user_deepagents_dir` | `~/.deepagents/` | `~/.bat-code/` |
| All `.deepagents/` path refs in Settings | `.deepagents` | `.bat-code` |
| Shell allow env var | `DEEPAGENTS_SHELL_ALLOW_LIST` | `BATCODE_SHELL_ALLOW_LIST` |
| `_is_editable_install()` | checks `deepagents-cli` | checks `batman-cli` |
| `__version__` import | `deepagents_cli._version` | `batman_code._version` |
| Error messages | "deepagents" | "bat-code" |
| LangSmith UTM source | `deepagents-cli` | `bat-code` |
| `get_default_coding_instructions()` | `default_agent_prompt.md` | `system_prompt.md` |

### Add new (Batman-specific)
```python
PERSONA_NAMES = ["batman", "alfred", "oracle", "nightwing", "joker"]
DEFAULT_PERSONA = "batman"
PERSONA_DISPLAY_NAMES = {
    "batman": "The Dark Knight",
    "alfred": "Alfred Pennyworth",
    "oracle": "Oracle",
    "nightwing": "Nightwing",
    "joker": "The Joker",
}
```

Add `bat_symbol: str` field to `Glyphs` dataclass (value: `">==|==<"`).

### Import strategy for model_config
Import from `deepagents_cli.model_config` for now (it's an editable dep). Phase 2 will port `model_config.py` into `batman_code` and update the import.

---

## 2. `app.tcss` — Full Batman stylesheet

Replace the 14-line placeholder. Port structure from `deepagents_cli/app.tcss`, hardcode Batman hex colors (no Textual theme vars).

### Key sections
- **Screen**: `background: #0a0a0f; layers: base autocomplete batsignal;`
- **Chat area**: `#chat`, `#messages`, `#welcome-banner` layout rules
- **Input area**: `#bottom-app-container`, `#input-area` with min/max height
- **Approval menu**: `.approval-menu` with `#f5c518` (bat-gold) border
- **Diff styling**: `.diff-removed` (red), `.diff-added` (green) — keep universal colors
- **Status bar**: `#status-bar` + `.detective-mode` (#1a3a5c) + `.dark-knight-mode` (#8b0000)
- **Completion popup**: `#completion-popup` with Gotham colors
- **Message types** (new): `.message-user` (dim border), `.message-assistant` (gold border), `.message-tool` (violet bg), `.message-error` (red border), `.message-system` (blue border)
- **Bat-signal overlay** (new): `#batsignal-overlay` on `layer: batsignal`, `opacity: 0.35`
- **Tool approval**: `.tool-approval-widget` with gold accents

---

## 3. Constraints
- Do NOT refactor `batcave.py` to use `config.COLORS` — separate cleanup task
- Keep same public API surface as `deepagents_cli.config` so later phase ports need minimal import changes
- `config.py` must not import from batman-cli widgets

---

## 4. Verification
1. `uv run python -c "from batman_code.config import COLORS, Glyphs, Settings, get_glyphs, get_banner, PERSONA_NAMES, console, settings, create_model, SessionState"` — all imports work
2. `uv run python -c "from batman_code.config import get_glyphs; g = get_glyphs(); print(g.bat_symbol)"` — prints `>==|==<`
3. `uv run python -c "from batman_code.config import settings; print(settings.user_deepagents_dir)"` — prints `~/.bat-code`
4. `uv run python -c "from batman_code.config import get_banner; print(get_banner())"` — shows Batman banner
5. `uv run bat-code` — splash still works (no config.py dependency)
6. `uv run bat-code --no-splash` — app loads without CSS parse errors

## 5. Commit strategy
Break into 2 digestible commits:
1. `config.py` — config module with Batman palette, glyphs, settings, model infra
2. `app.tcss` — expanded stylesheet with Batman theming
