# bat-code tests

Unit tests for `batman_code` modules. Run from `libs/batman-cli/`:

```powershell
uv sync --group dev
uv run --group dev pytest
```

## Conventions

- Mirror source layout: `tests/widgets/test_<widget>.py` covers
  `batman_code/widgets/<widget>.py`.
- Test the **pure logic**: formatters, label builders, navigation math,
  parsers, state transitions. Skip Textual layout/render — covered indirectly
  by import smoke tests.
- For widgets with theming, add explicit assertions on themed strings
  (e.g., `assert "Case Files" in title`, `assert "Villain Detected" in label`).
- Network / filesystem / SQLite work goes through `monkeypatch` or
  `tmp_path` — never touch real user dirs.
