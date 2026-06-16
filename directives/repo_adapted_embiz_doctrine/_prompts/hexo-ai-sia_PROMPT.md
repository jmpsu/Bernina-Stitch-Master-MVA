Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: hexo-ai-sia
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/hexo-ai-sia_SOURCE_BUNDLE.md

EMBIZ context:
- Root: /root/embroidery_business_agent_system
- Local corpus: /root/web-archive/ai_agents_skills_library
- OpenClaw: /root/.openclaw/workspace
- Agent bus: /usr/local/bin/agent-msg
- Slack mirror outbound-only; no secrets.
- Human approval required before customer contact.
- Human approval required before digitizing.
- Never claim SVG/PES/DST/EXP/INF/BMP exists unless file exists on disk.
- Named agents: Maya, Madeline, Morgan, Mila, Melanie, Mackenzie, Marina, Monica, Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

You must adapt this repo into EMBIZ doctrine, not summarize it.

Write these sections:
# hexo-ai-sia EMBIZ ADAPTED DOCTRINE
## Source Material Read
## What This Repo Contributes To EMBIZ
## EMBIZ-Specific Adaptation
## Assigned Agent Ownership
## Local Skill / Knowledge Library Integration
## Runtime Rules
## Required Files / Configs
## Commands / Checks
## Security Restrictions
## Verification Checklist
## Build Tasks
## What Not To Use
## Integration Status

Now use this source bundle:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/__init__.py =====

"""SIA: Self-Improving AI framework"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sia-agent")
except PackageNotFoundError:  # package is not installed (e.g. running from source)
    __version__ = "0.0.0+unknown"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/__main__.py =====

"""Allow running sia as `python -m sia`."""

from sia.orchestrator import main

if __name__ == "__main__":
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_impls/__init__.py =====

"""Agent-implementation registry package.

Importing this package registers all built-in agent impls (claude, openhands,
pydantic-ai) without importing their optional SDKs.
"""

# Import agent-impl modules for their registration side effects.
from sia.agent_impls import claude, openhands, pydantic_ai  # noqa: F401  (registers impls)
from sia.agent_impls.base import available_agent_impls, get_agent_impl, register, run_agent

__all__ = ["available_agent_impls", "get_agent_impl", "register", "run_agent"]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_impls/base.py =====

"""Agent-implementation registry.

An *agent impl* runs a meta/feedback agent: an async runner with the signature
``run(model_name, max_turns, prompt, agent_working_directory)``. Implementations
register themselves by a unique id; the orchestrator and CLI discover them via this
registry, so adding one is a single ``register(...)`` call. Optional SDK imports
happen lazily inside each runner, so the registry lists every impl regardless of
what's installed.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from sia.logging_setup import get_logger

if TYPE_CHECKING:
    from sia.providers import Provider

logger = get_logger(__name__)

# Runners accept (model_name, max_turns, prompt, working_dir) and an optional provider
# (keyword, default None) describing the endpoint/credentials for the meta agent.
AgentRunner = Callable[..., Awaitable[None]]

REGISTRY: dict[str, AgentRunner] = {}


def register(name: str, runner: AgentRunner) -> AgentRunner:
    """Register an agent-impl runner under ``name``."""
    REGISTRY[name] = runner
    return runner


def available_agent_impls() -> list[str]:
    """Ids of all registered agent impls."""
    return list(REGISTRY)


def get_agent_impl(name: str) -> AgentRunner:
    """Return the runner registered under ``name`` (raises ValueError if unknown)."""
    if name not in REGISTRY:
        available = ", ".join(available_agent_impls())
        raise ValueError(f"Unknown agent impl: {name}. Available: {available}")
    return REGISTRY[name]


async def run_agent(
    model_name: str,
    max_turns: str,
    prompt: str,
    agent_working_directory: str,
    agent_impl: str = "claude",
    provider: Provider | None = None,
) -> None:
    """Dispatch to the named agent impl.

    Args:
        model_name: The model to use (format depends on the agent impl).
        max_turns: Maximum number of turns for the agent.
        prompt: The task prompt to send to the agent.
        agent_working_directory: Working directory for the agent.
        agent_impl: Which registered impl to use (e.g. "claude", "openhands", "pydantic-ai").
        provider: Optional endpoint/credentials for the model (api_key_env, base_url).
    """
    logger.info(f"Using {agent_impl} agent impl")
    await get_agent_impl(agent_impl)(model_name, max_turns, prompt, agent_working_directory, provider=provider)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_impls/claude.py =====

"""Claude Code SDK agent impl."""

from __future__ import annotations

from datetime import datetime

from sia.agent_impls.base import register
from sia.logging_setup import get_logger

logger = get_logger(__name__)


async def run_agent_claude(model_name, max_turns, prompt, agent_working_directory, provider=None):
    """Run agent using Claude Code SDK

    The ``provider`` argument is accepted for a uniform agent-impl signature but ignored:
    the Claude Code SDK authenticates against Anthropic natively (ANTHROPIC_API_KEY).

    Note: Claude Code automatically saves trajectories to ~/.claude/projects/
    """
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    logger.info(f"Starting agent execution with {model_name} model (max turns: {max_turns})")
    logger.debug("=" * 80)
    logger.debug(f"Working directory: {agent_working_directory}")
    logger.debug("=" * 80)

    turn_count = 0
    start_time = datetime.now()

    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                cwd=agent_working_directory,
                allowed_tools=["Bash", "Read", "Write", "Edit", "Glob"],
                permission_mode="bypassPermissions",
                max_turns=max_turns,
                model=model_name,
            ),
        ):
            logged_content = False

            if hasattr(message, "content") and message.content:
                for block in message.content:
                    # Log agent text responses
                    if hasattr(block, "text") and block.text:
                        if not logged_content:
                            turn_count += 1
                            logger.debug(f"\n{'─' * 80}")
                            logger.debug(f"TURN {turn_count}: Agent Response")
                            logger.debug(f"{'─' * 80}")
                            logged_content = True
                        logger.debug(f"{block.text}")

                    # Log tool calls
                    elif hasattr(block, "name"):
                        if not logged_content:
                            turn_count += 1
                            logger.debug(f"\n{'─' * 80}")
                            logger.debug(f"TURN {turn_count}: Tool Execution")
                            logger.debug(f"{'─' * 80}")
                            logged_content = True

                        logger.debug(f"🔧 Tool: {block.name}")
                        if hasattr(block, "input") and block.input:
                            # Pretty print tool input
                            import json

                            try:
                                input_str = json.dumps(block.input, indent=2)
                                logger.debug(f"   Input: {input_str}")
                            except (TypeError, ValueError):
                                logger.debug(f"   Input: {block.input}")

                    # Log tool results
                    elif hasattr(block, "type") and block.type == "tool_result":
                        if hasattr(block, "content"):
                            result = block.content if isinstance(block.content, str) else str(block.content)
                            # Truncate very long outputs
                            if len(result) > 500:
                                result = result[:500] + f"\n... (truncated, {len(result)} total chars)"
                            logger.debug(f"   ✓ Result: {result}")

            # Log final result
            if isinstance(message, ResultMessage):
                elapsed_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"\n{'=' * 80}")
                logger.debug(f"Final result: {message.result}")
                logger.debug(f"{'=' * 80}")
                logger.info(f"Execution complete: {turn_count} turns in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"ERROR: {e!s}")
        logger.error(f"{'!' * 80}", exc_info=True)
        raise


register("claude", run_agent_claude)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_impls/openhands.py =====

"""OpenHands SDK agent impl."""

from __future__ import annotations

import os
from datetime import datetime

from sia.agent_impls.base import register
from sia.api_keys import resolve_api_key
from sia.logging_setup import get_logger

logger = get_logger(__name__)


def _resolve_model(model_name, provider=None):
    """Resolve the litellm model spec OpenHands' LLM should use.

    litellm derives the provider from the model string's prefix. For an
    OpenAI-compatible endpoint (a provider with ``client_kind == "openai"`` and a
    ``base_url``), the model must carry an explicit ``openai/`` prefix so litellm
    routes to that ``base_url`` instead of trying to parse the model's own namespace
    (e.g. ``moonshotai/Kimi-K2.6``) as a provider. Already-prefixed and native
    (anthropic) specs pass through unchanged.
    """
    if provider is None or not isinstance(model_name, str):
        return model_name
    if provider.client_kind == "openai" and provider.base_url and not model_name.startswith("openai/"):
        return f"openai/{model_name}"
    return model_name


async def run_agent_openhands(model_name, max_turns, prompt, agent_working_directory, provider=None):
    """Run agent using OpenHands SDK"""
    try:
        from openhands.sdk import LLM, Agent, Conversation, Tool
        from openhands.tools.file_editor import FileEditorTool
        from openhands.tools.terminal import TerminalTool
    except ImportError:
        logger.error("OpenHands SDK not installed. Install with: pip install openhands-ai")
        raise

    logger.info(f"Starting OpenHands agent execution with {model_name} model (max turns: {max_turns})")
    logger.debug("=" * 80)
    logger.debug(f"Working directory: {agent_working_directory}")
    logger.debug("=" * 80)

    turn_count = 0
    start_time = datetime.now()

    try:
        # Determine API key + base_url. An explicit provider takes precedence; otherwise
        # infer the key from the model name.
        base_url = provider.base_url if provider else None
        api_key = os.getenv(provider.api_key_env) if provider else resolve_api_key(model_name)
        if not api_key:
            logger.warning(f"No API key found for model {model_name}. Using LLM_API_KEY if available.")
            api_key = os.getenv("LLM_API_KEY")

        # Create LLM instance. litellm needs an explicit provider prefix to route to a
        # custom OpenAI-compatible base_url (see _resolve_model).
        llm = LLM(
            model=_resolve_model(model_name, provider),
            api_key=api_key,
            base_url=base_url,
        )

        # Create agent with available tools
        agent = Agent(
            llm=llm,
            tools=[
                Tool(name=TerminalTool.name),
                Tool(name=FileEditorTool.name),
            ],
        )

        # Create conversation with workspace and persistence
        # Trajectory will be saved in: agent_working_directory/openhands_trajectory/
        trajectory_dir = os.path.join(agent_working_directory, "openhands_trajectory")

        conversation = Conversation(agent=agent, workspace=agent_working_directory, persistence_dir=trajectory_dir)

        # Send the task prompt
        logger.debug(f"\n{'─' * 80}")
        logger.debug(f"TURN {turn_count + 1}: Sending prompt to agent")
        logger.debug(f"{'─' * 80}")
        conversation.send_message(prompt)

        # Run the agent
        logger.info(f"Running agent (max turns: {max_turns})...")
        logger.debug(f"  → Trajectory will be saved to: {trajectory_dir}")
        result = conversation.run()

        # Log completion
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"\n{'=' * 80}")
        logger.debug(f"Final result: {result}")
        logger.debug(f"{'=' * 80}")
        logger.info(f"Execution complete in {elapsed_time:.2f} seconds")
        logger.debug(f"  ✓ Trajectory saved to: {trajectory_dir}")

    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"ERROR: {e!s}")
        logger.error(f"{'!' * 80}", exc_info=True)
        raise


register("openhands", run_agent_openhands)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_impls/pydantic_ai.py =====

"""PydanticAI agent impl for running meta/feedback agents.

Builds a PydanticAI Agent with bash + file tools and caps iterations via
UsageLimits. The PydanticAI SDK is imported lazily so the impl can be listed in
the registry even when the optional ``[pydantic-ai]`` extra isn't installed.

The model spec is passed through to PydanticAI's native model parsing (e.g.
"openai:gpt-4o", "anthropic:claude-...", "google-gla:gemini-..."); a non-string
(a PydanticAI Model instance) is used as-is (e.g. TestModel in tests).
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime

from sia.agent_impls.base import register
from sia.config import Config
from sia.logging_setup import get_logger

logger = get_logger(__name__)


def _resolve_model(model_name, provider=None):
    """Resolve the model spec for PydanticAI.

    Without a provider (or for a non-string spec like TestModel) the value is passed
    through to PydanticAI's native parsing. For an OpenAI-compatible provider with a
    base_url, build an OpenAIChatModel pointed at that endpoint.
    """
    if not isinstance(model_name, str) or provider is None:
        return model_name
    if provider.client_kind == "openai" and provider.base_url:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(base_url=provider.base_url, api_key=os.getenv(provider.api_key_env)),
        )
    return model_name


def _make_tools(working_dir: str):
    """File + bash tools operating within ``working_dir`` (paths resolve relative to it)."""

    def _resolve(path: str) -> str:
        return path if os.path.isabs(path) else os.path.join(working_dir, path)

    def write_file(path: str, content: str) -> str:
        """Write (overwrite) a file with the given content."""
        target = _resolve(path)
        try:
            parent = os.path.dirname(target)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written {len(content)} characters to '{target}'."
        except OSError as e:
            return f"Error writing file: {e}"

    def read_file(path: str) -> str:
        """Read and return the contents of a file."""
        target = _resolve(path)
        try:
            with open(target, encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File '{target}' not found."
        except OSError as e:
            return f"Error reading file: {e}"

    def bash(command: str) -> str:
        """Run a bash command in the working directory and return stdout + stderr."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=Config().SHELL_TIMEOUT,
                cwd=working_dir,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out."
        except OSError as e:
            return f"Error running command: {e}"

    return [write_file, read_file, bash]


async def run_agent_pydantic_ai(model_name, max_turns, prompt, agent_working_directory, provider=None):
    """Run a meta/feedback agent using the PydanticAI Agent framework."""
    try:
        from pydantic_ai import Agent
        from pydantic_ai.usage import UsageLimits
    except ImportError:
        logger.error("PydanticAI not installed. Install with: pip install 'sia-agent[pydantic-ai]'")
        raise

    logger.info(f"Starting PydanticAI agent execution with {model_name} model (max turns: {max_turns})")
    logger.debug("=" * 80)
    logger.debug(f"Working directory: {agent_working_directory}")
    logger.debug("=" * 80)

    start_time = datetime.now()

    try:
        request_limit = int(max_turns)
    except (TypeError, ValueError):
        request_limit = Config().DEFAULT_MAX_TURNS

    try:
        agent = Agent(_resolve_model(model_name, provider), tools=_make_tools(agent_working_directory))
        result = await agent.run(prompt, usage_limits=UsageLimits(request_limit=request_limit))

        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.debug(f"\n{'=' * 80}")
        logger.debug(f"Final result: {result.output}")
        logger.debug(f"{'=' * 80}")
        logger.info(f"Execution complete in {elapsed_time:.2f} seconds")

    except Exception as e:
        logger.error(f"\n{'!' * 80}")
        logger.error(f"ERROR: {e!s}")
        logger.error(f"{'!' * 80}", exc_info=True)
        raise


register("pydantic-ai", run_agent_pydantic_ai)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/agent_reference.py =====

"""The target agent's *reference*: where its improvable seed code + deps come from.

A target-agent profile carries an ``agent_reference`` describing the seed the
meta-agent starts from and the feedback-agent iterates on:

- ``"default"`` — the task package's bundled ``reference/`` directory (entrypoint
  ``reference_target_agent.py``). This is the historical behavior.
- ``{"source": "./my_agent.py"}`` — a single user file. Its text is embedded in the
  meta-agent prompt (the "basic" reference).
- ``{"source": "./my_agent_dir/", "entrypoint": "main.py"}`` — a multi-file
  directory. SIA copies it into each generation's working dir and the agent reads it
  with its own tools rather than having it piped into the prompt.

A reference has two separable parts: the **improvable seed source** (stays editable —
SIA rewrites it every generation) and its **dependencies**. Dependencies live in a
``requirements.txt`` *inside the reference* (not a profile field) so the meta/feedback
agents can evolve them across generations; they are installed per generation and
augment the global ``Config.VENV_PACKAGES`` baseline.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from sia.layout import Names

if TYPE_CHECKING:
    from sia.layout import TaskLayout


@dataclass(frozen=True)
class AgentReference:
    """A parsed ``agent_reference`` spec (paths already resolved to absolute)."""

    kind: str  # "default" | "file" | "dir"
    source: Path | None = None  # abs path to the file (file) or directory (dir); None for default
    entrypoint: str | None = None  # filename within the directory (dir only)


DEFAULT_AGENT_REFERENCE = AgentReference(kind="default")


@dataclass(frozen=True)
class ResolvedAgentReference:
    """An ``AgentReference`` resolved against a concrete task, ready to use."""

    inline_seed: str | None  # entrypoint text to embed in the prompt (default/file); None for a dir
    ref_dir: Path | None  # directory whose contents are copied into each gen working dir (dir only)
    entrypoint: str  # filename the agent should treat as the starting point
    requirements: Path | None  # requirements.txt to install + carry forward, if present


def parse_agent_reference(spec: object, base_dir: str | Path | None = None) -> AgentReference:
    """Parse a raw ``agent_reference`` value from a profile JSON into an AgentReference.

    ``base_dir`` is the directory the profile file lives in; a relative ``source``
    resolves against it (falling back to the current working directory).
    """
    if spec is None or spec == "default":
        return DEFAULT_AGENT_REFERENCE
    if not isinstance(spec, dict) or "source" not in spec:
        raise SystemExit('agent_reference must be "default" or an object with a "source" field')

    data = cast("dict[str, Any]", spec)
    base = Path(base_dir) if base_dir else Path.cwd()
    source = Path(data["source"])
    if not source.is_absolute():
        source = base / source
    source = source.resolve()

    if source.is_dir():
        return AgentReference(kind="dir", source=source, entrypoint=data.get("entrypoint"))
    if source.is_file():
        return AgentReference(kind="file", source=source)
    raise SystemExit(f"agent_reference source not found: {source}")


def resolve_agent_reference(ref: AgentReference, task_layout: TaskLayout) -> ResolvedAgentReference:
    """Resolve an AgentReference against a concrete task into a ResolvedAgentReference."""
    if ref.kind == "default":
        ref_dir = Path(task_layout.reference_dir)
        seed = (ref_dir / Names.REFERENCE_AGENT_FILE).read_text(encoding="utf-8")
        reqs = ref_dir / Names.REQUIREMENTS_TXT
        return ResolvedAgentReference(
            inline_seed=seed,
            ref_dir=None,
            entrypoint=Names.REFERENCE_AGENT_FILE,
            requirements=reqs if reqs.is_file() else None,
        )

    if ref.kind == "file":
        assert ref.source is not None
        return ResolvedAgentReference(
            inline_seed=ref.source.read_text(encoding="utf-8"),
            ref_dir=None,
            entrypoint=ref.source.name,
            requirements=None,
        )

    # kind == "dir"
    assert ref.source is not None
    entrypoint = ref.entrypoint or Names.REFERENCE_AGENT_FILE
    if not (ref.source / entrypoint).is_file():
        raise SystemExit(f"agent_reference entrypoint '{entrypoint}' not found in {ref.source}")
    reqs = ref.source / Names.REQUIREMENTS_TXT
    return ResolvedAgentReference(
        inline_seed=None,
        ref_dir=ref.source,
        entrypoint=entrypoint,
        requirements=reqs if reqs.is_file() else None,
    )


def copy_reference_into(resolved: ResolvedAgentReference, gen_dir: str | Path) -> None:
    """Place reference helper files + requirements.txt into a generation working dir.

    For a directory reference the whole reference is copied so the generated
    ``target_agent.py`` can import its helper modules and the agent can read them with
    its tools. For default/file references only a sibling ``requirements.txt`` (if any)
    is carried in — the seed code itself reaches the agent via the prompt.
    """
    dest = Path(gen_dir)
    if resolved.ref_dir is not None:
        for entry in resolved.ref_dir.iterdir():
            if entry.is_dir():
                shutil.copytree(entry, dest / entry.name, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, dest / entry.name)
    elif resolved.requirements is not None:
        shutil.copy2(resolved.requirements, dest / Names.REQUIREMENTS_TXT)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/api_keys.py =====

"""Model-name → provider API key resolution."""

from __future__ import annotations

import os


def resolve_api_key(model_name: str) -> str | None:
    """Return the provider-specific API key for ``model_name`` from the environment.

    Precedence (matches the original run_agent_openhands logic):
      - claude / anthropic → ANTHROPIC_API_KEY
      - gemini / google    → GOOGLE_API_KEY or GEMINI_API_KEY
      - gpt / openai       → OPENAI_API_KEY
      - anything else      → LLM_API_KEY

    Returns None when the matched variable is unset (the caller may then fall back).
    """
    name = model_name.lower()
    if "claude" in name or "anthropic" in name:
        return os.getenv("ANTHROPIC_API_KEY")
    if "gemini" in name or "google" in name:
        return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if "gpt" in name or "openai" in name:
        return os.getenv("OPENAI_API_KEY")
    return os.getenv("LLM_API_KEY")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/cli.py =====

"""Command-line argument parsing and resolution for the SIA orchestrator.

Extracted from orchestrator.main() so the parser and the arg→params resolution
can be tested independently. main() remains the entry point and dispatches on the
sub-command (``run`` / ``web``).

Sub-commands:
    sia run [flags]   Run the orchestrator (agent evolution). This is the default
                      when no sub-command is given, so ``sia --task gpqa`` still
                      works. A live dashboard is started in a background thread
                      unless ``--no-web`` is passed.
    sia web [flags]   Serve the runs visualizer over HTTP.

Agent configuration is selected via JSON *profiles* (see sia/profiles.py): the
meta/feedback agent via ``--meta-agent-profile`` and the target agent via
``--target-agent-profile``. Each value is a bundled/user profile name or a path to a
``.json`` file.
"""

from __future__ import annotations

import argparse

from sia.config import Config
from sia.layout import BUNDLED_TASKS, Names
from sia.logging_setup import get_logger

logger = get_logger(__name__)

_SUBCOMMANDS = ("run", "web")


def _add_run_args(parser: argparse.ArgumentParser, env_config: Config) -> None:
    """Attach orchestrator (agent-evolution) arguments to ``parser``."""
    parser.add_argument(
        "--max_gen",
        type=int,
        default=env_config.DEFAULT_MAX_GENERATIONS,
        help="Maximum number of generations to run (default: 3)",
    )
    parser.add_argument("--run_id", type=int, default=1, help="Run ID for this experiment (default: 1)")
    task_group = parser.add_mutually_exclusive_group(required=True)
    task_group.add_argument(
        "--task",
        type=str,
        choices=BUNDLED_TASKS,
        help=f"Name of a bundled task shipped with sia-agent ({', '.join(BUNDLED_TASKS)})",
    )
    task_group.add_argument(
        "--task_dir",
        type=str,
        help="Path to an external task directory (e.g., ./tasks/my-task)",
    )
    parser.add_argument(
        "--meta-agent-profile",
        dest="meta_agent_profile",
        type=str,
        default=env_config.DEFAULT_META_AGENT_PROFILE,
        help=(
            "Agent profile for the meta/feedback agent: a bundled/user profile name or a path "
            f"to a .json file (default: {env_config.DEFAULT_META_AGENT_PROFILE}). A profile bundles "
            "agent_impl + model + provider."
        ),
    )
    parser.add_argument(
        "--target-agent-profile",
        dest="target_agent_profile",
        type=str,
        default=env_config.DEFAULT_TARGET_AGENT_PROFILE,
        help=(
            "Agent profile for the target agent: a bundled/user profile name or a path to a "
            f".json file (default: {env_config.DEFAULT_TARGET_AGENT_PROFILE}). The model + provider "
            "the generated target_agent.py will call, plus its agent_reference (seed code)."
        ),
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        default=env_config.SANDBOX_MODE,
        choices=["none", "docker"],
        help="Sandbox mode for target agent execution: none (default) or docker (requires Docker)",
    )
    parser.add_argument(
        "--focus",
        type=str,
        default="harness",
        choices=["harness", "weights"],
        help="Focus of improvement: 'harness' (default) for code/prompt changes or 'weights' for RL-based weight tuning",
    )
    parser.add_argument(
        "--training_sandbox",
        dest="training_sandbox",
        type=str,
        default="modal",
        choices=["modal", "sandboxfusion"],
        help="Sandbox for train.py code execution in weights mode (default: modal). Use 'sandboxfusion' for SandboxFusion service.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO, or the $SIA_LOG_LEVEL env var).",
    )
    # Live dashboard controls (the web server auto-started during a run).
    parser.add_argument(
        "--no-web",
        dest="no_web",
        action="store_true",
        help="Do not start the live visualizer dashboard during the run.",
    )
    parser.add_argument(
        "--web-port",
        dest="web_port",
        type=int,
        default=8000,
        help="Port for the live dashboard started during the run (default: 8000).",
    )
    parser.add_argument(
        "--web-host",
        dest="web_host",
        type=str,
        default="127.0.0.1",
        help="Host for the live dashboard (default: 127.0.0.1).",
    )


def _add_web_args(parser: argparse.ArgumentParser, env_config: Config) -> None:
    """Attach visualizer (``sia web``) arguments to ``parser``."""
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000).")
    parser.add_argument(
        "--runs-dir",
        dest="runs_dir",
        type=str,
        default=Names.RUNS_ROOT,
        help=f"Directory of runs to visualize (default: {Names.RUNS_ROOT}).",
    )
    parser.add_argument(
        "--no-browser",
        dest="no_browser",
        action="store_true",
        help="Do not open a browser window automatically.",
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: INFO, or the $SIA_LOG_LEVEL env var).",
    )


def build_parser(env_config: Config) -> argparse.ArgumentParser:
    """Build the top-level ``sia`` parser with ``run`` / ``web`` sub-commands."""
    parser = argparse.ArgumentParser(prog="sia", description="SIA: Self-Improving AI framework")
    sub = parser.add_subparsers(dest="command", metavar="{run,web}")

    run_parser = sub.add_parser("run", help="Run the orchestrator (agent evolution).")
    _add_run_args(run_parser, env_config)

    web_parser = sub.add_parser("web", help="Serve the runs visualizer over HTTP.")
    _add_web_args(web_parser, env_config)

    return parser


def parse_args(env_config: Config, argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments, defaulting to the ``run`` sub-command.

    For backward compatibility ``sia --task gpqa`` (no sub-command) is treated as
    ``sia run --task gpqa``; ``sia web ...`` opts into the visualizer.
    """
    import sys

    raw = sys.argv[1:] if argv is None else argv
    # Insert the default sub-command unless the user asked for one (or for help).
    if not raw or (raw[0] not in _SUBCOMMANDS and raw[0] not in ("-h", "--help")):


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/config.py =====

"""Centralized configuration for SIA framework."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Config:
    """Single source of truth for all SIA configuration defaults."""

    # Agent profile defaults (JSON profiles selected on the CLI, see sia/defaults/profiles/)
    DEFAULT_META_AGENT_PROFILE: str = "default-meta"
    DEFAULT_TARGET_AGENT_PROFILE: str = "default-target"

    # Model defaults (fallbacks for context metadata / env overrides)
    DEFAULT_CLAUDE_META_MODEL: str = "haiku"
    DEFAULT_OPENHANDS_META_MODEL: str = "gemini/gemini-3.1-pro-preview"
    DEFAULT_TASK_MODEL: str = "claude-haiku-4-5-20251001"

    # Generation defaults
    DEFAULT_MAX_GENERATIONS: int = 3
    DEFAULT_RUN_ID: int = 1

    # Agent execution
    DEFAULT_MAX_TURNS: int = 20
    CONTEXT_SUMMARY_MAX_TURNS: int = 5
    DEFAULT_AGENT_IMPL: str = "claude"

    # Truncation limits
    AGENT_CODE_PREVIEW_LIMIT: int = 3000
    TRAJECTORY_PREVIEW_LIMIT: int = 1000
    TOOL_RESULT_PREVIEW_LIMIT: int = 500
    INSIGHT_PREVIEW_LIMIT: int = 200

    # Timeouts
    SHELL_TIMEOUT: int = 30
    EVAL_TIMEOUT: int = 600

    # Sandbox settings
    SANDBOX_MODE: str = "none"  # "none" or "docker"
    DOCKER_IMAGE: str = "python:3.11-slim"
    DOCKER_MEMORY_LIMIT: str = "2g"
    DOCKER_CPU_LIMIT: float = 2.0
    DOCKER_TIMEOUT: int = 3600  # seconds

    # File size limits (bytes)
    MAX_CONTEXT_FILE_SIZE: int = 10_000_000  # 10 MB
    MAX_EXECUTION_LOG_SIZE: int = 50_000_000  # 50 MB

    # Virtual environment packages.
    VENV_PACKAGES: ClassVar[list[str]] = [
        "anthropic",
        "openai",
        "python-dotenv",
        "google-genai",
        "claude-agent-sdk",
        "tqdm",
        "pydantic",
        "scikit-learn",
        "pandas",
        "numpy",
    ]

    # Additional packages only for weights mode (RL training)
    WEIGHTS_VENV_PACKAGES: ClassVar[list[str]] = [
        "vllm",
        "tinker",
        "tinker-cookbook[modal] @ git+https://github.com/thinking-machines-lab/tinker-cookbook.git@nightly",
    ]

    @classmethod
    def from_env(cls) -> Config:
        """Create Config with overrides from SIA_* environment variables."""
        cfg = cls()
        env_map = {
            "SIA_META_AGENT_PROFILE": ("DEFAULT_META_AGENT_PROFILE", str),
            "SIA_TARGET_AGENT_PROFILE": ("DEFAULT_TARGET_AGENT_PROFILE", str),
            "SIA_META_MODEL": ("DEFAULT_CLAUDE_META_MODEL", str),
            "SIA_TASK_MODEL": ("DEFAULT_TASK_MODEL", str),
            "SIA_MAX_GENERATIONS": ("DEFAULT_MAX_GENERATIONS", int),
            "SIA_AGENT_IMPL": ("DEFAULT_AGENT_IMPL", str),
            "SIA_MAX_TURNS": ("DEFAULT_MAX_TURNS", int),
            "SIA_SANDBOX_MODE": ("SANDBOX_MODE", str),
        }
        for env_var, (attr, converter) in env_map.items():
            val = os.environ.get(env_var)
            if val is not None:
                with contextlib.suppress(ValueError, TypeError):
                    setattr(cfg, attr, converter(val))
        return cfg


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/config_files.py =====

"""Name-or-path resolution for JSON config files (providers and profiles).

A config value is either a filesystem **path** (contains a path separator or ends in
``.json``) or a bare **name** that resolves, in order, against the user directory
(``$SIA_<KIND>S_DIR`` else ``./<kind>s``) and then the bundled defaults shipped inside
the wheel (``sia/defaults/<kind>s/*.json``). Used by both ``sia.providers`` and
``sia.profiles`` so the lookup rules stay identical.
"""

from __future__ import annotations

import os
from importlib.resources import files as resource_files
from pathlib import Path


def _looks_like_path(value: str) -> bool:
    """True when ``value`` should be treated as a filesystem path, not a bare name."""
    return value.endswith(".json") or "/" in value or os.sep in value


def user_dir(env_var: str, default_subdir: str) -> Path:
    """User config directory: ``$<env_var>`` if set, else ``./<default_subdir>``."""
    return Path(os.environ.get(env_var, default_subdir))


def read_config_text(name_or_path: str, *, env_var: str, subdir: str, kind: str) -> tuple[str, str]:
    """Resolve ``name_or_path`` to (file_text, source_label) for a config of ``kind``.

    Raises SystemExit with the list of available names when a bare name can't be found.
    """
    if _looks_like_path(name_or_path):
        path = Path(name_or_path)
        if not path.is_file():
            raise SystemExit(f"{kind} file not found: {name_or_path}")
        return path.read_text(encoding="utf-8"), str(path)

    filename = f"{name_or_path}.json"

    candidate = user_dir(env_var, subdir) / filename
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8"), str(candidate)

    bundled = resource_files("sia").joinpath("defaults", subdir, filename)
    if bundled.is_file():
        return bundled.read_text(encoding="utf-8"), f"<bundled>/defaults/{subdir}/{filename}"

    available = ", ".join(available_names(env_var=env_var, subdir=subdir)) or "(none)"
    raise SystemExit(f"Unknown {kind} '{name_or_path}'. Available: {available} (or pass a path to a .json file).")


def available_names(*, env_var: str, subdir: str) -> list[str]:
    """Sorted union of config names from the bundled defaults and the user directory."""
    names: set[str] = set()

    bundled = resource_files("sia").joinpath("defaults", subdir)
    if bundled.is_dir():
        names |= {entry.name[:-5] for entry in bundled.iterdir() if entry.name.endswith(".json")}

    udir = user_dir(env_var, subdir)
    if udir.is_dir():
        names |= {entry.name[:-5] for entry in udir.iterdir() if entry.name.endswith(".json")}

    return sorted(names)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/context_manager.py =====

"""
Context Manager for SIA (Self-Improving Agent) System

Manages the context.md file that tracks the evolution of agent generations,
including code changes, performance metrics, and insights across iterations.
"""

import asyncio
import os
import re
import tempfile
from datetime import datetime
from typing import Any

from sia.config import Config
from sia.io_utils import safe_load_json as _safe_load_json
from sia.io_utils import safe_read_file as _safe_read_file
from sia.logging_setup import get_logger

logger = get_logger(__name__)


class ContextManager:
    """Manages context.md for tracking generation evolution in a run"""

    def __init__(self, run_directory: str, run_config: dict[str, Any], config: Config | None = None):
        """
        Initialize the context manager.

        Args:
            run_directory: Path to the run directory (e.g., runs/run_1)
            run_config: Configuration dict with keys:
                - task_dir: Task directory path
                - meta_model: Meta-agent model name
                - task_model: Task-agent model name
                - agent_impl: Agent impl for the meta/feedback agent ('claude' / 'openhands' / ...)
                - max_gen: Maximum number of generations
            config: Optional Config instance for tunables (defaults to Config()).
        """
        self.run_dir = run_directory
        self.context_path = os.path.join(run_directory, "context.md")
        self.config = run_config
        self.cfg = config or Config()
        self.generations = []
        self.meta_model = run_config.get("meta_model", self.cfg.DEFAULT_CLAUDE_META_MODEL)
        self.agent_impl = run_config.get("agent_impl", self.cfg.DEFAULT_AGENT_IMPL)

    def initialize(self):
        """Create context.md with header information"""
        header = f"""# Run Context: {os.path.basename(self.run_dir)}

**Task**: {self.config.get("task_dir", "N/A")}
**Meta Model**: {self.config.get("meta_model", "N/A")}
**Task Model**: {self.config.get("task_model", "N/A")}
**Agent impl**: {self.config.get("agent_impl", "N/A")}
**Started**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Max Generations**: {self.config.get("max_gen", "N/A")}

---

"""
        with open(self.context_path, "w", encoding="utf-8") as f:
            f.write(header)
        logger.info(f"Initialized context.md at {self.context_path}")

    def _generate_llm_summary(self, gen_num: int, gen_data: dict[str, Any], metrics: dict[str, Any]) -> str | None:
        """
        Call LLM to generate a summary of changes and improvements.

        Args:
            gen_num: Generation number
            gen_data: Generation data dictionary
            metrics: Extracted metrics for this generation

        Returns:
            Summary string or None if generation 1 or error
        """
        # Skip for generation 1 (no previous generation to compare)
        if gen_num == 1:
            return None

        try:
            # Read current generation's target_agent.py
            current_agent_path = gen_data["agent_path"]
            current_agent_code = _safe_read_file(current_agent_path)
            if current_agent_code is None:
                logger.warning(f"Could not read current agent code for gen {gen_num}, skipping LLM summary")
                return None

            # Read previous generation's target_agent.py
            prev_gen_dir = os.path.join(self.run_dir, f"gen_{gen_num - 1}")
            prev_agent_path = os.path.join(prev_gen_dir, "target_agent.py")
            prev_agent_code = _safe_read_file(prev_agent_path)
            if prev_agent_code is None:
                if not os.path.exists(prev_agent_path):
                    prev_agent_code = "Not available"
                else:
                    logger.warning(f"Could not read previous agent code for gen {gen_num - 1}")
                    prev_agent_code = "Not available (file too large or unreadable)"

            # Read improvement.md from current generation
            improvement_path = gen_data.get("improvement_path")
            improvement_content = ""
            if improvement_path and os.path.exists(improvement_path):
                improvement_content = _safe_read_file(improvement_path) or ""

            # Get previous generation's metrics
            prev_metrics = self.generations[-1]["metrics"] if self.generations else {}

            # Format metrics comparison
            metrics_comparison = self._format_metrics_comparison(prev_metrics, metrics)

            # Create prompt for LLM
            prompt = f"""You are analyzing the evolution of an AI agent across generations.

**TASK**: Provide a concise summary (2-4 sentences) of what changed between Generation {gen_num - 1} and Generation {gen_num}, focusing on:
1. Key code/structural changes made
2. The reasoning behind these changes (from improvement.md)
3. Impact on performance metrics (if any)

**IMPROVEMENT PLAN** (improvement.md from gen_{gen_num}):
```
{improvement_content if improvement_content else "No improvement.md found"}
```

**PREVIOUS AGENT CODE** (gen_{gen_num - 1}/target_agent.py):
```python
{prev_agent_code[: self.cfg.AGENT_CODE_PREVIEW_LIMIT]}{"..." if len(prev_agent_code) > self.cfg.AGENT_CODE_PREVIEW_LIMIT else ""}
```

**CURRENT AGENT CODE** (gen_{gen_num}/target_agent.py):
```python
{current_agent_code[: self.cfg.AGENT_CODE_PREVIEW_LIMIT]}{"..." if len(current_agent_code) > self.cfg.AGENT_CODE_PREVIEW_LIMIT else ""}
```

**METRICS COMPARISON**:
{metrics_comparison}

**YOUR SUMMARY** (2-4 sentences, be specific about what changed and why):
"""

            # Create a temporary directory for LLM execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Import run_agent here to avoid circular imports
                from sia.util import run_agent

                # Run the LLM to generate summary
                async def get_summary():
                    # We'll capture the output by writing to a file
                    summary_file = os.path.join(temp_dir, "summary.txt")

                    # Modify prompt to ask LLM to write summary to file
                    file_prompt = prompt + f"\n\nWrite your 2-4 sentence summary to the file: {summary_file}"

                    await run_agent(
                        model_name=self.meta_model,
                        max_turns=str(self.cfg.CONTEXT_SUMMARY_MAX_TURNS),
                        prompt=file_prompt,
                        agent_working_directory=temp_dir,
                        agent_impl=self.agent_impl,
                    )

                    # Read the summary from file
                    if os.path.exists(summary_file):
                        summary_text = _safe_read_file(summary_file)
                        return summary_text.strip() if summary_text else None
                    return None

                # Run async function
                summary = asyncio.run(get_summary())

                if summary:
                    logger.info(f"Generated LLM summary for Generation {gen_num}")
                    return summary
                else:
                    logger.warning(f"Could not generate LLM summary for Generation {gen_num}")
                    return None

        except (OSError, RuntimeError) as e:
            logger.warning(f"Error generating LLM summary: {e}")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/io_utils.py =====

"""Shared, safe filesystem helpers.

Canonical home for the size-limited read/JSON helpers that were previously defined
in context_manager.py and re-implemented ad hoc inside orchestrator.py. Keeping a
single implementation removes that duplication (DRY) and gives one place to test
the size-limit and error-handling behavior.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from sia.config import Config
from sia.logging_setup import get_logger

logger = get_logger(__name__)

# Default size cap, evaluated once at import.
_DEFAULT_MAX_BYTES = Config().MAX_CONTEXT_FILE_SIZE


def file_size_ok(path: str | Path, max_bytes: int) -> tuple[bool, int]:
    """Return ``(within_limit, size_bytes)`` for ``path``.

    Centralizes the ``os.path.getsize`` + ``<=`` comparison used across the codebase.
    A file whose size equals ``max_bytes`` is within the limit (matches prior ``>`` checks).
    """
    size = os.path.getsize(path)
    return size <= max_bytes, size


def safe_read_file(path: str | Path, max_bytes: int = _DEFAULT_MAX_BYTES) -> str | None:
    """Read a file as UTF-8 text, returning None if it exceeds ``max_bytes`` or can't be read."""
    try:
        within_limit, size = file_size_ok(path, max_bytes)
        if not within_limit:
            logger.warning(f"File too large ({size:,} bytes > {max_bytes:,}): {path}")
            return None
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        logger.warning(f"Could not read file: {path}: {e}")
        return None


def safe_load_json(path: str | Path, max_bytes: int = _DEFAULT_MAX_BYTES) -> dict | list | None:
    """Load JSON from a file, returning None if it exceeds ``max_bytes`` or can't be parsed."""
    try:
        within_limit, size = file_size_ok(path, max_bytes)
        if not within_limit:
            logger.warning(f"JSON file too large ({size:,} bytes > {max_bytes:,}): {path}")
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not load JSON: {path}: {e}")
        return None


def write_text(path: str | Path, content: str) -> None:
    """Write UTF-8 text to ``path`` (single spelling of the common idiom)."""
    Path(path).write_text(content, encoding="utf-8")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/layout.py =====

"""Filesystem layout: path/filename constants and run/task path builders.

Single source of truth for the path and filename literals that were previously
scattered across orchestrator.py and context_manager.py. Path-building methods
return ``str`` (not ``Path``) to match the existing ``os.path``-based call sites,
keeping behavior byte-identical.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.resources import files as resource_files
from pathlib import Path

# Tasks that ship inside the wheel via package-data (sia/tasks/<name>/...).
BUNDLED_TASKS = ("gpqa", "lawbench", "longcot-chess", "spaceship-titanic")


class Names:
    """Every filename / relative-path literal used by a run or a task."""

    # Run / generation artifacts
    TARGET_AGENT = "target_agent.py"
    TRAIN_SCRIPT = "train.py"
    AGENT_EXECUTION_JSON = "agent_execution.json"
    AGENT_EXECUTION_DIR = "agent_execution"
    EXECUTION_GLOB = "execution_q*.json"
    STDOUT_LOG = "target_agent_stdout.log"
    TRAIN_STDOUT_LOG = "train_stdout.log"
    EVAL_LOG = "evaluation.log"
    RESULTS_JSON = "results.json"
    CONTEXT_MD = "context.md"
    IMPROVEMENT_MD = "improvement.md"
    META_PROMPT = "meta_agent_prompt.txt"
    FEEDBACK_PROMPT = "feedback_agent_prompt.txt"
    REQUIREMENTS_TXT = "requirements.txt"
    VENV_DIR = "venv"
    RUNS_ROOT = "./runs"

    # Task inputs
    DATA_PUBLIC = "data/public"
    TASK_MD = "data/public/task.md"
    EVALUATE_PY = "evaluate.py"
    SHARED_SAMPLE_EXECUTION = "sample_agent_execution.json"
    REFERENCE_DIR = "reference"
    REFERENCE_AGENT_FILE = "reference_target_agent.py"
    SAMPLE_TASK_DESCRIPTIONS = f"{REFERENCE_DIR}/SAMPLE_TASK_DESCRIPTIONS.md"
    REFERENCE_AGENT = f"{REFERENCE_DIR}/{REFERENCE_AGENT_FILE}"
    SHARED_DIR = "_shared"


def venv_python_path(venv_dir: str) -> str:
    """Path to the python executable inside a venv."""
    return os.path.join(venv_dir, "bin", "python")


def venv_pip_path(venv_dir: str) -> str:
    """Path to the pip executable inside a venv."""
    return os.path.join(venv_dir, "bin", "pip")


def find_evaluate_script(task_dir: str) -> str | None:
    """Locate evaluate.py: prefer data/public/evaluate.py, then task_dir/evaluate.py, else None."""
    candidate = os.path.join(task_dir, Names.DATA_PUBLIC, Names.EVALUATE_PY)
    if os.path.exists(candidate):
        return candidate
    candidate = os.path.join(task_dir, Names.EVALUATE_PY)
    if os.path.exists(candidate):
        return candidate
    return None


def resolve_task_dir(task: str | None, task_dir: str | None) -> tuple[str, str]:
    """Resolve --task / --task_dir to a (task_dir, shared_dir) pair of real paths.

    - --task <name>  → bundled sia/tasks/<name>/, shared_dir = bundled sia/tasks/_shared/
    - --task_dir P   → P, shared_dir = P/../_shared/ if present else bundled _shared/
    """
    bundled_root = Path(str(resource_files("sia.tasks")))
    bundled_shared = bundled_root / Names.SHARED_DIR

    if task:
        resolved = bundled_root / task
        if not resolved.is_dir():
            available = ", ".join(BUNDLED_TASKS)
            raise SystemExit(f"Bundled task '{task}' not found. Available: {available}")
        return str(resolved), str(bundled_shared)

    if task_dir:
        resolved = Path(task_dir).resolve()
        if not resolved.is_dir():
            raise SystemExit(f"Task directory does not exist: {task_dir}")
        external_shared = resolved.parent / Names.SHARED_DIR
        shared = external_shared if external_shared.is_dir() else bundled_shared
        return str(resolved), str(shared)

    raise SystemExit("Either --task or --task_dir must be provided")


@dataclass(frozen=True)
class RunLayout:
    """Paths under a run directory (e.g. ``./runs/run_1``)."""

    run_dir: str

    @classmethod
    def for_run_id(cls, run_id: int, runs_root: str = Names.RUNS_ROOT) -> RunLayout:
        return cls(f"{runs_root}/run_{run_id}")

    # Generation directories: gen_dir returns an absolute path, gen_dir_rel a relative one.
    def gen_dir(self, n: int) -> str:
        return os.path.abspath(f"{self.run_dir}/gen_{n}")

    def gen_dir_rel(self, n: int) -> str:
        return os.path.join(self.run_dir, f"gen_{n}")

    @property
    def venv_dir(self) -> str:
        return os.path.join(self.run_dir, Names.VENV_DIR)

    @property
    def venv_python(self) -> str:
        return venv_python_path(self.venv_dir)

    @property
    def context_md(self) -> str:
        return os.path.join(self.run_dir, Names.CONTEXT_MD)

    def target_agent(self, n: int) -> str:
        return os.path.join(self.gen_dir(n), Names.TARGET_AGENT)

    def stdout_log(self, n: int, focus: str = "harness") -> str:
        """Return stdout log path based on improvement focus mode.

        Args:
            n: Generation number
            focus: "harness" (code/prompt improvements) or "weights" (RL-based tuning)
        """
        log_name = Names.TRAIN_STDOUT_LOG if focus == "weights" else Names.STDOUT_LOG
        return os.path.join(self.gen_dir(n), log_name)

    def improvement_md(self, n: int) -> str:
        return os.path.join(self.gen_dir(n), Names.IMPROVEMENT_MD)

    def agent_execution_dir(self, n: int) -> str:
        return os.path.join(self.gen_dir(n), Names.AGENT_EXECUTION_DIR)

    def meta_prompt(self, n: int) -> str:
        return os.path.join(self.gen_dir(n), Names.META_PROMPT)


@dataclass(frozen=True)
class TaskLayout:
    """Paths for a resolved task directory and its shared directory."""

    task_dir: str
    shared_dir: str

    @property
    def dataset_dir(self) -> str:
        return os.path.join(self.task_dir, Names.DATA_PUBLIC)

    @property
    def abs_dataset_dir(self) -> str:
        return os.path.abspath(self.dataset_dir)

    @property
    def task_md(self) -> str:
        return os.path.join(self.task_dir, Names.TASK_MD)

    @property
    def sample_descriptions(self) -> str:
        return os.path.join(self.task_dir, Names.SAMPLE_TASK_DESCRIPTIONS)

    @property
    def reference_dir(self) -> str:
        return os.path.join(self.task_dir, Names.REFERENCE_DIR)

    @property


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/logging_setup.py =====

"""Centralized logging configuration for SIA.

Replaces the duplicated ``logging.basicConfig(...)`` blocks that previously lived
in both orchestrator.py and util.py. Configuration is idempotent and uses the same
format/datefmt as before, so log output is unchanged.
"""

from __future__ import annotations

import logging
import os

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_ENV_VAR = "SIA_LOG_LEVEL"
_configured = False


def _resolve_level(level: int | str | None) -> int:
    """Resolve a level from an explicit value, then ``$SIA_LOG_LEVEL``, then INFO.

    Accepts a logging int, a level name ("DEBUG"), or a numeric string ("10").
    Unrecognized values fall back to INFO.
    """
    if level is None:
        level = os.environ.get(_ENV_VAR, "").strip() or None
    if level is None:
        return logging.INFO
    if isinstance(level, int):
        return level
    name = level.upper()
    if name.isdigit():
        return int(name)
    return logging.getLevelNamesMapping().get(name, logging.INFO)


def configure_logging(level: int | str | None = None) -> None:
    """Configure root logging.

    On the first call this installs the handler/format. The level is taken from
    ``level`` if given, else from ``$SIA_LOG_LEVEL``, else INFO. A later call with
    an explicit ``level`` (e.g. a CLI flag parsed after import) updates the root
    level; otherwise subsequent calls are no-ops.
    """
    global _configured
    resolved = _resolve_level(level)
    if _configured:
        if level is not None:
            logging.getLogger().setLevel(resolved)
        return
    logging.basicConfig(level=resolved, format=_LOG_FORMAT, datefmt=_DATE_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger, ensuring logging is configured first."""
    configure_logging()
    return logging.getLogger(name)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/orchestrator.py =====

"""
Directory structure (conceptual)

orchestration/
  orchestrator.py

tasks/
  task_1/
    reference/
      reference_target_agent.py
      SAMPLE_TASK_DESCRIPTIONS.md
    data/
      public/
        train.csv
        test.csv
        task.md
      private/
  task_2/
    reference/
      reference_target_agent.py
      SAMPLE_TASK_DESCRIPTIONS.md
    data/
      public/
        task.md
      private/

tasks/_shared/                 # cross-task examples/templates (public)
  sample_agent_execution.json

runs/
  run_1/ (unique meta_agent, unique feedback_agent, unique_task, reference_target_agent, config)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
  run_2/ (unique meta_agent, unique feedback_agent, unique_task, reference_target_agent, config)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
  run_3/ (unique meta_agent, unique feedback_agent, unique_task, reference_target_agent, config)
    gen_1: (meta_agent, reference_target_agent) -> target_agent_1 -> gen_1
    gen_2: (feedback_agent, target_agent_1) -> target_agent_2 -> gen_2
    gen_3: (feedback_agent, target_agent_2) -> target_agent_3 -> gen_3
"""

import asyncio
import glob
import json
import os
import subprocess
import time
import traceback
from datetime import datetime
from pathlib import Path

from sia import __version__, cli
from sia.agent_reference import ResolvedAgentReference, copy_reference_into, resolve_agent_reference
from sia.config import Config
from sia.io_utils import file_size_ok, write_text
from sia.layout import BUNDLED_TASKS, Names, RunLayout, TaskLayout, resolve_task_dir, venv_python_path
from sia.logging_setup import configure_logging, get_logger
from sia.profiles import MetaAgentProfile, load_meta_agent_profile, load_target_agent_profile
from sia.prompts import build_feedback_prompt, build_meta_prompt
from sia.providers import Provider
from sia.results import FeedbackContext, TargetAgentResult
from sia.run_setup import RunSetup, TaskFiles, install_requirements, load_task_files, setup_run_directory
from sia.util import run_agent

__all__ = [
    "BUNDLED_TASKS",
    "RunSetup",
    "TaskFiles",
    "build_feedback_prompt",
    "build_meta_prompt",
    "load_agent_execution",
    "load_task_files",
    "main",
    "resolve_task_dir",
    "run_evaluation",
    "run_generation",
    "setup_run_directory",
]

logger = get_logger(__name__)


# ========================
# HELPER FUNCTIONS
# ========================


def load_agent_execution(gen_directory, config: Config | None = None):
    """
    Load execution logs with automatic format detection.

    Supports two formats:
    1. Single-file: gen_X/agent_execution.json (backwards compatible)
    2. Multi-trajectory: gen_X/agent_execution/execution_q0.json, execution_q1.json, ...

    Args:
        gen_directory: Path to the generation directory
        config: Optional Config instance (defaults to Config()).

    Returns:
        tuple: (execution_data, is_multi_trajectory)
            - execution_data: dict or list containing execution log(s)
            - is_multi_trajectory: bool indicating if multi-trajectory format
    """
    cfg = config or Config()
    execution_folder = os.path.join(gen_directory, Names.AGENT_EXECUTION_DIR)
    execution_file = os.path.join(gen_directory, Names.AGENT_EXECUTION_JSON)

    # Multi-trajectory folder: one file per question
    if os.path.isdir(execution_folder):
        logger.info("  → Detected multi-trajectory format (folder)")

        files = sorted(glob.glob(os.path.join(execution_folder, Names.EXECUTION_GLOB)))

        if not files:
            logger.warning("  ✗ agent_execution/ folder exists but is empty")
            return {"error": "Empty execution folder", "type": "multi-trajectory"}, True

        # Load all trajectory files
        trajectories = []
        for f in files:
            try:
                within_limit, file_size = file_size_ok(f, cfg.MAX_EXECUTION_LOG_SIZE)
                if not within_limit:
                    logger.warning(f"Skipping oversized trajectory ({file_size:,} bytes): {os.path.basename(f)}")
                    trajectories.append({"error": "File too large", "file": os.path.basename(f), "size": file_size})
                    continue
                with open(f, encoding="utf-8") as fp:
                    trajectories.append(json.load(fp))
            except json.JSONDecodeError as e:
                logger.warning(f"  ✗ Failed to parse {os.path.basename(f)}: {e}")
                trajectories.append({"error": str(e), "file": os.path.basename(f)})
            except (OSError, KeyError) as e:
                logger.warning(f"  ✗ Error reading {os.path.basename(f)}: {e}")
                trajectories.append({"error": str(e), "file": os.path.basename(f)})

        logger.info(f"  ✓ Loaded {len(trajectories)} trajectory files")

        return {"trajectories": trajectories, "count": len(trajectories), "type": "multi-trajectory"}, True

    # Single combined execution file
    elif os.path.exists(execution_file):
        logger.info("  → Detected single-file format")

        try:
            within_limit, file_size = file_size_ok(execution_file, cfg.MAX_EXECUTION_LOG_SIZE)
            if not within_limit:
                logger.warning(f"Execution log too large ({file_size:,} bytes), skipping")
                return {"error": "File too large", "size": file_size}, False
            with open(execution_file, encoding="utf-8") as f:
                data = json.load(f)
            logger.info("  ✓ Successfully loaded agent execution log")
            return data, False

        except json.JSONDecodeError as e:
            logger.warning(f"  ✗ Failed to parse agent_execution.json: {e}")
            logger.warning("  → The target agent may have crashed or failed to complete")

            # Return partial data for debugging
            try:
                with open(execution_file, encoding="utf-8") as f:
                    raw = f.read()
                return {
                    "error": "Parse error",
                    "raw_preview": raw[:1000],
                    "parse_error": str(e),
                    "file_size": len(raw),
                }, False
            except OSError as read_error:
                return {"error": "Could not read file", "read_error": str(read_error)}, False

        except FileNotFoundError:
            logger.error("  ✗ agent_execution.json not found")
            return {"error": "Execution log file not found"}, False

    # Neither exists
    else:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/prepare_mlebench_dataset.py =====

#!/usr/bin/env python3
"""
Script to prepare a task dataset from MLE-Bench competitions.

This script:
1. Runs mlebench prepare command on a competition
2. Copies public and private data to tasks/competition-id/data/
3. Renames description.md to task.md in data/public/
4. Generates similar tasks using Gemini API (optional)
5. Creates SAMPLE_TASK_DESCRIPTIONS.md in reference/
6. Copies reference_target_agent.py from _shared/ to reference/
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

_ = load_dotenv()


def run_mlebench_prepare(competition_id: str) -> bool:
    """Run mlebench prepare command for the given competition."""
    print(f"[1/6] Running mlebench prepare for competition: {competition_id}")
    try:
        result = subprocess.run(
            ["mlebench", "prepare", "-c", competition_id], capture_output=True, text=True, check=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running mlebench prepare: {e}", file=sys.stderr)
        print(e.stdout)
        print(e.stderr, file=sys.stderr)
        return False


def copy_dataset_files(competition_id: str, tasks_dir: Path) -> bool:
    """Copy public and private data from mlebench cache to tasks directory."""
    print(f"[2/6] Copying dataset files for {competition_id}")

    # Source directory (mlebench cache) - data is in prepared/ subdirectory
    cache_dir = Path.home() / ".cache" / "mle-bench" / "data" / competition_id
    prepared_dir = cache_dir / "prepared"

    # Destination directory
    task_dir = tasks_dir / competition_id
    data_dir = task_dir / "data"

    # Create destination directories
    data_dir.mkdir(parents=True, exist_ok=True)

    if not prepared_dir.exists():
        print(f"Error: Prepared directory not found: {prepared_dir}", file=sys.stderr)
        return False

    # Copy public directory if exists
    public_src = prepared_dir / "public"
    if public_src.exists() and any(public_src.iterdir()):
        public_dst = data_dir / "public"
        if public_dst.exists():
            shutil.rmtree(public_dst)
        shutil.copytree(public_src, public_dst)
        print(f"  ✓ Copied public data to {public_dst}")
    else:
        print(f"  ⚠ No public directory found or empty at {public_src}")

    # Copy private directory if exists
    private_src = prepared_dir / "private"
    if private_src.exists() and any(private_src.iterdir()):
        private_dst = data_dir / "private"
        if private_dst.exists():
            shutil.rmtree(private_dst)
        shutil.copytree(private_src, private_dst)
        print(f"  ✓ Copied private data to {private_dst}")
    else:
        print(f"  ⚠ No private directory found or empty at {private_src}")

    return True


def move_description_to_task(competition_id: str, tasks_dir: Path) -> bool:
    """Rename description.md to task.md in data/public."""
    print("[3/6] Renaming description.md to task.md")

    task_dir = tasks_dir / competition_id
    data_dir = task_dir / "data"
    public_dir = data_dir / "public"

    # Look for description.md in data/public (already copied from prepared/public)
    description_file = public_dir / "description.md"

    if description_file.exists():
        # Rename description.md to task.md
        task_md_public = public_dir / "task.md"
        description_file.rename(task_md_public)
        print(f"  ✓ Renamed description.md to {task_md_public}")

        return True
    else:
        print(f"  ⚠ No description.md found at {description_file}")
        return False


def get_similar_tasks_from_gemini(competition_id: str, task_description: str) -> str:
    """Use Gemini to generate similar task descriptions."""
    print("[4/6] Generating similar tasks using Gemini API")

    # Get API key from environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  ⚠ No GEMINI_API_KEY environment variable set. Skipping similar tasks generation.")
        return ""

    genai.configure(api_key=api_key)

    try:
        # Use Gemini 2.0 Flash Thinking (closest to "Gemini 3 Pro Preview")
        model = genai.GenerativeModel("gemini-3-flash-preview")

        prompt = f"""Given the following Kaggle competition task:

Competition ID: {competition_id}

Task Description:
{task_description}

Generate 3-5 DIVERSE machine learning task descriptions that cover different problem types, domains, and data modalities.

IMPORTANT: Create diversity across:
- Problem types: Classification, regression, clustering, forecasting, generation, etc.
- Data types: Tabular, text, images, time-series, graphs, etc.
- Domains: Healthcare, finance, retail, transportation, social media, etc.

FORMATTING REQUIREMENTS:
1. Match the same level of detail, structure, and writing style as the original task description
2. Each task should be a complete, standalone problem statement
3. Include all relevant sections: overview, dataset description, evaluation metrics, submission format, etc.
4. Separate each task with exactly 5 dashes: -----

EXAMPLE FORMAT:

## Task 1: [Title]

[Complete problem description matching the style and detail level of the original task]

-----

## Task 2: [Title]

[Complete problem description matching the style and detail level of the original task]

-----

[Continue for remaining tasks]

Generate tasks that will help train a generalizable AI agent capable of handling diverse machine learning problems."""

        response = model.generate_content(prompt)
        print("  ✓ Generated similar tasks from Gemini")
        return response.text

    except Exception as e:
        print(f"  ⚠ Error calling Gemini API: {e}", file=sys.stderr)
        return ""


def create_sample_task_descriptions(competition_id: str, tasks_dir: Path, similar_tasks: str) -> bool:
    """Create SAMPLE_TASK_DESCRIPTIONS.md in reference directory."""
    print("[5/6] Creating SAMPLE_TASK_DESCRIPTIONS.md")

    task_dir = tasks_dir / competition_id
    reference_dir = task_dir / "reference"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/profiles.py =====

"""Agent profiles — JSON-defined configuration for one agent role.

Two roles, two shapes:

- A **meta/feedback** agent runs *inside* SIA via a registered ``agent_impl``
  (claude / openhands / pydantic-ai) — see :class:`MetaAgentProfile`.
- The **target** agent is generated code SIA never runs as an engine; it is seeded
  from an ``agent_reference`` (the task package's bundled reference, or a user file /
  directory) and iteratively improved — see :class:`TargetAgentProfile`.

Profiles are JSON files (bundled under ``sia/defaults/profiles/`` and user-extensible
via ``$SIA_PROFILES_DIR`` or ``./profiles``). Each references a
:class:`~sia.providers.Provider` by name. Adding a profile is dropping a JSON file —
no code change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from sia.agent_impls import available_agent_impls
from sia.agent_reference import AgentReference, parse_agent_reference
from sia.config_files import available_names, read_config_text
from sia.providers import Provider, load_provider

ENV_VAR = "SIA_PROFILES_DIR"
SUBDIR = "profiles"


@dataclass(frozen=True)
class MetaAgentProfile:
    """Full configuration for the meta/feedback agent role."""

    profile_id: str  # stable identifier (also the value passed to --meta-agent-profile)
    name: str  # human-readable display name
    agent_impl: str  # a registered agent impl (claude / openhands / pydantic-ai)
    model: str
    provider: Provider


@dataclass(frozen=True)
class TargetAgentProfile:
    """Full configuration for the target agent role (generated, never run by SIA)."""

    profile_id: str  # stable identifier (also the value passed to --target-agent-profile)
    name: str  # human-readable display name
    model: str
    provider: Provider
    agent_reference: AgentReference  # where the seed code + deps come from


def available_profiles() -> list[str]:
    """Names of all profiles discoverable in the bundled + user directories."""
    return available_names(env_var=ENV_VAR, subdir=SUBDIR)


def _load_json(name_or_path: str) -> tuple[dict, str]:
    text, source = read_config_text(name_or_path, env_var=ENV_VAR, subdir=SUBDIR, kind="profile")
    try:
        return json.loads(text), source
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid profile JSON at {source}: {exc}") from exc


def _require(data: dict, keys: set[str], source: str) -> None:
    missing = keys - data.keys()
    if missing:
        raise SystemExit(f"Profile at {source} is missing required keys: {', '.join(sorted(missing))}")


def _profile_base_dir(source: str) -> str | None:
    """Directory a profile file lives in (for resolving a relative agent_reference)."""
    return None if source.startswith("<bundled>") else str(Path(source).parent)


def load_meta_agent_profile(name_or_path: str) -> MetaAgentProfile:
    """Load and validate a meta-agent profile by bundled/user name or path to a .json file."""
    data, source = _load_json(name_or_path)
    _require(data, {"profile_id", "name", "agent_impl", "model", "provider_id"}, source)

    provider = load_provider(data["provider_id"])
    profile = MetaAgentProfile(
        profile_id=data["profile_id"],
        name=data["name"],
        agent_impl=data["agent_impl"],
        model=data["model"],
        provider=provider,
    )
    _validate_meta(profile, source)
    return profile


def load_target_agent_profile(name_or_path: str) -> TargetAgentProfile:
    """Load and validate a target-agent profile by bundled/user name or path to a .json file."""
    data, source = _load_json(name_or_path)
    _require(data, {"profile_id", "name", "model", "provider_id"}, source)

    agent_reference = parse_agent_reference(data.get("agent_reference"), _profile_base_dir(source))
    return TargetAgentProfile(
        profile_id=data["profile_id"],
        name=data["name"],
        model=data["model"],
        provider=load_provider(data["provider_id"]),
        agent_reference=agent_reference,
    )


def _validate_meta(profile: MetaAgentProfile, source: str) -> None:
    """Reject incoherent agent_impl/provider combinations for the meta agent."""
    valid = available_agent_impls()
    if profile.agent_impl not in valid:
        raise SystemExit(
            f"Profile at {source} has invalid agent_impl '{profile.agent_impl}'. Expected one of: {', '.join(valid)}."
        )
    # The Claude Code SDK only talks to Anthropic; pairing it with another provider
    # would silently authenticate against the wrong endpoint.
    if profile.agent_impl == "claude" and profile.provider.client_kind != "anthropic":
        raise SystemExit(
            f"Profile at {source} pairs agent_impl 'claude' with provider "
            f"'{profile.provider.name}' (client_kind={profile.provider.client_kind}). "
            f"The claude agent impl requires an anthropic provider; use the openhands or "
            f"pydantic-ai agent impl for other providers."
        )


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/prompts.py =====

"""Prompt builders for the meta-agent and feedback-agent.

Moved verbatim out of orchestrator.py. The exact text is product-critical and is
locked by the golden-master tests in tests/test_prompts_snapshot.py.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sia.providers import Provider
    from sia.run_setup import TaskFiles


def _reference_section(task_files: TaskFiles, reference_dir: str | None) -> str:
    """The reference paragraph of the meta prompt.

    Default/single-file: embed the seed code verbatim (byte-identical to the original).
    Multi-file directory: point the agent at the on-disk reference and tell it to read
    the files itself and declare any extra deps in requirements.txt.
    """
    if reference_dir is None:
        return (
            "Here is a sample target_agent.py showing the complete implementation pattern "
            f"(READ THE ENTIRE FILE):\n{task_files.reference_target_agent_py}"
        )
    return (
        f"Your reference agent implementation has been placed in your working directory ({reference_dir}). "
        "It may span multiple files. READ IT YOURSELF with your file tools (Read/Glob/Grep) — study the "
        "entrypoint and any helper modules — then write your target_agent.py in the same directory.\n"
        "If your target_agent.py needs third-party packages, list them (one per line) in a requirements.txt "
        "in your working directory; they are installed before the target agent runs."
    )


def _build_weights_meta_prompt(
    task_files: TaskFiles,
    task_model: str,
    working_dir: str,
    training_sandbox: str = "modal",
) -> str:
    """Build the meta-agent prompt for RL-based weight tuning (train.py).

    Args:
        training_sandbox: "modal" (default) or "sandboxfusion" for code execution
    """
    # RL Integration Guide (sections 1-9)
    RL_GUIDE = """# RL Integration Guide: Custom Task Tuning with Tinker-Cookbook

This guide provides the necessary architectural context and implementation patterns to integrate a custom Agent/Task into the `tinker-cookbook` RL pipeline. Use this to build a task-specific `Env`, `EnvGroupBuilder`, and `RLDataset`.

---

## 1. Core Abstractions Mapping

| Tinker Class | Role in RL | Custom Implementation Goal |
| :--- | :--- | :--- |
| **`Env`** | The "World" | Manages a single trajectory (one agent, one problem). Handles tool-calls and intermediate rewards. |
| **`EnvGroupBuilder`** | The "Orchestrator" | Creates $N$ environments for the **same** problem. Handles final group-level rewards (GRPO). |
| **`RLDataset`** | The "Task Source" | Groups `EnvGroupBuilder` instances into batches. Feeds the training loop. |

---

## 2. Implementing the `Env`

The `Env` must manage the conversation state and define how the agent interacts with tools.

```python
from tinker_cookbook.rl.types import Env, StepResult
from tinker_cookbook.renderers import Renderer

class CustomAgentEnv(Env):
    def __init__(self, task_data, renderer: Renderer):
        self.task = task_data
        self.renderer = renderer
        self.messages = []

    async def initial_observation(self):
        self.messages = [{"role": "user", "content": self.task["query"]}]
        prompt, stop_cond = self.renderer.build_generation_prompt(self.messages)
        return prompt, stop_cond

    async def step(self, action_tokens: list[int], extra=None):
        response_text = self.renderer.tokenizer.decode(action_tokens)

        # LOGIC: Execute tools or parse final answer
        tool_result, is_done = await execute_agent_tools(response_text)

        # Step reward (e.g., formatting check)
        reward = -0.1 if "invalid_tool" in response_text else 0.0

        self.messages.append({"role": "assistant", "content": response_text})
        if tool_result:
            self.messages.append({"role": "user", "content": f"Result: {tool_result}"})

        next_obs, next_stop = self.renderer.build_generation_prompt(self.messages)
        return StepResult(
            reward=reward, episode_done=is_done,
            next_observation=next_obs, next_stop_condition=next_stop
        )
```

---

## 3. Implementing the `EnvGroupBuilder`

This class is responsible for spawning $N$ environments for a single problem and computing the final outcome.

```python
from tinker_cookbook.rl.types import EnvGroupBuilder, Trajectory
from typing import Sequence

class CustomTaskGroupBuilder(EnvGroupBuilder):
    def __init__(self, task_data, group_size: int, renderer: Renderer):
        self.task = task_data
        self.group_size = group_size
        self.renderer = renderer

    async def make_envs(self) -> Sequence[CustomAgentEnv]:
        # Return N copies of the environment for the same task
        return [CustomAgentEnv(self.task, self.renderer) for _ in range(self.group_size)]

    async def compute_group_rewards(self, trajectories: list[Trajectory], envs: Sequence[CustomAgentEnv]):
        # Called after all N rollouts finish. Use this for "Final Success" rewards.
        rewards_and_metrics = []
        for traj in trajectories:
            final_text = self.renderer.tokenizer.decode(traj.transitions[-1].ac.tokens)
            is_correct = check_success(final_text, self.task["answer"])

            # Final Reward: 1.0 for success, 0.0 for failure
            reward = 1.0 if is_correct else 0.0
            rewards_and_metrics.append((reward, {"is_correct": float(is_correct)}))

        return rewards_and_metrics
```

---

## 5. Implementing a Custom `RLDatasetBuilder`

The `RLDatasetBuilder` is the entry point for your data. It must be a `@chz.chz` dataclass.

```python
from tinker_cookbook.rl.types import RLDataset, RLDatasetBuilder
from tinker_cookbook import renderers, tokenizer_utils
import chz
import json

class CustomTaskDataset(RLDataset):
    def __init__(self, tasks, batch_size: int, group_size: int, renderer):
        self.builders = [CustomTaskGroupBuilder(t, group_size, renderer) for t in tasks]
        self.batch_size = batch_size

    def get_batch(self, index: int):
        start = index * self.batch_size
        return self.builders[start : start + self.batch_size]

    def __len__(self):
        return (len(self.builders) + self.batch_size - 1) // self.batch_size

@chz.chz
class MyDatasetBuilder(RLDatasetBuilder):
    batch_size: int
    group_size: int
    model_name: str
    renderer_name: str = "qwen3_instruct"
    data_path: str = "data.jsonl"

    async def __call__(self) -> tuple[RLDataset, RLDataset | None]:
        # 1. Load your raw data
        with open(self.data_path) as f:
            tasks = [json.loads(line) for line in f]

        # 2. Setup Renderer & Tokenizer
        tokenizer = tokenizer_utils.get_tokenizer(self.model_name)
        renderer = renderers.get_renderer(self.renderer_name, tokenizer=tokenizer)



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/providers.py =====

"""LLM provider registry — JSON-defined endpoints/credentials.

A ``Provider`` describes *how* to talk to a model provider: the SDK family
(``client_kind``), an optional OpenAI-compatible ``base_url``, and the environment
variable holding the API key. Providers are defined in JSON files (bundled under
``sia/defaults/providers/`` and user-extensible via ``$SIA_PROVIDERS_DIR`` or
``./providers``) and referenced **by name** from an agent profile (see ``sia.profiles``).

Adding a provider is dropping a JSON file — no code change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from sia.config_files import available_names, read_config_text

ENV_VAR = "SIA_PROVIDERS_DIR"
SUBDIR = "providers"

# SDK family the generated/meta agent should use to reach the model.
VALID_CLIENT_KINDS = ("anthropic", "openai", "google")


@dataclass(frozen=True)
class Provider:
    """How to reach a model provider's API."""

    provider_id: str  # stable identifier, referenced by a profile's "provider_id"
    name: str  # human-readable display name
    client_kind: str  # "anthropic" | "openai" | "google"
    base_url: str | None  # None for native endpoints; set for OpenAI-compatible providers
    api_key_env: str


def available_providers() -> list[str]:
    """Names of all providers discoverable in the bundled + user directories."""
    return available_names(env_var=ENV_VAR, subdir=SUBDIR)


def load_provider(name_or_path: str) -> Provider:
    """Load and validate a provider by bundled/user name or by path to a .json file."""
    text, source = read_config_text(name_or_path, env_var=ENV_VAR, subdir=SUBDIR, kind="provider")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid provider JSON at {source}: {exc}") from exc

    missing = {"provider_id", "name", "client_kind", "api_key_env"} - data.keys()
    if missing:
        raise SystemExit(f"Provider at {source} is missing required keys: {', '.join(sorted(missing))}")

    client_kind = data["client_kind"]
    if client_kind not in VALID_CLIENT_KINDS:
        raise SystemExit(
            f"Provider at {source} has invalid client_kind '{client_kind}'. "
            f"Expected one of: {', '.join(VALID_CLIENT_KINDS)}."
        )

    return Provider(
        provider_id=data["provider_id"],
        name=data["name"],
        client_kind=client_kind,
        base_url=data.get("base_url"),
        api_key_env=data["api_key_env"],
    )


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/results.py =====

"""Result dataclasses replacing positional tuple returns.

Internally the orchestrator builds these for clarity; at the call boundary it
still returns ``.as_tuple()`` to preserve the existing wire contract that tests
and callers depend on.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TargetAgentResult:
    """Outcome of running a target agent generation."""

    success: bool
    stdout: str
    stderr: str
    error_msg: str

    def as_tuple(self) -> tuple[bool, str, str, str]:
        return (self.success, self.stdout, self.stderr, self.error_msg)


@dataclass
class FeedbackContext:
    """The two text blocks the feedback prompt is built from."""

    execution_status: str
    execution_section: str

    def as_tuple(self) -> tuple[str, str]:
        return (self.execution_status, self.execution_section)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/run_setup.py =====

"""Run/task setup: load task reference files and create the run directory.

Hosts the TaskFiles/RunSetup containers and the filesystem-prep helpers previously
defined in orchestrator.py (re-exported there for the existing test contract).
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from sia.config import Config
from sia.context_manager import ContextManager
from sia.layout import RunLayout, TaskLayout, venv_pip_path, venv_python_path
from sia.logging_setup import get_logger

if TYPE_CHECKING:
    from sia.agent_reference import ResolvedAgentReference
    from sia.profiles import MetaAgentProfile, TargetAgentProfile

logger = get_logger(__name__)


@dataclass
class TaskFiles:
    """Container for task reference files loaded from disk."""

    sample_task_descriptions: str
    reference_target_agent_py: str
    sample_agent_execution: dict
    task_md: str


@dataclass
class RunSetup:
    """Container for run directory paths and managers."""

    run_directory: str
    meta_agent_working_directory: str
    venv_dir: str
    context_mgr: ContextManager


def load_task_files(
    task_dir: str,
    shared_dir: str,
    resolved_ref: ResolvedAgentReference | None = None,
) -> TaskFiles:
    """Load all reference files from the task directory.

    The seed shown to the meta-agent comes from ``resolved_ref`` (the target profile's
    agent_reference) when provided: its ``inline_seed`` for a default/single-file
    reference, or empty for a multi-file directory reference (the agent reads that from
    disk). When ``resolved_ref`` is None, fall back to the task's bundled reference.
    """
    logger.info("Loading files from task directory...")
    paths = TaskLayout(task_dir, shared_dir)

    sample_task_descriptions = Path(paths.sample_descriptions).read_text()
    logger.info("  ✓ Sample task descriptions loaded")

    if resolved_ref is None:
        reference_target_agent_py = Path(paths.reference_agent).read_text()
    else:
        reference_target_agent_py = resolved_ref.inline_seed or ""
    logger.info("  ✓ Reference target agent loaded")

    with open(paths.sample_execution) as f:
        sample_agent_execution = json.load(f)
    logger.info("  ✓ Sample agent execution loaded")

    task_md = Path(paths.task_md).read_text()
    logger.info("  ✓ Task specification loaded")

    return TaskFiles(
        sample_task_descriptions=sample_task_descriptions,
        reference_target_agent_py=reference_target_agent_py,
        sample_agent_execution=sample_agent_execution,
        task_md=task_md,
    )


def _create_venv(venv_dir: str, packages: list[str]) -> None:
    """Create a virtual environment and install packages."""
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", venv_dir], check=True)
        subprocess.run(
            ["uv", "pip", "install", "--python", venv_python_path(venv_dir), *packages],
            check=True,
        )
    else:
        venv.create(venv_dir, with_pip=True)
        subprocess.run([venv_pip_path(venv_dir), "install", *packages], check=True)


def install_requirements(venv_dir: str, requirements_path: str) -> None:
    """Install a requirements.txt into an existing venv (augmenting the baseline packages).

    Used per generation so the meta/feedback agents can evolve the target's
    dependencies by editing requirements.txt across generations.
    """
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--python", venv_python_path(venv_dir), "-r", requirements_path]
    else:
        cmd = [venv_pip_path(venv_dir), "install", "-r", requirements_path]
    logger.info(f"Installing generation dependencies from {requirements_path}")
    subprocess.run(cmd, check=True)


def _write_run_profiles(
    run_directory: str,
    meta_profile: MetaAgentProfile | None,
    target_profile: TargetAgentProfile | None,
) -> None:
    """Persist the resolved meta/target profiles as ``profiles.json`` in the run dir.

    Dumping the whole profile object (provider details + resolved agent_reference,
    whose ``source`` is already an absolute path) means the web visualizer renders
    full profile detail generically — no per-field plumbing, and new profile fields
    show up automatically.
    """
    profiles = {
        role: dataclasses.asdict(profile)
        for role, profile in (("meta", meta_profile), ("target", target_profile))
        if profile is not None
    }
    if not profiles:
        return
    path = os.path.join(run_directory, "profiles.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(profiles, fh, indent=2, default=str)  # default=str: Path -> string


def setup_run_directory(
    run_id: int,
    task_dir: str,
    meta_model: str,
    task_model: str,
    agent_impl: str,
    max_gen: int,
    focus: str = "harness",
    config: Config | None = None,
    meta_profile: MetaAgentProfile | None = None,
    target_profile: TargetAgentProfile | None = None,
) -> RunSetup:
    """Create run directories, venv, and context manager.

    Args:
        focus: "harness" (default) or "weights" for RL-based tuning. Determines which packages are installed.
    """
    cfg = config or Config()
    layout = RunLayout.for_run_id(run_id)
    run_directory = layout.run_dir
    meta_agent_working_directory = layout.gen_dir(1)

    if os.path.exists(run_directory):
        logger.error(f"Run directory already exists: {run_directory}")
        logger.error("Please use a different run_id or remove the existing directory")
        sys.exit(1)

    logger.info(f"Creating run directory: {run_directory}")
    os.makedirs(run_directory, exist_ok=False)

    logger.info(f"Creating meta_agent working directory: {meta_agent_working_directory}")
    os.makedirs(meta_agent_working_directory, exist_ok=False)

    venv_dir = layout.venv_dir
    logger.info(f"Creating virtual environment at: {venv_dir}")
    # Build packages list conditionally based on focus mode
    packages = cfg.VENV_PACKAGES.copy()
    if focus == "weights":
        packages.extend(cfg.WEIGHTS_VENV_PACKAGES)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/__init__.py =====

"""Bundled tasks shipped with sia-agent.

Each subdirectory is a task with the standard layout:
    data/public/    — public dataset and task.md
    data/private/   — private evaluation data
    reference/      — reference target agent and sample task descriptions
"""


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/_shared/reference_target_agent.py =====

import anthropic
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-haiku-4-5-20251001"

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "write_file",
        "description": "Write (overwrite) a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read and return the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "bash",
        "description": "Run a bash command and return stdout + stderr.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
            },
            "required": ["command"],
        },
    },
]

# ── Tool implementations ──────────────────────────────────────────────────────

def write_file(path: str, content: str) -> str:
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} characters to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except Exception as e:
        return f"Error reading file: {e}"


def bash(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def dispatch_tool(name: str, inputs: dict) -> str:
    if name == "write_file":
        return write_file(**inputs)
    elif name == "read_file":
        return read_file(**inputs)
    elif name == "bash":
        return bash(**inputs)
    else:
        return f"Unknown tool: {name}"


# ── Multi-Trajectory Logger ───────────────────────────────────────────────────

class MultiTrajectoryLogger:
    """
    Logger for tasks with multiple independent samples (e.g., GPQA with multiple questions).

    For tasks where you need to process multiple independent items (questions, test cases,
    samples), this logger saves each trajectory separately instead of one large file.

    Usage:
        logger = MultiTrajectoryLogger(working_dir)

        for idx, question in enumerate(questions):
            messages = []
            messages.append({"role": "user", "content": question_prompt})

            response = client.messages.create(...)
            messages.append({"role": "assistant", "content": response.content})

            # Save this trajectory
            logger.log_trajectory(idx, messages)

        logger.finalize(len(questions))
    """

    def __init__(self, working_dir: str):
        """
        Initialize the multi-trajectory logger.

        Args:
            working_dir: Path to the working directory where agent_execution/ will be created
        """
        import os
        self.working_dir = working_dir
        self.execution_folder = os.path.join(working_dir, "agent_execution")
        os.makedirs(self.execution_folder, exist_ok=True)
        print(f"Initialized multi-trajectory logger at: {self.execution_folder}")

    def log_trajectory(self, trajectory_id: int, messages: list):
        """
        Save a complete trajectory for one sample.

        Args:
            trajectory_id: Index of this trajectory (0-based)
            messages: List of message dicts (same format as Anthropic API messages)
        """
        import os
        filename = f"execution_q{trajectory_id}.json"
        filepath = os.path.join(self.execution_folder, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved trajectory {trajectory_id} to {filename}")
        except Exception as e:
            print(f"  ✗ Error saving trajectory {trajectory_id}: {e}")

    def finalize(self, total_count: int):
        """
        Log completion message.

        Args:
            total_count: Total number of trajectories saved
        """
        print(f"\n{'='*60}")
        print(f"✓ Multi-trajectory logging complete:")
        print(f"  - Total trajectories: {total_count}")
        print(f"  - Saved to: {self.execution_folder}/")
        print(f"  - Files: execution_q0.json to execution_q{total_count-1}.json")
        print(f"{'='*60}\n")


# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(task: str) -> None:
    print(f"\n{'='*60}")
    print(f"Task: {task}")
    print('='*60)

    messages = [{"role": "user", "content": task}]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/data/public/evaluate.py =====

#!/usr/bin/env python3
"""
Evaluate GPQA submissions from target_agent.py output.

This script:
1. Loads ground truth from data/private/diamond_questions.json (with correct answers)
2. Loads model predictions from a submission JSON file
3. Compares model answers against correct answer letters
4. Outputs accuracy metrics and per-domain breakdown

The script automatically looks for JSON files in the results/ subdirectory
if it exists within --gen-dir.

Usage:
    python evaluate.py --gen-dir path/to/generation/directory
    python evaluate.py --submission path/to/submission.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def load_ground_truth(data_path: Path) -> List[dict]:
    """Load the ground truth questions and answers."""
    if not data_path.is_file():
        raise FileNotFoundError(f"Ground truth file not found: {data_path}")

    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_correct_answers(questions: List[dict]) -> Dict[int, str]:
    """
    Build a mapping of question_id -> correct_answer_letter.

    Reads the correct_answer_letter field from the private dataset.
    """
    correct_answers = {}

    for item in questions:
        question_id = item.get("id")
        if question_id is None:
            continue

        # The private dataset already has the correct_answer_letter field
        correct_ltr = item.get("correct_answer_letter")
        if correct_ltr:
            correct_answers[question_id] = correct_ltr

    return correct_answers


def load_submission(submission_path: Path) -> Dict:
    """Load a submission JSON file."""
    if not submission_path.is_file():
        raise FileNotFoundError(f"Submission file not found: {submission_path}")

    with open(submission_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_submission_file(gen_dir: Path) -> Optional[Path]:
    """
    Find a submission JSON file in the generation directory.

    Search order:
    1. Check for results/ subdirectory and look for JSON files there
    2. Look for common patterns in gen_dir itself (results*.json, submission*.json, etc.)
    3. If only one JSON file exists, use that
    """
    if not gen_dir.is_dir():
        return None

    # First, check if there's a results/ subdirectory (created by reference agent)
    results_dir = gen_dir / "results"
    if results_dir.is_dir():
        json_files = list(results_dir.glob("*.json"))
        if json_files:
            # Return the most recently modified file from results/
            return max(json_files, key=lambda p: p.stat().st_mtime)

    # Try common patterns in gen_dir itself
    patterns = ["results*.json", "submission*.json", "output*.json"]
    for pattern in patterns:
        matches = list(gen_dir.glob(pattern))
        if matches:
            # Return the most recently modified file
            return max(matches, key=lambda p: p.stat().st_mtime)

    # If no pattern matches, look for any JSON file
    json_files = list(gen_dir.glob("*.json"))
    if len(json_files) == 1:
        return json_files[0]
    elif len(json_files) > 1:
        # Return the most recently modified
        return max(json_files, key=lambda p: p.stat().st_mtime)

    return None


def normalize_answer(answer: str) -> str:
    """Normalize an answer to a single letter A-D."""
    answer = str(answer).strip().upper()

    # If it's already a single letter A-D, return it
    if answer in "ABCD":
        return answer

    # Try to extract the first A-D letter from the string
    for char in answer:
        if char in "ABCD":
            return char

    return ""


def evaluate_submission(submission: Dict, correct_answers: Dict[int, str], questions: List[dict]) -> Dict:
    """
    Evaluate a submission against ground truth.

    Args:
        submission: The submission JSON containing model answers
        correct_answers: Mapping of question_id -> correct_answer_letter
        questions: Original questions list for metadata

    Returns:
        Dictionary with evaluation results
    """
    results = {
        "total_questions": len(correct_answers),
        "correct": 0,
        "incorrect": 0,
        "missing": 0,
        "invalid": 0,
        "accuracy": 0.0,
        "accuracy_percent": 0.0,
        "details": [],
        "timestamp": datetime.now().isoformat(),
    }

    # Build a lookup for question metadata
    question_lookup = {q.get("id"): q for q in questions}

    # Extract answers from submission
    # Support multiple formats
    submission_answers = {}

    if "details" in submission:
        # Format: {"details": [{"question_id": 1, "model_answer": "A"}, ...]}
        for detail in submission["details"]:
            qid = detail.get("question_id")
            answer = detail.get("model_answer", "")
            if qid is not None:
                submission_answers[qid] = normalize_answer(answer)

    elif "answers" in submission:
        # Format: {"answers": {"1": "A", "2": "B", ...}}
        for qid_str, answer in submission["answers"].items():
            try:
                qid = int(qid_str)
                submission_answers[qid] = normalize_answer(answer)
            except ValueError:
                continue

    else:
        # Try to extract from top-level if submission is just a dict of answers
        for key, value in submission.items():
            if key in ["model", "dataset_config", "timestamp", "total_questions",
                      "correct", "incorrect", "accuracy", "total_cost_usd",
                      "total_input_tokens", "total_output_tokens", "total_reasoning_tokens"]:
                continue
            try:
                qid = int(key)
                submission_answers[qid] = normalize_answer(value)
            except (ValueError, TypeError):
                continue



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/reference/reference_target_agent.py =====

#!/usr/bin/env python3
"""
Qwen/Qwen3-4B-Instruct-2507 on diamond_questions.json via Tinker API.

This script:
1. Loads questions from data/public/diamond_questions.json (pre-shuffled, no answers)
2. Calls Tinker API (Qwen) to get model predictions (letters A-D)
3. Saves answers to: results/{model}_{dataset}_{timestamp}.json
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import argparse
import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tqdm.asyncio import tqdm as async_tqdm


# -----------------------------------------------------------------------------
# Configuration — model, labels, concurrency, pricing
# -----------------------------------------------------------------------------
MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"
TINKER_BASE_URL = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"
DATASET_LABEL = "diamond_qna"
CONCURRENCY = 5
MODEL_PRICING = {"input": 0.0, "output": 0.0}


# -----------------------------------------------------------------------------
# Structured output — schema
# -----------------------------------------------------------------------------
class Answer(BaseModel):
    answer: str = Field(description="Letter A, B, C, or D")


# -----------------------------------------------------------------------------
# Cost & API client
# -----------------------------------------------------------------------------
def calculate_cost(input_tokens: int, output_tokens: int, reasoning_tokens: int = 0) -> float:
    return (input_tokens / 1e6) * MODEL_PRICING["input"] + ((output_tokens + reasoning_tokens) / 1e6) * MODEL_PRICING["output"]


def setup_client() -> AsyncOpenAI:
    api_key = os.getenv("TINKER_API_KEY")
    if not api_key:
        raise SystemExit("Set TINKER_API_KEY environment variable.")
    return AsyncOpenAI(api_key=api_key, base_url=TINKER_BASE_URL)


# -----------------------------------------------------------------------------
# Prompt building & model response parsing
# -----------------------------------------------------------------------------
def format_question(example: dict) -> str:
    """
    Format a question with answer options.
    """
    question_text = example["Question"]
    options = example["options"]

    prompt = (
        f"Answer this multiple choice question.\n\n{question_text}\n\n"
        f"A) {options['A']}\nB) {options['B']}\nC) {options['C']}\nD) {options['D']}\n\n"
        f'Respond with JSON only: {{"answer": "A"}} (value is A, B, C, or D).'
    )

    return prompt


def parse_answer_letter(model_answer_raw: str) -> str:
    """
    Extract A, B, C, or D from the model response.
    """
    # Try to find JSON block
    json_match = re.search(r'\{.*\}', model_answer_raw, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            answer = str(data.get("answer", "")).strip().upper()
            if answer in "ABCD":
                return answer
        except json.JSONDecodeError:
            pass

    # Fallback: look for the first A, B, C, or D in the raw string
    answer = model_answer_raw.strip().upper()
    if answer in "ABCD":
        return answer
    
    # Try to find "The answer is X" pattern
    match = re.search(r'ANSWER IS ([ABCD])', answer)
    if match:
        return match.group(1)
        
    match = re.search(r'ANSWER: ([ABCD])', answer)
    if match:
        return match.group(1)

    return next((letter for letter in "ABCD" if letter in answer), "")


# -----------------------------------------------------------------------------
# Inference — one question
# -----------------------------------------------------------------------------
async def get_answer_async(
    index: int,
    example: dict,
    client: AsyncOpenAI,
    semaphore: asyncio.Semaphore,
) -> dict:
    """
    Get model answer for a single question.
    """
    question_id = example.get("id", index)
    async with semaphore:
        try:
            prompt = format_question(example)
            model_answer_raw, model_answer = "", ""
            input_tokens, output_tokens = 0, 0

            for attempt in range(3):
                try:
                    response = await client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                        max_tokens=1000,
                        # Some models might not support json_object mode, but Tinker usually does
                        response_format={"type": "json_object"}
                    )
                    model_answer_raw = (response.choices[0].message.content or "").strip()
                    if not model_answer_raw:
                        raise ValueError("empty model response")
                    
                    model_answer = parse_answer_letter(model_answer_raw)
                    if model_answer not in "ABCD":
                        raise ValueError(f"answer must be A–D, got: {model_answer_raw[:120]!r}")
                    
                    usage = response.usage
                    input_tokens = usage.prompt_tokens
                    output_tokens = usage.completion_tokens
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(2**attempt)
            
            return {
                "success": True,
                "question_id": question_id,
                "model_answer": model_answer,
                "model_answer_raw": model_answer_raw,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "reasoning_tokens": 0,
                "cost_usd": calculate_cost(input_tokens, output_tokens),
            }
        except Exception as exc:
            return {"success": False, "question_id": question_id, "error": str(exc)}


async def get_all_answers_async(
    questions: list, client: AsyncOpenAI, concurrency: int
) -> list:
    """Run inference on all questions concurrently."""
    semaphore = asyncio.Semaphore(max(1, concurrency))
    tasks = [
        get_answer_async(index, example, client, semaphore)
        for index, example in enumerate(questions)
    ]
    return await async_tqdm.gather(*tasks, desc="Getting answers")




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/data/public/evaluate.py =====

"""
Evaluate a submission against the private ground truth.

Usage:
    python tasks/lawbench/data/public/evaluate.py --gen-dir runs/run_30/gen_1
    python tasks/lawbench/data/public/evaluate.py --all-gens --run-dir runs/run_30
    python tasks/lawbench/data/public/evaluate.py --submission runs/run_30/gen_1/submission.csv
"""

import argparse
import json
import sys
import pandas as pd
from pathlib import Path

# Get task root (go up from data/public/ to task root)
TASK_DIR   = Path(__file__).parent.parent.parent
TRUTH_PATH = TASK_DIR / "data/private/test.csv"


def evaluate(submission_path: Path) -> dict:
    truth = pd.read_csv(TRUTH_PATH)
    pred  = pd.read_csv(submission_path)

    label_col = "label" if "label" in pred.columns else pred.columns[-1]
    pred = pred.rename(columns={label_col: "pred_label"})

    # align on id
    merged = truth.merge(pred[["id", "pred_label"]], on="id", how="left")
    merged["pred_label"] = merged["pred_label"].fillna("__missing__")

    correct = merged["pred_label"].values == merged["label"].values
    acc = correct.mean()

    per_class = (
        pd.DataFrame({"true": merged["label"].values, "ok": correct})
        .groupby("true")["ok"]
        .mean()
        .sort_values()
    )

    return {
        "accuracy":  float(acc),
        "n_correct": int(correct.sum()),
        "n_total":   len(correct),
        "per_class": per_class.to_dict(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, help="Path to submission CSV")
    parser.add_argument("--gen-dir",   type=Path, help="Generation directory (looks for submission.csv or predictions.csv)")
    parser.add_argument("--run-dir",   type=Path, help="Run directory (for --all-gens)")
    parser.add_argument("--runs-dir",  type=Path, help="Runs root (for --all-runs)")
    parser.add_argument("--all-gens",  action="store_true")
    parser.add_argument("--all-runs",  action="store_true")
    args = parser.parse_args()

    if args.all_runs and args.runs_dir:
        for run_dir in sorted(args.runs_dir.glob("run_*")):
            _print_all_gens(run_dir)

    elif args.all_gens and args.run_dir:
        _print_all_gens(args.run_dir)

    elif args.gen_dir:
        # Find submission file in generation directory
        submission_path = None
        for fname in ["submission.csv", "predictions.csv"]:
            candidate = args.gen_dir / fname
            if candidate.exists():
                submission_path = candidate
                print(f"Found submission: {fname}")
                break

        if not submission_path:
            print(f"Error: No submission.csv or predictions.csv found in {args.gen_dir}")
            sys.exit(1)

        # Run evaluation
        print("\nEvaluating...")
        r = evaluate(submission_path)

        # Save results to results.json (required by orchestrator)
        results_path = args.gen_dir / "results.json"
        with open(results_path, 'w') as f:
            json.dump(r, f, indent=2)
        print(f"Saved results to: {results_path}")

        # Print summary
        print(f"\nAccuracy : {r['accuracy']:.4f}  ({r['n_correct']}/{r['n_total']})")
        print("\nWorst 10 classes:")
        items = sorted(r["per_class"].items(), key=lambda x: x[1])
        for cls, acc in items[:10]:
            bar = "#" * int(acc * 20)
            print(f"  {cls:<42} {acc:.2f}  {bar}")
        print("\nBest 10 classes:")
        for cls, acc in items[-10:]:
            bar = "#" * int(acc * 20)
            print(f"  {cls:<42} {acc:.2f}  {bar}")

    elif args.submission:
        r = evaluate(args.submission)
        print(f"\nAccuracy : {r['accuracy']:.4f}  ({r['n_correct']}/{r['n_total']})")
        print("\nWorst 10 classes:")
        items = sorted(r["per_class"].items(), key=lambda x: x[1])
        for cls, acc in items[:10]:
            bar = "#" * int(acc * 20)
            print(f"  {cls:<42} {acc:.2f}  {bar}")
        print("\nBest 10 classes:")
        for cls, acc in items[-10:]:
            bar = "#" * int(acc * 20)
            print(f"  {cls:<42} {acc:.2f}  {bar}")
    else:
        parser.print_help()


def _print_all_gens(run_dir: Path):
    print(f"\nRun: {run_dir.name}")
    print(f"{'Gen':<8} {'Accuracy':>10} {'Correct':>12}  File")
    print("-" * 55)
    for gen_dir in sorted(run_dir.glob("gen_*")):
        for fname in ["submission.csv", "predictions.csv"]:
            sub = gen_dir / fname
            if sub.exists():
                try:
                    r = evaluate(sub)
                    print(f"{gen_dir.name:<8} {r['accuracy']:>10.4f} {r['n_correct']:>6}/{r['n_total']:<6}  {fname}")
                except Exception as e:
                    print(f"{gen_dir.name:<8}  ERROR: {e}")
                break
    print()


if __name__ == "__main__":
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/reference/reference_target_agent.py =====

#!/usr/bin/env python3
"""
Reference Target Agent for LawBench Criminal Charge Prediction

Uses GPT-OSS-120B via Tinker API to predict criminal charges from Chinese legal cases.

Usage:
    python reference_target_agent.py --dataset_dir /path/to/dataset --working_dir /path/to/working
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Tinker configuration (hardcoded)
TINKER_BASE_URL = "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1"
TINKER_MODEL = "openai/gpt-oss-120b"


def extract_charge(response_text: str, valid_classes: list) -> str:
    """
    Extract the charge prediction from LLM response.
    Tries to match against valid classes.
    """
    # Clean the response
    text = response_text.strip()

    # Try to find exact match in valid classes
    for valid_class in valid_classes:
        if valid_class in text:
            return valid_class

    # If no exact match, return the first few characters (likely the charge)
    # Remove common prefixes/suffixes
    text = text.replace('罪名：', '').replace('[罪名]', '').replace('罪', '').strip()

    # Try again with cleaned text
    for valid_class in valid_classes:
        if valid_class.replace('罪', '').strip() in text:
            return valid_class

    # Fallback: return first valid class (better than crashing)
    logger.warning(f"Could not extract valid charge from: {text[:100]}")
    return valid_classes[0] if valid_classes else "盗窃"


def main():
    parser = argparse.ArgumentParser(
        description='Reference agent for LawBench charge prediction using GPT-OSS-120B'
    )
    parser.add_argument('--dataset_dir', required=True, help='Path to dataset directory (READ-ONLY)')
    parser.add_argument('--working_dir', required=True, help='Path to working directory (READ-WRITE)')
    args = parser.parse_args()

    dataset_dir = Path(args.dataset_dir)
    working_dir = Path(args.working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    # Get API key from environment
    api_key = os.environ.get("TINKER_API_KEY")
    if not api_key:
        logger.error("❌ TINKER_API_KEY environment variable not set")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("LawBench Criminal Charge Prediction - GPT-OSS-120B Agent")
    logger.info("=" * 70)
    logger.info(f"Model: {TINKER_MODEL}")
    logger.info(f"Dataset directory: {dataset_dir}")
    logger.info(f"Working directory: {working_dir}")

    # Initialize OpenAI client with Tinker
    client = OpenAI(
        api_key=api_key,
        base_url=TINKER_BASE_URL,
    )

    # Track execution
    execution_log = []
    start_time = datetime.now()

    try:
        # Step 1: Load test data
        logger.info("\n[Step 1] Loading test data...")
        test_path = dataset_dir / "test.csv"
        test_df = pd.read_csv(test_path)
        logger.info(f"  ✓ Loaded {len(test_df)} test samples")

        execution_log.append({
            "step": "load_test",
            "status": "success",
            "samples": len(test_df)
        })

        # Step 2: Load valid classes
        logger.info("\n[Step 2] Loading valid classes...")
        classes_path = dataset_dir / "classes.json"
        with open(classes_path, 'r', encoding='utf-8') as f:
            valid_classes = json.load(f)
        logger.info(f"  ✓ Loaded {len(valid_classes)} valid classes")

        execution_log.append({
            "step": "load_classes",
            "status": "success",
            "num_classes": len(valid_classes)
        })

        # Step 3: Load training data for few-shot examples (optional)
        logger.info("\n[Step 3] Loading training data for few-shot examples...")
        train_path = dataset_dir / "train.csv"
        train_df = pd.read_csv(train_path)
        sample_charges = train_df['label'].unique().tolist()[:10]
        logger.info(f"  ✓ Using {len(sample_charges)} sample charges for prompting")

        execution_log.append({
            "step": "load_train_samples",
            "status": "success",
            "sample_charges": len(sample_charges)
        })

        # Step 4: Generate predictions with multi-trajectory logging
        logger.i
