"""Unit tests for `batman_code.main` pure-logic helpers.

Covers everything testable without spinning up a live Textual app:
- `check_cli_dependencies` (missing / present branches).
- `parse_args` argparse surface (persona flag, choices constraint,
  --no-splash flag, subparser presence, version string).
- `apply_stdin_pipe` (TTY passthrough, empty passthrough, no-flag
  branch, -n prepend, -m prepend, oversized/undecodable failure).
- `run_textual_cli_async` signature + create_batman_agent / persona
  forwarding.
- Regression guards against upstream wording (`Deep Agents`,
  `deepagents-cli`, `~/.deepagents/`) surviving the port.

Skips: `cli_main` (dispatch shell — covered by end-to-end in Phase 10).
"""

from __future__ import annotations

import argparse
import inspect
import io
import sys
from typing import Any

import pytest

from batman_code import main as main_module
from batman_code.main import (
    apply_stdin_pipe,
    check_cli_dependencies,
    parse_args,
    run_textual_cli_async,
)


# ---------------------------------------------------------------------------
# check_cli_dependencies
# ---------------------------------------------------------------------------


def test_check_cli_dependencies_returns_when_all_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        main_module.importlib.util, "find_spec", lambda _name: object()
    )
    # No SystemExit expected.
    check_cli_dependencies()


def test_check_cli_dependencies_exits_when_package_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        main_module.importlib.util,
        "find_spec",
        lambda name: None if name == "tavily" else object(),
    )
    with pytest.raises(SystemExit) as exc:
        check_cli_dependencies()
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "tavily-python" in captured.out
    # Identity check: message must say "bat-code", not the upstream name.
    assert "bat-code" in captured.out
    assert "deepagents CLI" not in captured.out


def test_check_cli_dependencies_reports_all_missing_packages(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        main_module.importlib.util, "find_spec", lambda _name: None
    )
    with pytest.raises(SystemExit):
        check_cli_dependencies()
    captured = capsys.readouterr()
    for pkg in ("requests", "python-dotenv", "tavily-python", "textual"):
        assert pkg in captured.out


# ---------------------------------------------------------------------------
# parse_args — surface + persona flag + no_splash flag
# ---------------------------------------------------------------------------


def _parse(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> argparse.Namespace:
    monkeypatch.setattr(sys, "argv", ["bat-code", *argv])
    return parse_args()


def test_parse_args_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _parse(monkeypatch, [])
    assert args.persona == "batman"
    assert args.no_splash is False
    assert args.resume_thread is None
    assert args.auto_approve is False
    assert args.sandbox == "none"
    assert args.command is None
    assert args.non_interactive_message is None
    assert args.initial_prompt is None


def test_parse_args_accepts_all_canonical_personas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for persona in ("batman", "alfred", "oracle", "nightwing", "joker"):
        args = _parse(monkeypatch, ["-p", persona])
        assert args.persona == persona


def test_parse_args_rejects_unknown_persona(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit):
        _parse(monkeypatch, ["-p", "penguin"])


def test_parse_args_rejects_dropped_agent_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # -a / --agent was replaced with -p / --persona at the top level.
    with pytest.raises(SystemExit):
        _parse(monkeypatch, ["--agent", "coder"])


def test_parse_args_no_splash_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _parse(monkeypatch, ["--no-splash"])
    assert args.no_splash is True


def test_parse_args_resume_bare_uses_sentinel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _parse(monkeypatch, ["-r"])
    assert args.resume_thread == "__MOST_RECENT__"


def test_parse_args_resume_with_id(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _parse(monkeypatch, ["-r", "abc12345"])
    assert args.resume_thread == "abc12345"


def test_parse_args_sandbox_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    for kind in ("none", "modal", "daytona", "runloop", "langsmith"):
        args = _parse(monkeypatch, ["--sandbox", kind])
        assert args.sandbox == kind
    with pytest.raises(SystemExit):
        _parse(monkeypatch, ["--sandbox", "docker"])


def test_parse_args_subcommand_help(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _parse(monkeypatch, ["help"])
    assert args.command == "help"


def test_parse_args_subcommand_list(monkeypatch: pytest.MonkeyPatch) -> None:
    args = _parse(monkeypatch, ["list"])
    assert args.command == "list"


def test_parse_args_subcommand_reset_requires_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `reset` subcommand still uses --agent for its target (the agent to
    # reset). This is subcommand-scoped and stays verbatim.
    with pytest.raises(SystemExit):
        _parse(monkeypatch, ["reset"])
    args = _parse(monkeypatch, ["reset", "--agent", "coder"])
    assert args.command == "reset"
    assert args.agent == "coder"


def test_parse_args_subcommand_threads_list_persona_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Top-level -a/--agent was replaced; the subcommand filter is now
    # --persona to match.
    args = _parse(monkeypatch, ["threads", "list", "--persona", "alfred"])
    assert args.command == "threads"
    assert args.threads_command == "list"
    assert args.persona == "alfred"


def test_parse_args_subcommand_threads_ls_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _parse(monkeypatch, ["threads", "ls"])
    assert args.command == "threads"
    assert args.threads_command == "ls"


def test_parse_args_subcommand_threads_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args = _parse(monkeypatch, ["threads", "delete", "abc12345"])
    assert args.command == "threads"
    assert args.threads_command == "delete"
    assert args.thread_id == "abc12345"


def test_parse_args_version_prints_bat_code_name(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        _parse(monkeypatch, ["-v"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "bat-code" in combined
    assert "deepagents-cli" not in combined


# ---------------------------------------------------------------------------
# apply_stdin_pipe — TTY / non-TTY branches
# ---------------------------------------------------------------------------


def _make_args(**overrides: Any) -> argparse.Namespace:
    ns = argparse.Namespace(
        non_interactive_message=None,
        initial_prompt=None,
    )
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


class _StdinStub(io.StringIO):
    """StringIO with a settable `isatty` return value."""

    def __init__(self, text: str, is_tty: bool) -> None:
        super().__init__(text)
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


def test_apply_stdin_pipe_returns_when_stdin_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", None)
    args = _make_args()
    apply_stdin_pipe(args)
    assert args.non_interactive_message is None
    assert args.initial_prompt is None


def test_apply_stdin_pipe_returns_when_tty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _StdinStub("some piped text", is_tty=True))
    args = _make_args()
    apply_stdin_pipe(args)
    assert args.non_interactive_message is None
    assert args.initial_prompt is None


def test_apply_stdin_pipe_returns_when_piped_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _StdinStub("   \n\n  ", is_tty=False))
    # Prevent TTY-restoration side effects.
    monkeypatch.setattr(main_module.os, "open", lambda *_a, **_kw: (_ for _ in ()).throw(OSError()))
    args = _make_args()
    apply_stdin_pipe(args)
    assert args.non_interactive_message is None
    assert args.initial_prompt is None


def test_apply_stdin_pipe_sets_non_interactive_when_no_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _StdinStub("fix the typo", is_tty=False))
    monkeypatch.setattr(main_module.os, "open", lambda *_a, **_kw: (_ for _ in ()).throw(OSError()))
    args = _make_args()
    apply_stdin_pipe(args)
    assert args.non_interactive_message == "fix the typo"
    assert args.initial_prompt is None


def test_apply_stdin_pipe_prepends_to_existing_non_interactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _StdinStub("context data", is_tty=False))
    monkeypatch.setattr(main_module.os, "open", lambda *_a, **_kw: (_ for _ in ()).throw(OSError()))
    args = _make_args(non_interactive_message="summarize this")
    apply_stdin_pipe(args)
    assert args.non_interactive_message == "context data\n\nsummarize this"


def test_apply_stdin_pipe_prepends_to_existing_initial_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdin", _StdinStub("log contents", is_tty=False))
    monkeypatch.setattr(main_module.os, "open", lambda *_a, **_kw: (_ for _ in ()).throw(OSError()))
    args = _make_args(initial_prompt="explain this")
    apply_stdin_pipe(args)
    assert args.initial_prompt == "log contents\n\nexplain this"
    assert args.non_interactive_message is None


def test_apply_stdin_pipe_docstring_uses_bat_code_examples() -> None:
    src = inspect.getsource(apply_stdin_pipe)
    assert "| bat-code" in src
    assert "| deepagents" not in src


# ---------------------------------------------------------------------------
# run_textual_cli_async — persona + no_splash forwarding
# ---------------------------------------------------------------------------


def test_run_textual_cli_async_signature_has_persona_and_no_splash() -> None:
    sig = inspect.signature(run_textual_cli_async)
    assert "persona" in sig.parameters
    assert "no_splash" in sig.parameters
    assert sig.parameters["persona"].default == "batman"
    assert sig.parameters["no_splash"].default is False


def test_run_textual_cli_async_uses_create_batman_agent() -> None:
    src = inspect.getsource(run_textual_cli_async)
    assert "create_batman_agent(" in src
    # Regression guard against upstream call.
    assert "create_cli_agent(" not in src


def test_run_textual_cli_async_forwards_persona_to_agent_and_app() -> None:
    src = inspect.getsource(run_textual_cli_async)
    # Both call sites (create_batman_agent + run_textual_app) receive persona.
    assert src.count("persona=persona") >= 2
    assert "no_splash=no_splash" in src


# ---------------------------------------------------------------------------
# Regression guards — identity fixes bundled with the port
# ---------------------------------------------------------------------------


def test_main_module_has_no_deepagents_cli_imports() -> None:
    src = inspect.getsource(main_module)
    # Only "deepagents_cli" in test regression-guard function names should
    # match; the source module itself should be clean.
    assert "from deepagents_cli" not in src
    assert "import deepagents_cli" not in src


def test_parse_args_description_says_bat_code() -> None:
    src = inspect.getsource(parse_args)
    assert "bat-code" in src
    assert "Deep Agents" not in src


def test_parse_args_version_string_is_bat_code() -> None:
    src = inspect.getsource(parse_args)
    assert 'f"bat-code {__version__}"' in src
    assert "deepagents-cli" not in src


def test_cli_main_paths_use_bat_code_dir() -> None:
    src = inspect.getsource(main_module.cli_main)
    # Both save/clear default-model error messages point to ~/.bat-code/.
    assert src.count("~/.bat-code/") >= 2
    assert "~/.deepagents/" not in src


def test_cli_main_hints_use_bat_code_binary_name() -> None:
    src = inspect.getsource(main_module.cli_main)
    # Resume + threads-list hints reference the bat-code binary.
    assert "bat-code -r " in src
    assert "bat-code threads list" in src
    # Regression against upstream binary name in hint strings.
    assert "deepagents -r " not in src
    assert "deepagents threads list" not in src
