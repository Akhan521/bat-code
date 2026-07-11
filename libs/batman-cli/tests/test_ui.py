"""Tests for `batman_code.ui`.

Source-inspection regression guards to ensure every user-facing
argparse flag registered in `main.py` also appears in the
`show_help()` output. Prevents the Phase 10 bug where argparse
knew about `--no-splash` / `-q` / `--no-stream` / `--model-params`
but `show_help()` silently omitted them.
"""

from __future__ import annotations

import inspect

import pytest

from batman_code import ui


@pytest.mark.parametrize(
    "flag",
    [
        "-r, --resume",
        "-p, --persona",
        "-M, --model",
        "--model-params",
        "-m, --message",
        "--auto-approve",
        "--no-splash",
        "--sandbox",
        "--sandbox-id",
        "--sandbox-setup",
        "-n, --non-interactive",
        "-q, --quiet",
        "--no-stream",
        "--shell-allow-list",
        "--default-model",
        "--clear-default-model",
        "-v, --version",
        "-h, --help",
    ],
)
def test_show_help_lists_every_top_level_flag(flag: str) -> None:
    source = inspect.getsource(ui.show_help)
    assert flag in source, f"show_help() is missing {flag!r} in its output"
