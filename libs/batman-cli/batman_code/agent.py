"""Agent management and creation for Bat-Code."""

import os
import shutil
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.sandbox import SandboxBackendProtocol
from deepagents.middleware import MemoryMiddleware, SkillsMiddleware

from batman_code.backends import CLIShellBackend, patch_filesystem_middleware

if TYPE_CHECKING:
    from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain.agents.middleware import (
    InterruptOnConfig,
)
from langchain.agents.middleware.types import AgentState
from langchain.messages import ToolCall
from langchain.tools import BaseTool
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.pregel import Pregel
from langgraph.runtime import Runtime

from batman_code.config import (
    COLORS,
    config,
    console,
    get_default_coding_instructions,
    get_glyphs,
    settings,
)
from batman_code.integrations.sandbox_factory import get_default_working_dir
from batman_code.local_context import LocalContextMiddleware
from batman_code.prompts import load_persona
from batman_code.subagents import list_subagents

DEFAULT_AGENT_NAME = "agent"
"""The default agent name used when no `-a` flag is provided."""


def list_agents() -> None:
    """List all available agents."""
    agents_dir = settings.user_deepagents_dir

    if not agents_dir.exists() or not any(agents_dir.iterdir()):
        console.print("[yellow]No agents found.[/yellow]")
        console.print(
            "[dim]Agents will be created in ~/.bat-code/ "
            "when you first use them.[/dim]",
            style=COLORS["dim"],
        )
        return

    console.print("\n[bold]Available Agents:[/bold]\n", style=COLORS["primary"])

    for agent_path in sorted(agents_dir.iterdir()):
        if agent_path.is_dir():
            agent_name = agent_path.name
            agent_md = agent_path / "AGENTS.md"
            is_default = agent_name == DEFAULT_AGENT_NAME
            default_label = " [dim](default)[/dim]" if is_default else ""

            bullet = get_glyphs().bullet
            if agent_md.exists():
                console.print(
                    f"  {bullet} [bold]{agent_name}[/bold]{default_label}",
                    style=COLORS["primary"],
                )
                console.print(f"    {agent_path}", style=COLORS["dim"])
            else:
                console.print(
                    f"  {bullet} [bold]{agent_name}[/bold]{default_label}"
                    " [dim](incomplete)[/dim]",
                    style=COLORS["tool"],
                )
                console.print(f"    {agent_path}", style=COLORS["dim"])

    console.print()


def reset_agent(agent_name: str, source_agent: str | None = None) -> None:
    """Reset an agent to default or copy from another agent."""
    agents_dir = settings.user_deepagents_dir
    agent_dir = agents_dir / agent_name

    if source_agent:
        source_dir = agents_dir / source_agent
        source_md = source_dir / "AGENTS.md"

        if not source_md.exists():
            console.print(
                f"[bold red]Error:[/bold red] Source agent '{source_agent}' not found "
                "or has no AGENTS.md"
            )
            return

        source_content = source_md.read_text()
        action_desc = f"contents of agent '{source_agent}'"
    else:
        source_content = get_default_coding_instructions()
        action_desc = "default"

    if agent_dir.exists():
        shutil.rmtree(agent_dir)
        console.print(
            f"Removed existing agent directory: {agent_dir}", style=COLORS["tool"]
        )

    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_md = agent_dir / "AGENTS.md"
    agent_md.write_text(source_content)

    console.print(
        f"{get_glyphs().checkmark} Agent '{agent_name}' reset to {action_desc}",
        style=COLORS["primary"],
    )
    console.print(f"Location: {agent_dir}\n", style=COLORS["dim"])


def get_system_prompt(
    assistant_id: str,
    sandbox_type: str | None = None,
    persona: str = "batman",
) -> str:
    """Get the base system prompt for the agent.

    Loads the immutable system prompt from ``system_prompt.md`` and
    interpolates dynamic sections (model identity, working directory,
    skills path, persona instructions).

    Args:
        assistant_id: The agent identifier for path references.
        sandbox_type: Type of sandbox provider
            (``'daytona'``, ``'langsmith'``, ``'modal'``, ``'runloop'``).
            If ``None``, agent is operating in local mode.
        persona: Name of the persona to inject (e.g. ``'batman'``,
            ``'alfred'``, ``'joker'``).

    Returns:
        The fully interpolated system prompt string.
    """
    template = (Path(__file__).parent / "system_prompt.md").read_text()

    skills_path = f"~/.bat-code/{assistant_id}/skills/"

    # Build model identity section
    model_identity_section = ""
    if settings.model_name:
        model_identity_section = (
            f"### Model Identity\n\nYou are running as model `{settings.model_name}`"
        )
        if settings.model_provider:
            model_identity_section += f" (provider: {settings.model_provider})"
        model_identity_section += ".\n"
        if settings.model_context_limit:
            model_identity_section += (
                f"Your context window is {settings.model_context_limit:,} tokens.\n"
            )
        model_identity_section += "\n"

    # Build working directory section (local vs sandbox)
    if sandbox_type:
        working_dir = get_default_working_dir(sandbox_type)
        working_dir_section = (
            f"### Current Working Directory\n\n"
            f"You are operating in a **remote Linux sandbox** at `{working_dir}`.\n\n"
            f"All code execution and file operations happen in this sandbox "
            f"environment.\n\n"
            f"**Important:**\n"
            f"- The CLI is running locally on the user's machine, but you execute "
            f"code remotely\n"
            f"- Use `{working_dir}` as your working directory for all operations\n\n"
        )
    else:
        cwd = Path.cwd()
        working_dir_section = (
            f"### Current Working Directory\n\n"
            f"The filesystem backend is currently operating in: `{cwd}`\n\n"
            f"### File System and Paths\n\n"
            f"**IMPORTANT - Path Handling:**\n"
            f"- All file paths must be absolute paths (e.g., `{cwd}/file.txt`)\n"
            f"- Use the working directory to construct absolute paths\n"
            f"- Example: To create a file in your working directory, "
            f"use `{cwd}/research_project/file.md`\n"
            f"- Never use relative paths - always construct full absolute paths\n\n"
        )

    # Load and inject persona instructions
    persona_content = load_persona(persona)

    return (
        template.replace("{model_identity_section}", model_identity_section)
        .replace("{working_dir_section}", working_dir_section)
        .replace("{skills_path}", skills_path)
        .replace("{persona_instructions}", persona_content)
    )


def _format_write_file_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format write_file tool call for approval prompt."""
    args = tool_call["args"]
    file_path = args.get("file_path", "unknown")
    content = args.get("content", "")

    action = "Overwrite" if Path(file_path).exists() else "Create"
    line_count = len(content.splitlines())

    return f"File: {file_path}\nAction: {action} file\nLines: {line_count}"


def _format_edit_file_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format edit_file tool call for approval prompt."""
    args = tool_call["args"]
    file_path = args.get("file_path", "unknown")
    replace_all = bool(args.get("replace_all", False))

    scope = "all occurrences" if replace_all else "single occurrence"
    return f"File: {file_path}\nAction: Replace text ({scope})"


def _format_web_search_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format web_search tool call for approval prompt."""
    args = tool_call["args"]
    query = args.get("query", "unknown")
    max_results = args.get("max_results", 5)

    return (
        f"Query: {query}\nMax results: {max_results}\n\n"
        f"{get_glyphs().warning}  This will use Tavily API credits"
    )


def _format_fetch_url_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format fetch_url tool call for approval prompt."""
    args = tool_call["args"]
    url = args.get("url", "unknown")
    timeout = args.get("timeout", 30)

    return (
        f"URL: {url}\nTimeout: {timeout}s\n\n"
        f"{get_glyphs().warning}  Will fetch and convert web content to markdown"
    )


def _format_task_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format task (subagent) tool call for approval prompt."""
    args = tool_call["args"]
    description = args.get("description", "unknown")
    subagent_type = args.get("subagent_type", "unknown")

    # Truncate description if too long for display
    description_preview = description
    if len(description) > 500:
        description_preview = description[:500] + "..."

    glyphs = get_glyphs()
    separator = glyphs.box_horizontal * 40
    warning_msg = "Subagent will have access to file operations and shell commands"
    return (
        f"Subagent Type: {subagent_type}\n\n"
        f"Task Instructions:\n"
        f"{separator}\n"
        f"{description_preview}\n"
        f"{separator}\n\n"
        f"{glyphs.warning}  {warning_msg}"
    )


def _format_execute_description(
    tool_call: ToolCall, _state: AgentState[Any], _runtime: Runtime[Any]
) -> str:
    """Format execute tool call for approval prompt."""
    args = tool_call["args"]
    command = args.get("command", "N/A")
    return f"Execute Command: {command}\nWorking Directory: {Path.cwd()}"


def _add_interrupt_on() -> dict[str, InterruptOnConfig]:
    """Configure human-in-the-loop interrupt settings for all gated tools."""
    execute_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_execute_description,  # type: ignore[typeddict-item]
    }

    write_file_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_write_file_description,  # type: ignore[typeddict-item]
    }

    edit_file_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_edit_file_description,  # type: ignore[typeddict-item]
    }

    web_search_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_web_search_description,  # type: ignore[typeddict-item]
    }

    fetch_url_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_fetch_url_description,  # type: ignore[typeddict-item]
    }

    task_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": _format_task_description,  # type: ignore[typeddict-item]
    }

    return {
        "execute": execute_interrupt_config,
        "write_file": write_file_interrupt_config,
        "edit_file": edit_file_interrupt_config,
        "web_search": web_search_interrupt_config,
        "fetch_url": fetch_url_interrupt_config,
        "task": task_interrupt_config,
    }


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
    """Create a Bat-Code agent with persona injection.

    Mirrors ``create_cli_agent`` from deepagents-cli with one addition:
    the ``persona`` parameter loads a character prompt and injects it
    into the system prompt at ``{persona_instructions}``.

    When ``persona`` is ``'joker'``, ``auto_approve`` is forced to
    ``True`` (DARK KNIGHT MODE).

    Args:
        model: LLM model to use (e.g., ``'anthropic:claude-sonnet-4-5-20250929'``).
        assistant_id: Agent identifier for memory/state storage.
        persona: Persona name (batman, alfred, oracle, nightwing, joker).
        tools: Additional tools to provide to agent.
        sandbox: Optional sandbox backend for remote execution.
        sandbox_type: Type of sandbox provider.
        system_prompt: Override the default system prompt.
        auto_approve: If ``True``, no tools trigger approval prompts.
        enable_memory: Enable ``MemoryMiddleware`` for persistent memory.
        enable_skills: Enable ``SkillsMiddleware`` for custom agent skills.
        enable_shell: Enable shell execution via ``CLIShellBackend``.
        checkpointer: Optional checkpointer for session persistence.

    Returns:
        2-tuple of ``(agent_graph, composite_backend)``.
    """
    # Joker persona always enables auto-approve (DARK KNIGHT MODE)
    if persona == "joker":
        auto_approve = True

    tools = tools or []

    # Setup agent directory for persistent memory (if enabled)
    if enable_memory or enable_skills:
        agent_dir = settings.ensure_agent_dir(assistant_id)
        agent_md = agent_dir / "AGENTS.md"
        if not agent_md.exists():
            agent_md.touch()

    # Skills directories (if enabled)
    skills_dir = None
    project_skills_dir = None
    if enable_skills:
        skills_dir = settings.ensure_user_skills_dir(assistant_id)
        project_skills_dir = settings.get_project_skills_dir()

    # Load custom subagents from filesystem
    custom_subagents: list[SubAgent | CompiledSubAgent] = []
    user_agents_dir = settings.get_user_agents_dir(assistant_id)
    project_agents_dir = settings.get_project_agents_dir()

    for subagent_meta in list_subagents(
        user_agents_dir=user_agents_dir,
        project_agents_dir=project_agents_dir,
    ):
        subagent: SubAgent = {
            "name": subagent_meta["name"],
            "description": subagent_meta["description"],
            "system_prompt": subagent_meta["system_prompt"],
        }
        if subagent_meta["model"]:
            subagent["model"] = subagent_meta["model"]
        custom_subagents.append(subagent)

    # Build middleware stack based on enabled features
    agent_middleware = []

    # Add memory middleware
    if enable_memory:
        memory_sources = [str(settings.get_user_agent_md_path(assistant_id))]
        project_agent_md = settings.get_project_agent_md_path()
        if project_agent_md:
            memory_sources.append(str(project_agent_md))

        agent_middleware.append(
            MemoryMiddleware(
                backend=FilesystemBackend(),
                sources=memory_sources,
            )
        )

    # Add skills middleware
    if enable_skills:
        sources = [str(settings.get_built_in_skills_dir())]
        sources.append(str(skills_dir))
        if project_skills_dir:
            sources.append(str(project_skills_dir))

        agent_middleware.append(
            SkillsMiddleware(
                backend=FilesystemBackend(),
                sources=sources,
            )
        )

    # CONDITIONAL SETUP: Local vs Remote Sandbox
    if sandbox is None:
        # ========== LOCAL MODE ==========
        if enable_shell:
            shell_env = os.environ.copy()
            if settings.user_langchain_project:
                shell_env["LANGSMITH_PROJECT"] = settings.user_langchain_project

            backend = CLIShellBackend(
                root_dir=Path.cwd(),
                inherit_env=True,
                env=shell_env,
            )
        else:
            backend = FilesystemBackend()

        # Local context middleware (git info, directory tree, etc.)
        agent_middleware.append(LocalContextMiddleware())
    else:
        # ========== REMOTE SANDBOX MODE ==========
        backend = sandbox

    # Get or use custom system prompt
    if system_prompt is None:
        system_prompt = get_system_prompt(
            assistant_id=assistant_id,
            sandbox_type=sandbox_type,
            persona=persona,
        )

    # Configure interrupt_on based on auto_approve setting
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None
    if auto_approve:
        interrupt_on = {}
    else:
        interrupt_on = _add_interrupt_on()  # type: ignore[assignment]

    # Set up composite backend with routing
    if sandbox is None:
        large_results_backend = FilesystemBackend(
            root_dir=tempfile.mkdtemp(prefix="batcode_large_results_"),
            virtual_mode=True,
        )
        conversation_history_backend = FilesystemBackend(
            root_dir=tempfile.mkdtemp(prefix="batcode_conversation_history_"),
            virtual_mode=True,
        )
        composite_backend = CompositeBackend(
            default=backend,
            routes={
                "/large_tool_results/": large_results_backend,
                "/conversation_history/": conversation_history_backend,
            },
        )
    else:
        composite_backend = CompositeBackend(
            default=backend,
            routes={},
        )

    # Create the agent
    if sandbox is None and enable_shell:
        patch_filesystem_middleware()
    final_checkpointer = checkpointer if checkpointer is not None else InMemorySaver()
    agent = create_deep_agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        backend=composite_backend,
        middleware=agent_middleware,
        interrupt_on=interrupt_on,
        checkpointer=final_checkpointer,
        subagents=custom_subagents or None,
    ).with_config(config)
    return agent, composite_backend
