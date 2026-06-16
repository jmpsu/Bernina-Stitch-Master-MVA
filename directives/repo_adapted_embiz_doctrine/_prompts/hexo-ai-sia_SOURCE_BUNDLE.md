

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
        logger.info("\n[Step 4] Generating predictions using GPT-OSS-120B...")
        logger.info("  → Processing test cases...")

        # Create agent_execution directory for multi-trajectory format
        execution_dir = working_dir / "agent_execution"
        execution_dir.mkdir(exist_ok=True)

        predictions = []
        failed_count = 0
        trajectories = []

        for idx, row in tqdm(test_df.iterrows(), total=len(test_df), desc="Predicting"):
            test_id = row['id']
            case_text = row['text']

            # Build prompt for this case
            examples = ""
            if sample_charges:
                examples = "\n示例：\n" + "\n".join([
                    f"- {charge}" for charge in sample_charges[:10]
                ]) + "\n"

            prompt = f"""你是一位法律专家。根据以下案件事实，预测被告人被判定的罪名。

{examples}
案件事实：
{case_text}

请从以下191个罪名中选择一个最合适的罪名：
{", ".join(valid_classes[:20])}... (共191个罪名)

只回答罪名，不要其他解释。格式：罪名"""

            trajectory = []

            try:
                # Record the request
                trajectory.append({
                    "role": "user",
                    "content": prompt,
                    "timestamp": datetime.now().isoformat()
                })

                # Make API call
                response = client.chat.completions.create(


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/data/public/evaluate.py =====

#!/usr/bin/env python3
"""
Evaluate LongCoT Chess submissions from target_agent.py output.

This script:
1. Loads ground truth from data/private/answers.json (with correct answers)
2. Loads model predictions from a submission JSON file (responses.json)
3. Compares model answers against correct answers
4. Outputs accuracy metrics and per-question breakdown

The script automatically looks for JSON files in the results/ subdirectory
if it exists within --gen-dir, or searches for responses.json directly.

Usage:
    python evaluate.py --gen-dir path/to/generation/directory
    python evaluate.py --submission path/to/responses.json
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def load_ground_truth(answers_path: Path) -> Dict[str, Any]:
    """Load ground truth answers."""
    if not answers_path.is_file():
        raise FileNotFoundError(f"Ground truth file not found: {answers_path}")

    with open(answers_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_submission(submission_path: Path) -> List[Dict[str, Any]]:
    """Load a submission JSON file (responses.json format)."""
    if not submission_path.is_file():
        raise FileNotFoundError(f"Submission file not found: {submission_path}")

    with open(submission_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_submission_file(gen_dir: Path) -> Optional[Path]:
    """
    Find a submission JSON file in the generation directory.

    Search order:
    1. Check for results/ subdirectory and look for JSON files there
    2. Look for responses.json directly in gen_dir
    3. Look for common patterns (results*.json, submission*.json, output*.json)
    4. If only one JSON file exists, use that
    """
    if not gen_dir.is_dir():
        return None

    # First, check if there's a results/ subdirectory
    results_dir = gen_dir / "results"
    if results_dir.is_dir():
        json_files = list(results_dir.glob("*.json"))
        if json_files:
            # Return the most recently modified file from results/
            return max(json_files, key=lambda p: p.stat().st_mtime)

    # Check for responses.json directly
    responses_file = gen_dir / "responses.json"
    if responses_file.is_file():
        return responses_file

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


def evaluate_answer(
    predicted: Union[List[str], int, str, None], expected: Union[List[str], str]
) -> bool:
    """Compare predicted answer with expected answer."""
    if predicted is None:
        return False

    # Both are lists (e.g., chess moves)
    if isinstance(expected, list) and isinstance(predicted, list):
        if len(predicted) != len(expected):
            return False
        # Check if any permutation matches (for unordered answers)
        # For chess moves, order matters, so direct comparison
        return predicted == expected or set(predicted) == set(expected)

    # Both are strings/numbers
    if isinstance(expected, (str, int)) and isinstance(predicted, (str, int)):
        return str(predicted).strip() == str(expected).strip()

    # Type mismatch
    return False


def evaluate_submission(
    results: List[Dict[str, Any]], correct_answers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a submission against ground truth.

    Args:
        results: List of results from responses.json
        correct_answers: Dictionary of correct answers

    Returns:
        Dictionary with evaluation results
    """
    evaluation_results = []
    correct = 0
    failed_inference = 0
    wrong_answer = 0

    for result in results:
        question_id = result.get("question_id")
        predicted = result.get("solution")

        # Get expected answer
        expected = correct_answers.get(question_id)

        if predicted is None:
            # Solution is None - failed inference or parse error
            status = "FAILED_INFERENCE"
            is_correct = False
            failed_inference += 1
        else:
            # Evaluate solution
            is_correct = evaluate_answer(predicted, expected)
            if is_correct:
                status = "CORRECT"
                correct += 1
            else:
                status = "WRONG"
                wrong_answer += 1

        # Store evaluation
        eval_result = {
            "question_id": question_id,
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "status": status,
        }
        evaluation_results.append(eval_result)

    # Calculate metrics
    total = len(results)
    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        "total_questions": total,
        "correct": correct,
        "wrong_answer": wrong_answer,
        "failed_inference": failed_inference,
        "accuracy": accuracy,
        "accuracy_percent": accuracy,
        "details": evaluation_results,
        "timestamp": datetime.now().isoformat(),
    }


def save_evaluation_results(results: Dict, output_path: Path) -> None:
    """Save evaluation results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/reference/reference_target_agent.py =====

#!/usr/bin/env python3
"""
Reference target agent to run Gemini inference on chess hard questions.

This script:
1. Loads questions from chess_hard.json
2. Runs inference using Gemini API
3. Extracts and saves solutions to responses.json
4. Automatically runs evaluation and reports accuracy

Usage:
    python reference_target_agent.py --dataset_dir ./data/public --working_dir ./output

Environment variables required:
    GEMINI_API_KEY: Your Google Gemini API key
"""

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List


def setup_gemini_client(api_key: str):
    """Initialize Gemini client."""
    from google import genai
    return genai.Client(api_key=api_key)


def load_chess_hard_questions(dataset_dir: Path) -> List[Dict[str, Any]]:
    """Load chess hard questions from chess_hard.json."""
    chess_hard_path = dataset_dir / "chess_hard.json"

    if not chess_hard_path.exists():
        raise FileNotFoundError(f"Chess hard questions not found at {chess_hard_path}")

    with open(chess_hard_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not questions:
        raise ValueError("No questions found in chess_hard.json")

    print(f"Loaded {len(questions)} questions from chess_hard.json")
    return questions


def extract_solution(response: str):
    """Extract solution from model response.

    Handles formats like:
    - solution = ["c4", "bxc4", "bxc4"]
    - solution = 218
    """
    if not response:
        return None

    import re

    # Look for solution = [...] or solution = <number>
    pattern = r'solution\s*=\s*(.+?)(?:\n|$)'
    match = re.search(pattern, response, re.IGNORECASE)

    if not match:
        return None

    solution_str = match.group(1).strip()

    # Try to parse as list
    if solution_str.startswith('['):
        try:
            # Clean up the string and parse
            solution_str = solution_str.replace("'", '"')
            parsed = json.loads(solution_str)
            # Return as list of strings
            return [str(x).strip() for x in parsed]
        except:
            # Try to extract manually
            items = re.findall(r'[\"\']?([^,\[\]\"\'\s]+)[\"\']?', solution_str)
            return [item.strip() for item in items if item.strip()]

    # Try to parse as number or string
    solution_str = solution_str.strip('"\'')
    try:
        # Try to convert to int
        return int(solution_str)
    except ValueError:
        # Return as string
        return solution_str


def call_gemini(client, model: str, prompt: str) -> Dict[str, Any]:
    """Call Gemini API and return response with metadata."""
    from google.genai import types

    try:
        start_time = time.time()

        config = types.GenerateContentConfig(
            max_output_tokens=8192,
        )

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )

        elapsed = time.time() - start_time

        # Extract text from response
        text_parts = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if not getattr(part, "thought", False) and part.text:
                    text_parts.append(part.text)

        content = "".join(text_parts) if text_parts else (response.text or "")

        # Extract usage metadata
        usage = {}
        if response.usage_metadata:
            m = response.usage_metadata
            usage = {
                "prompt_tokens": getattr(m, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(m, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(m, "total_token_count", 0) or 0,
            }

        return {
            "success": True,
            "content": content,
            "usage": usage,
            "elapsed_seconds": elapsed,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "content": None,
            "usage": {},
            "elapsed_seconds": time.time() - start_time,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }


def run_inference(
    client,
    model: str,
    questions: List[Dict[str, Any]],
    working_dir: Path
):
    """Run inference on all questions and save results."""

    # Create working directory
    working_dir.mkdir(parents=True, exist_ok=True)

    results = []

    print(f"\nRunning inference on {len(questions)} questions...")
    print(f"Model: {model}")
    print(f"Output directory: {working_dir}\n")

    for idx, question in enumerate(questions, 1):
        question_id = question.get("question_id", f"unknown_{idx}")
        prompt = question.get("prompt", "")

        print(f"[{idx}/{len(questions)}] Processing {question_id}...", end=" ", flush=True)

        # Call Gemini
        response = call_gemini(client, model, prompt)

        # Extract solution from response
        solution = None
        if response["success"] and response["content"]:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/spaceship-titanic/reference/reference_target_agent.py =====

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

# ── Agent loop ────────────────────────────────────────────────────────────────

def run_agent(task: str) -> None:
    print(f"\n{'='*60}")
    print(f"Task: {task}")
    print('='*60)

    messages = [{"role": "user", "content": task}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        # Collect any text the model emits this turn
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\nAssistant: {block.text}")

        # Done – no more tool calls
        if response.stop_reason == "end_turn":
            break

        # Handle tool calls
        if response.stop_reason == "tool_use":
            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n[Tool] {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                    result = dispatch_tool(block.name, block.input)
                    print(f"[Result] {result[:200]}{'...' if len(result) > 200 else ''}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop reason – bail out
            print(f"Unexpected stop_reason: {response.stop_reason}")
            break

    print(f"\n{'='*60}\nDone.\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_agent(
        "Write a Python file called hello.py that prints 'Hello, World!', "
        "then run it with bash and confirm the output is correct."
    )


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/util.py =====

"""Backward-compatible shim.

Agent impls moved to the ``sia.agent_impls`` package. This module is kept so
existing imports (``from sia.util import run_agent``) continue to work.
"""

from sia.agent_impls import available_agent_impls, get_agent_impl, run_agent

__all__ = ["available_agent_impls", "get_agent_impl", "run_agent"]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/web/__init__.py =====

"""Web visualizer for the SIA ``runs/`` directory.

Public surface:
    create_app(runs_dir)          -> FastAPI app
    serve(...)                    -> run in foreground (``sia web``)
    serve_in_background(...)      -> daemon thread (live dashboard during ``sia run``)
"""

from sia.web.server import create_app, serve, serve_in_background

__all__ = ["create_app", "serve", "serve_in_background"]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/web/runs.py =====

"""Data layer for the runs visualizer.

Pure, dependency-light functions that read the ``runs/`` directory tree and turn
it into JSON-serializable models. Nothing here imports FastAPI, so it can be
unit-tested in isolation and reused from other tools.

Directory shape this understands (see orchestrator.py for the writer side)::

    runs/
      run_<id>/
        context.md                 # run-level metadata + per-generation log
        gen_<n>/
          target_agent.py          # the generated agent code
          meta_agent_prompt.txt     # gen 1: the meta-agent prompt
          feedback_agent_prompt.txt # gen >1: the feedback prompt
          improvement.md            # gen >1: the improvement plan
          evaluation_results.json   # scores + per-question details
          evaluation.log            # evaluator stdout/stderr
          target_agent_stdout.log   # agent stdout
          agent_execution/          # execution_q<id>.json per-question chat logs
          openhands_trajectory/     # <session>/events/event-*.json (optional)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Files we surface as first-class artifacts in the UI (label -> filename).
TEXT_ARTIFACTS: dict[str, str] = {
    "target_agent": "target_agent.py",
    "meta_prompt": "meta_agent_prompt.txt",
    "feedback_prompt": "feedback_agent_prompt.txt",
    "improvement": "improvement.md",
    "eval_log": "evaluation.log",
    "stdout_log": "target_agent_stdout.log",  # or train_stdout.log for weights mode
}

# Alternative filenames to check for stdout_log artifact
_STDOUT_LOG_ALTS = ("target_agent_stdout.log", "train_stdout.log")

# Candidate names for the structured evaluation summary, in priority order.
_EVAL_RESULT_NAMES = ("evaluation_results.json", "results.json")

_RUN_DIR_RE = re.compile(r"^run_(\d+)$")
_GEN_DIR_RE = re.compile(r"^gen_(\d+)$")
_EXEC_FILE_RE = re.compile(r"^execution_q(\d+)\.json$")
_META_RE = re.compile(r"^\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.*)$")


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class EvalSummary(BaseModel):
    """Headline numbers from a generation's evaluation results."""

    total: int | None = None
    correct: int | None = None
    incorrect: int | None = None
    missing: int | None = None
    invalid: int | None = None
    accuracy_percent: float | None = None


class GenerationSummary(BaseModel):
    name: str
    index: int
    eval: EvalSummary | None = None
    has_target_agent: bool = False
    has_improvement: bool = False
    num_trajectories: int = 0


class RunSummary(BaseModel):
    name: str
    index: int
    task: str | None = None
    meta_model: str | None = None
    task_model: str | None = None
    agent_impl: str | None = None
    started: str | None = None
    max_generations: int | None = None
    num_generations: int = 0
    best_accuracy_percent: float | None = None
    generations: list[GenerationSummary] = []


class DomainStat(BaseModel):
    domain: str
    total: int
    correct: int
    accuracy_percent: float


class GenerationDetail(BaseModel):
    name: str
    index: int
    eval: EvalSummary | None = None
    domains: list[DomainStat] = []
    artifacts: list[str] = []
    trajectories: list[int] = []
    has_openhands: bool = False


class RunDetail(BaseModel):
    name: str
    index: int
    task: str | None = None
    meta_model: str | None = None
    task_model: str | None = None
    agent_impl: str | None = None
    started: str | None = None
    max_generations: int | None = None
    # Resolved meta/target agent profiles (full JSON from the run's profiles.json),
    # rendered as-is in the profile chips. None for older runs predating profiles.json.
    profiles: dict[str, Any] | None = None
    context_md: str | None = None
    generations: list[GenerationDetail] = []


# --------------------------------------------------------------------------- #
# Filesystem helpers
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> Any | None:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _eval_results_path(gen_dir: Path) -> Path | None:
    for name in _EVAL_RESULT_NAMES:
        candidate = gen_dir / name
        if candidate.is_file():
            return candidate
    return None


def _eval_summary(gen_dir: Path) -> EvalSummary | None:
    path = _eval_results_path(gen_dir)
    if path is None:
        return None
    data = _read_json(path)
    if not isinstance(data, dict):
        return None
    pct = data.get("accuracy_percent")
    if pct is None and isinstance(data.get("accuracy"), int | float):
        pct = data["accuracy"] * 100
    return EvalSummary(
        total=data.get("total_questions") or data.get("total"),
        correct=data.get("correct"),
        incorrect=data.get("incorrect"),
        missing=data.get("missing"),
        invalid=data.get("invalid"),
        accuracy_percent=pct,
    )


def _trajectory_ids(gen_dir: Path) -> list[int]:
    exec_dir = gen_dir / "agent_execution"
    if not exec_dir.is_dir():
        return []
    ids: list[int] = []
    for child in exec_dir.iterdir():
        m = _EXEC_FILE_RE.match(child.name)
        if m:
            ids.append(int(m.group(1)))
    return sorted(ids)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/web/server.py =====

"""FastAPI app + launchers for the runs visualizer.

``create_app(runs_dir)`` builds the app; ``serve(...)`` runs it in the
foreground (the ``sia web`` command); ``serve_in_background(...)`` starts it in a
daemon thread so the orchestrator can expose a live dashboard during ``sia run``.
"""

from __future__ import annotations

import threading
from pathlib import Path

from sia.logging_setup import get_logger
from sia.web import runs as runs_data

logger = get_logger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"


def create_app(runs_dir: str | Path):
    """Build the FastAPI application serving the runs under ``runs_dir``."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import FileResponse, PlainTextResponse
    except ModuleNotFoundError as exc:  # pragma: no cover - import guard
        raise RuntimeError(
            "The web visualizer needs FastAPI + uvicorn. Install with:\n    pip install 'sia-agent[web]'"
        ) from exc

    runs_root = Path(runs_dir).resolve()
    app = FastAPI(title="SIA Runs Visualizer", docs_url="/api/docs", openapi_url="/api/openapi.json")

    @app.get("/api/runs")
    def api_runs():
        return runs_data.list_runs(runs_root)

    @app.get("/api/runs/{run_name}")
    def api_run(run_name: str):
        detail = runs_data.get_run(runs_root, run_name)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Run not found: {run_name}")
        return detail

    @app.get("/api/runs/{run_name}/gens/{gen_name}/eval")
    def api_eval_details(run_name: str, gen_name: str):
        details = runs_data.get_eval_details(runs_root, run_name, gen_name)
        if details is None:
            raise HTTPException(status_code=404, detail="No evaluation details found")
        return details

    @app.get("/api/runs/{run_name}/gens/{gen_name}/artifact/{label}", response_class=PlainTextResponse)
    def api_artifact(run_name: str, gen_name: str, label: str):
        text = runs_data.get_artifact_text(runs_root, run_name, gen_name, label)
        if text is None:
            raise HTTPException(status_code=404, detail=f"Artifact not found: {label}")
        return text

    @app.get("/api/runs/{run_name}/gens/{gen_name}/trajectory/{qid}")
    def api_trajectory(run_name: str, gen_name: str, qid: int):
        turns = runs_data.get_trajectory(runs_root, run_name, gen_name, qid)
        if turns is None:
            raise HTTPException(status_code=404, detail=f"Trajectory not found: q{qid}")
        return turns

    @app.get("/api/runs/{run_name}/gens/{gen_name}/openhands")
    def api_openhands_sessions(run_name: str, gen_name: str):
        sessions = runs_data.list_openhands_sessions(runs_root, run_name, gen_name)
        if sessions is None:
            raise HTTPException(status_code=404, detail="Generation not found")
        return sessions

    @app.get("/api/runs/{run_name}/gens/{gen_name}/openhands/{session}")
    def api_openhands_events(run_name: str, gen_name: str, session: str):
        events = runs_data.get_openhands_events(runs_root, run_name, gen_name, session)
        if events is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return events

    @app.get("/")
    def index():
        return FileResponse(_STATIC_DIR / "index.html")

    return app


def serve(
    host: str = "127.0.0.1",
    port: int = 8000,
    runs_dir: str | Path = "./runs",
    open_browser: bool = True,
) -> None:
    """Run the server in the foreground (blocks). Used by ``sia web``."""
    import uvicorn

    app = create_app(runs_dir)
    url = f"http://{host}:{port}"
    logger.info(f"SIA visualizer serving {Path(runs_dir).resolve()} at {url}")
    if open_browser:
        _open_browser_later(url)
    uvicorn.run(app, host=host, port=port, log_level="warning")


def serve_in_background(
    host: str = "127.0.0.1",
    port: int = 8000,
    runs_dir: str | Path = "./runs",
) -> threading.Thread | None:
    """Start the server in a daemon thread; never raises if deps are missing.

    Returns the thread (or ``None`` if the server could not start). Intended to
    give a live dashboard while ``sia run`` is executing.
    """
    try:
        import uvicorn

        app = create_app(runs_dir)
    except (RuntimeError, ModuleNotFoundError) as exc:
        logger.warning(f"Live dashboard unavailable: {exc}")
        return None

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    def _run() -> None:
        try:
            server.run()
        except Exception as exc:  # pragma: no cover - background best-effort
            logger.warning(f"Live dashboard stopped: {exc}")

    thread = threading.Thread(target=_run, name="sia-web", daemon=True)
    thread.start()
    logger.info(f"Live dashboard: http://{host}:{port} (serving {Path(runs_dir).resolve()})")
    return thread


def _open_browser_later(url: str, delay: float = 1.0) -> None:
    import webbrowser

    threading.Timer(delay, lambda: webbrowser.open(url)).start()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/conftest.py =====

"""Pytest configuration for the SIA test suite.

Ensures the tests directory is importable so shared helpers (e.g. golden_master)
can be imported as top-level modules regardless of pytest's import mode.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden_master.py =====

"""Golden-master test helper.

Characterization tests capture the *current* output of a function as a committed
"golden" file, then assert future runs produce byte-identical output. This locks
business logic (especially the large prompt / context.md strings) so the refactor
can be proven behavior-preserving.

To (re)generate goldens after an intentional change:

    UPDATE_GOLDEN=1 python -m pytest tests/

Volatile substrings (timestamps, temp paths) must be normalized by the caller
before passing text in, so goldens stay deterministic across machines/runs.
"""

from __future__ import annotations

import difflib
import os
import re
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "golden"
_UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"

# Matches "YYYY-MM-DD HH:MM:SS" timestamps (datetime.now() output in the code).
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


def normalize_timestamps(text: str) -> str:
    """Replace concrete timestamps with a stable placeholder."""
    return _TIMESTAMP_RE.sub("<TS>", text)


def normalize_paths(text: str, replacements: dict[str, str]) -> str:
    """Replace volatile absolute paths with stable placeholders.

    For each (path -> placeholder), both the raw and os-resolved forms are
    replaced (macOS temp dirs resolve /var -> /private/var).
    """
    for raw, placeholder in replacements.items():
        for variant in (raw, str(Path(raw).resolve())):
            text = text.replace(variant, placeholder)
    return text


def assert_golden(name: str, actual: str) -> None:
    """Assert `actual` matches committed golden `name` (or write it under UPDATE_GOLDEN)."""
    path = GOLDEN_DIR / name
    if _UPDATE:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    assert path.exists(), f"Missing golden '{name}'. Generate with: UPDATE_GOLDEN=1 pytest"
    expected = path.read_text(encoding="utf-8")
    if actual != expected:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile=f"golden/{name}",
                tofile="actual",
                lineterm="",
            )
        )
        raise AssertionError(f"Golden mismatch for '{name}':\n{diff}")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_agent_impls.py =====

"""Tests for the agent-impl registry and the PydanticAI agent impl."""

import asyncio

import pytest

from sia.agent_impls import available_agent_impls, get_agent_impl


def test_registry_lists_builtin_agent_impls():
    assert set(available_agent_impls()) >= {"claude", "openhands", "pydantic-ai"}


def test_get_agent_impl_returns_callable():
    assert callable(get_agent_impl("claude"))
    assert callable(get_agent_impl("pydantic-ai"))


def test_get_agent_impl_unknown_raises():
    with pytest.raises(ValueError):
        get_agent_impl("does-not-exist")


def test_util_reexports_registry_run_agent():
    from sia.agent_impls import run_agent as impl_run_agent
    from sia.util import run_agent as util_run_agent

    assert util_run_agent is impl_run_agent


def test_pydantic_ai_impl_runs_with_test_model(tmp_path):
    pytest.importorskip("pydantic_ai")
    from pydantic_ai.models.test import TestModel

    from sia.agent_impls.pydantic_ai import run_agent_pydantic_ai

    # TestModel drives the agent without network; it exercises each registered tool,
    # so write_file should create a file in the working directory.
    asyncio.run(
        run_agent_pydantic_ai(
            TestModel(),
            "5",
            "Create a file with some content using the write_file tool.",
            str(tmp_path),
        )
    )
    assert any(tmp_path.iterdir())


def test_pydantic_ai_model_passthrough():
    from sia.agent_impls.pydantic_ai import _resolve_model

    # Model specs are passed through unchanged to PydanticAI's native parsing.
    assert _resolve_model("openai:gpt-4o") == "openai:gpt-4o"
    assert _resolve_model("anthropic:claude-sonnet-4-5") == "anthropic:claude-sonnet-4-5"
    # No provider -> still a plain passthrough.
    assert _resolve_model("openai:gpt-4o", None) == "openai:gpt-4o"


def test_openhands_model_gets_openai_prefix_for_compatible_provider():
    """An OpenAI-compatible provider (base_url) gets an explicit litellm 'openai/' prefix."""
    from sia.agent_impls.openhands import _resolve_model
    from sia.providers import load_provider

    nebius = load_provider("nebius")  # client_kind=openai, has base_url
    assert _resolve_model("moonshotai/Kimi-K2.6", nebius) == "openai/moonshotai/Kimi-K2.6"
    # Already prefixed -> not double-prefixed.
    assert _resolve_model("openai/gpt-4o", nebius) == "openai/gpt-4o"


def test_openhands_model_passthrough_without_compatible_provider():
    """Native (anthropic) and provider-less specs pass through unchanged."""
    from sia.agent_impls.openhands import _resolve_model
    from sia.providers import load_provider

    assert _resolve_model("claude-sonnet-4-5", None) == "claude-sonnet-4-5"
    anthropic = load_provider("anthropic")  # client_kind=anthropic, no base_url
    assert _resolve_model("claude-sonnet-4-5", anthropic) == "claude-sonnet-4-5"


def test_run_agent_threads_provider_to_agent_impl():
    """run_agent forwards the optional provider kwarg to the dispatched agent impl."""
    import asyncio

    from sia.agent_impls import base
    from sia.providers import load_provider

    captured = {}

    async def fake_runner(model, max_turns, prompt, cwd, provider=None):
        captured["provider"] = provider

    base.register("capture-test", fake_runner)
    nebius = load_provider("nebius")
    asyncio.run(base.run_agent("m", "5", "p", "/tmp", agent_impl="capture-test", provider=nebius))
    assert captured["provider"] is nebius


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_agent_reference.py =====

"""Tests for the target agent's reference model (sia.agent_reference)."""

from sia.agent_reference import (
    copy_reference_into,
    parse_agent_reference,
    resolve_agent_reference,
)
from sia.layout import TaskLayout


def _task_dir_with_reference(tmp_path, *, requirements=False):
    """Build a minimal task directory with a bundled reference/ folder."""
    task_dir = tmp_path / "task"
    ref = task_dir / "reference"
    ref.mkdir(parents=True)
    (ref / "reference_target_agent.py").write_text("print('bundled reference')")
    if requirements:
        (ref / "requirements.txt").write_text("anthropic\n")
    return task_dir


def test_default_resolves_to_task_reference(tmp_path):
    task_dir = _task_dir_with_reference(tmp_path)
    layout = TaskLayout(str(task_dir), str(tmp_path))

    ref = parse_agent_reference("default")
    assert ref.kind == "default"

    resolved = resolve_agent_reference(ref, layout)
    assert resolved.inline_seed == "print('bundled reference')"
    assert resolved.ref_dir is None
    assert resolved.entrypoint == "reference_target_agent.py"
    assert resolved.requirements is None


def test_default_picks_up_reference_requirements(tmp_path):
    task_dir = _task_dir_with_reference(tmp_path, requirements=True)
    layout = TaskLayout(str(task_dir), str(tmp_path))

    resolved = resolve_agent_reference(parse_agent_reference("default"), layout)
    assert resolved.requirements is not None
    assert resolved.requirements.name == "requirements.txt"


def test_omitted_spec_is_default():
    assert parse_agent_reference(None).kind == "default"


def test_single_file_reference(tmp_path):
    (tmp_path / "my_agent.py").write_text("print('mine')")
    layout = TaskLayout(str(tmp_path / "task"), str(tmp_path))

    ref = parse_agent_reference({"source": "./my_agent.py"}, base_dir=tmp_path)
    assert ref.kind == "file"

    resolved = resolve_agent_reference(ref, layout)
    assert resolved.inline_seed == "print('mine')"
    assert resolved.ref_dir is None
    assert resolved.entrypoint == "my_agent.py"


def test_directory_reference_reads_from_disk(tmp_path):
    src = tmp_path / "agent_dir"
    src.mkdir()
    (src / "main.py").write_text("import helper")
    (src / "helper.py").write_text("VALUE = 1")
    (src / "requirements.txt").write_text("numpy\n")
    layout = TaskLayout(str(tmp_path / "task"), str(tmp_path))

    ref = parse_agent_reference({"source": "./agent_dir/", "entrypoint": "main.py"}, base_dir=tmp_path)
    assert ref.kind == "dir"

    resolved = resolve_agent_reference(ref, layout)
    # Multi-file reference is NOT embedded — the agent reads it from disk.
    assert resolved.inline_seed is None
    assert resolved.ref_dir == src
    assert resolved.entrypoint == "main.py"
    assert resolved.requirements is not None


def test_copy_reference_into_directory(tmp_path):
    src = tmp_path / "agent_dir"
    src.mkdir()
    (src / "main.py").write_text("x")
    (src / "helper.py").write_text("y")
    layout = TaskLayout(str(tmp_path / "task"), str(tmp_path))
    resolved = resolve_agent_reference(
        parse_agent_reference({"source": "./agent_dir/", "entrypoint": "main.py"}, base_dir=tmp_path),
        layout,
    )

    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    copy_reference_into(resolved, gen_dir)
    assert (gen_dir / "main.py").read_text() == "x"
    assert (gen_dir / "helper.py").read_text() == "y"


def test_copy_reference_into_default_with_requirements(tmp_path):
    task_dir = _task_dir_with_reference(tmp_path, requirements=True)
    layout = TaskLayout(str(task_dir), str(tmp_path))
    resolved = resolve_agent_reference(parse_agent_reference("default"), layout)

    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    copy_reference_into(resolved, gen_dir)
    # Only the requirements.txt is carried in for a default reference (seed is inline).
    assert (gen_dir / "requirements.txt").read_text() == "anthropic\n"
    assert not (gen_dir / "reference_target_agent.py").exists()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_cli_interface.py =====

"""Verify CLI interface: ``run`` / ``web`` sub-commands and backward-compatible default."""

import subprocess
import sys


def _sia(*args):
    return subprocess.run([sys.executable, "-m", "sia", *args], capture_output=True, text=True)


def test_top_level_help_lists_subcommands():
    """sia --help should exit 0 and advertise both sub-commands."""
    result = _sia("--help")
    assert result.returncode == 0
    assert "run" in result.stdout
    assert "web" in result.stdout


def test_run_help_exposes_orchestrator_flags():
    """sia run --help should show the orchestrator flags."""
    result = _sia("run", "--help")
    assert result.returncode == 0
    for flag in ("--max_gen", "--task", "--task_dir", "--meta-agent-profile", "--target-agent-profile", "--sandbox"):
        assert flag in result.stdout


def test_web_help_exposes_server_flags():
    """sia web --help should show the server flags."""
    result = _sia("web", "--help")
    assert result.returncode == 0
    for flag in ("--host", "--port", "--runs-dir"):
        assert flag in result.stdout


def test_no_args_exits_nonzero():
    """sia without a task (defaults to `run`, which requires one) exits non-zero."""
    assert _sia().returncode != 0


def test_default_subcommand_is_run():
    """`sia --task nonexistent` is treated as `sia run --task nonexistent`."""
    assert _sia("--task", "nonexistent").returncode != 0


def test_invalid_task_exits_nonzero():
    result = _sia("run", "--task", "nonexistent")
    assert result.returncode != 0


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_config.py =====

"""Unit tests for sia.config.Config."""

from dataclasses import fields

from sia.config import Config


def test_default_values():
    cfg = Config()
    assert cfg.DEFAULT_MAX_GENERATIONS == 3
    assert cfg.DEFAULT_AGENT_IMPL == "claude"
    assert cfg.SANDBOX_MODE == "none"
    assert cfg.DEFAULT_MAX_TURNS == 20
    assert cfg.DOCKER_MEMORY_LIMIT == "2g"
    assert cfg.MAX_CONTEXT_FILE_SIZE == 10_000_000


def test_from_env_reads_sia_vars(monkeypatch):
    monkeypatch.setenv("SIA_MAX_GENERATIONS", "5")
    monkeypatch.setenv("SIA_AGENT_IMPL", "openhands")
    monkeypatch.setenv("SIA_SANDBOX_MODE", "docker")
    monkeypatch.setenv("SIA_META_MODEL", "opus")

    cfg = Config.from_env()
    assert cfg.DEFAULT_MAX_GENERATIONS == 5
    assert cfg.DEFAULT_AGENT_IMPL == "openhands"
    assert cfg.SANDBOX_MODE == "docker"
    assert cfg.DEFAULT_CLAUDE_META_MODEL == "opus"


def test_from_env_invalid_value_keeps_default(monkeypatch):
    monkeypatch.setenv("SIA_MAX_GENERATIONS", "not-a-number")

    cfg = Config.from_env()
    assert cfg.DEFAULT_MAX_GENERATIONS == 3


def test_from_env_no_vars_returns_defaults():
    cfg = Config.from_env()
    assert cfg.DEFAULT_MAX_GENERATIONS == 3
    assert cfg.DEFAULT_TASK_MODEL == "claude-haiku-4-5-20251001"


def test_config_is_dataclass_with_expected_fields():
    field_names = {f.name for f in fields(Config)}
    expected = {
        "DEFAULT_CLAUDE_META_MODEL",
        "DEFAULT_TASK_MODEL",
        "DEFAULT_MAX_GENERATIONS",
        "DEFAULT_AGENT_IMPL",
        "SANDBOX_MODE",
        "DOCKER_IMAGE",
        "MAX_CONTEXT_FILE_SIZE",
    }
    assert expected.issubset(field_names)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_config_injection.py =====

"""Regression tests for the config-injection fix.

Previously these call sites read Config.X (class attribute), silently dropping any
injected/env-overridden Config instance. These tests assert the injected instance
is now honored.
"""

import json
from unittest.mock import MagicMock, patch

from sia.config import Config
from sia.context_manager import ContextManager
from sia.orchestrator import load_agent_execution, run_evaluation


def test_load_agent_execution_honors_injected_max_size(tmp_path):
    (tmp_path / "agent_execution.json").write_text(json.dumps([{"role": "user", "content": "hi"}]))

    # Tiny limit via injected config → treated as too large.
    data, is_multi = load_agent_execution(str(tmp_path), config=Config(MAX_EXECUTION_LOG_SIZE=1))
    assert is_multi is False
    assert data["error"] == "File too large"

    # Default config loads the file normally.
    data2, _ = load_agent_execution(str(tmp_path))
    assert isinstance(data2, list)
    assert data2[0]["role"] == "user"


@patch("sia.orchestrator.subprocess.run")
def test_run_evaluation_honors_injected_timeout(mock_run, tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    pub = tmp_path / "task" / "data" / "public"
    pub.mkdir(parents=True)
    (pub / "evaluate.py").write_text("pass")
    (gen_dir / "results.json").write_text(json.dumps({"accuracy": 1.0}))
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    run_evaluation(str(gen_dir), str(tmp_path / "task"), "/fake/venv", config=Config(EVAL_TIMEOUT=123))

    assert mock_run.call_args.kwargs["timeout"] == 123


def test_context_manager_stores_injected_config(tmp_path):
    cfg = Config(AGENT_CODE_PREVIEW_LIMIT=7, CONTEXT_SUMMARY_MAX_TURNS=2)
    cm = ContextManager(str(tmp_path), {"meta_model": "x", "agent_impl": "claude"}, config=cfg)
    assert cm.cfg.AGENT_CODE_PREVIEW_LIMIT == 7
    assert cm.cfg.CONTEXT_SUMMARY_MAX_TURNS == 2


def test_from_env_override_reaches_instance(monkeypatch):
    monkeypatch.setenv("SIA_MAX_TURNS", "99")
    assert Config.from_env().DEFAULT_MAX_TURNS == 99


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_context_golden.py =====

"""Characterization: lock the full context.md produced by ContextManager.

Drives the manager through a realistic two-generation run (with metrics, deltas,
and improvement.md insights) and snapshots the entire context.md. _generate_llm_summary
is patched to None so the output is deterministic (no network / no LLM section).
"""

import json
from unittest.mock import patch

from golden_master import assert_golden, normalize_timestamps

from sia.context_manager import ContextManager

GEN1_AGENT = "print('gen 1 agent')\n"
# Larger gen-2 file so size/line deltas are exercised.
GEN2_AGENT = "import sys\n\n\ndef main():\n    print('gen 2 agent, improved')\n\n\nmain()\n"
IMPROVEMENT_MD = (
    "# Improvement Plan\n\n"
    "- Added structured error handling so the agent recovers from tool failures gracefully.\n"
    "- Switched to a retry loop with exponential backoff for transient API errors.\n"
    "- Improved logging to capture each tool call and its result for later analysis.\n"
)


@patch("sia.context_manager.ContextManager._generate_llm_summary", return_value=None)
def test_context_md_golden(_mock_llm, tmp_path):
    run_dir = tmp_path / "run_1"
    gen1 = run_dir / "gen_1"
    gen2 = run_dir / "gen_2"
    gen1.mkdir(parents=True)
    gen2.mkdir(parents=True)

    (gen1 / "target_agent.py").write_text(GEN1_AGENT)
    (gen2 / "target_agent.py").write_text(GEN2_AGENT)
    (gen2 / "improvement.md").write_text(IMPROVEMENT_MD)
    (gen1 / "results.json").write_text(json.dumps({"accuracy": 50.0, "correct": 99, "total": 198}))
    (gen2 / "results.json").write_text(json.dumps({"accuracy": 75.0, "correct": 148, "total": 198}))

    cm = ContextManager(
        str(run_dir),
        {
            "task_dir": "/tasks/example",
            "meta_model": "haiku",
            "task_model": "claude-haiku-4-5-20251001",
            "agent_impl": "claude",
            "max_gen": 2,
        },
    )
    cm.initialize()
    cm.add_generation(
        1,
        {
            "success": True,
            "timestamp": "2026-01-01 00:00:00",
            "duration": 1.5,
            "agent_path": str(gen1 / "target_agent.py"),
            "gen_dir": str(gen1),
            "improvement_path": None,
            "execution_type": "Single",
        },
    )
    cm.add_generation(
        2,
        {
            "success": True,
            "timestamp": "2026-01-01 00:05:00",
            "duration": 2.5,
            "agent_path": str(gen2 / "target_agent.py"),
            "gen_dir": str(gen2),
            "improvement_path": str(gen2 / "improvement.md"),
            "execution_type": "Single",
        },
    )
    cm.finalize()

    content = normalize_timestamps((run_dir / "context.md").read_text(encoding="utf-8"))
    assert_golden("context.md", content)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_context_manager.py =====

"""Unit tests for the ContextManager."""

import json
from unittest.mock import patch

import pytest

from sia.context_manager import ContextManager


@pytest.fixture
def run_dir(tmp_path):
    """Create a temporary run directory with a minimal gen_1."""
    gen1 = tmp_path / "gen_1"
    gen1.mkdir()

    # Create a minimal target_agent.py
    (gen1 / "target_agent.py").write_text("print('hello')\n")

    return tmp_path


@pytest.fixture
def context_mgr(run_dir):
    config = {
        "task_dir": "./tasks/test-task",
        "meta_model": "haiku",
        "task_model": "haiku",
        "agent_impl": "claude",
        "max_gen": 3,
    }
    mgr = ContextManager(str(run_dir), config)
    mgr.initialize()
    return mgr


def test_initialize_creates_context_md(context_mgr, run_dir):
    ctx = run_dir / "context.md"
    assert ctx.is_file()
    content = ctx.read_text()
    assert "Run Context" in content
    assert "haiku" in content


def test_add_generation(context_mgr, run_dir):
    gen_dir = run_dir / "gen_1"

    context_mgr.add_generation(
        gen_num=1,
        gen_data={
            "success": True,
            "timestamp": "2025-01-01 00:00:00",
            "duration": 10.5,
            "agent_path": str(gen_dir / "target_agent.py"),
            "gen_dir": str(gen_dir),
            "improvement_path": None,
            "execution_type": "Single",
        },
    )

    content = (run_dir / "context.md").read_text()
    assert "Generation 1" in content
    assert "SUCCESS" in content


def test_add_generation_with_results_json(context_mgr, run_dir):
    gen_dir = run_dir / "gen_1"
    results = {"accuracy": 0.85, "n_correct": 170, "n_total": 200}
    (gen_dir / "results.json").write_text(json.dumps(results))

    context_mgr.add_generation(
        gen_num=1,
        gen_data={
            "success": True,
            "timestamp": "2025-01-01 00:00:00",
            "duration": 5.0,
            "agent_path": str(gen_dir / "target_agent.py"),
            "gen_dir": str(gen_dir),
            "improvement_path": None,
            "execution_type": "Single",
        },
    )

    content = (run_dir / "context.md").read_text()
    assert "0.85" in content


def test_finalize_with_metrics(context_mgr, run_dir):
    gen1 = run_dir / "gen_1"
    (gen1 / "results.json").write_text(json.dumps({"accuracy": 0.80}))

    context_mgr.add_generation(
        gen_num=1,
        gen_data={
            "success": True,
            "timestamp": "2025-01-01 00:00:00",
            "duration": 5.0,
            "agent_path": str(gen1 / "target_agent.py"),
            "gen_dir": str(gen1),
            "improvement_path": None,
            "execution_type": "Single",
        },
    )

    context_mgr.finalize()
    content = (run_dir / "context.md").read_text()
    assert "Summary Statistics" in content


@pytest.mark.usefixtures("run_dir")
@patch("sia.context_manager.ContextManager._generate_llm_summary", return_value=None)
def test_multiple_generations_track_deltas(mock_llm, context_mgr, run_dir):
    # Gen 1
    gen1 = run_dir / "gen_1"
    (gen1 / "results.json").write_text(json.dumps({"accuracy": 0.70}))

    context_mgr.add_generation(
        gen_num=1,
        gen_data={
            "success": True,
            "timestamp": "2025-01-01 00:00:00",
            "duration": 5.0,
            "agent_path": str(gen1 / "target_agent.py"),
            "gen_dir": str(gen1),
            "improvement_path": None,
            "execution_type": "Single",
        },
    )

    # Gen 2
    gen2 = run_dir / "gen_2"
    gen2.mkdir()
    (gen2 / "target_agent.py").write_text("print('improved')\nimport os\n")
    (gen2 / "results.json").write_text(json.dumps({"accuracy": 0.85}))
    (gen2 / "improvement.md").write_text("## Changes\n- Added better error handling\n- Improved prompt structure\n")

    context_mgr.add_generation(
        gen_num=2,
        gen_data={
            "success": True,
            "timestamp": "2025-01-01 00:01:00",
            "duration": 8.0,
            "agent_path": str(gen2 / "target_agent.py"),
            "gen_dir": str(gen2),
            "improvement_path": str(gen2 / "improvement.md"),
            "execution_type": "Single",
        },
    )

    content = (run_dir / "context.md").read_text()
    assert "Generation 2" in content
    assert "Modified by feedback agent" in content


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_feedback_context_golden.py =====

"""Characterization: lock the execution_status / execution_section text built for
the feedback prompt across the success/failure x single/multi x results matrix.
"""

import json

from golden_master import assert_golden, normalize_paths

from sia.orchestrator import TaskFiles, _build_feedback_context

TASK_FILES = TaskFiles("desc", "ref", {}, "# Task")


def _snapshot(gen_dir, stdout_log_file, status, section) -> str:
    text = "===== EXECUTION STATUS =====\n" + status + "\n===== EXECUTION SECTION =====\n" + section
    return normalize_paths(text, {str(gen_dir): "<GEN>", str(stdout_log_file): "<LOG>"})


def test_success_single_with_results(tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    (gen_dir / "agent_execution.json").write_text(json.dumps([{"role": "user", "content": "solve it"}]))
    (gen_dir / "results.json").write_text(json.dumps({"accuracy": 0.9, "correct": 9, "total": 10}))
    stdout_log = str(gen_dir / "target_agent_stdout.log")

    status, section = _build_feedback_context(
        current_gen=1,
        gen_dir=str(gen_dir),
        dataset_dir="/data/public",
        target_agent_success=True,
        target_agent_error_msg="",
        target_agent_stdout="line1\nline2\nline3\n",
        target_agent_stderr="",
        stdout_log_file=stdout_log,
        task_files=TASK_FILES,
    )
    assert_golden("feedback_context_success_single.txt", _snapshot(gen_dir, stdout_log, status, section))


def test_failure_single_no_results(tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    (gen_dir / "agent_execution.json").write_text(json.dumps([{"role": "user", "content": "attempt"}]))
    stdout_log = str(gen_dir / "target_agent_stdout.log")

    status, section = _build_feedback_context(
        current_gen=1,
        gen_dir=str(gen_dir),
        dataset_dir="/data/public",
        target_agent_success=False,
        target_agent_error_msg="Target agent failed with exit code 1",
        target_agent_stdout="boot\nrunning\ncrash\n",
        target_agent_stderr="Traceback: boom",
        stdout_log_file=stdout_log,
        task_files=TASK_FILES,
    )
    assert_golden("feedback_context_failure_single.txt", _snapshot(gen_dir, stdout_log, status, section))


def test_success_multi_with_results(tmp_path):
    gen_dir = tmp_path / "gen_1"
    exec_dir = gen_dir / "agent_execution"
    exec_dir.mkdir(parents=True)
    for i in range(2):
        (exec_dir / f"execution_q{i}.json").write_text(json.dumps([{"role": "user", "content": f"q{i}"}]))
    (gen_dir / "results.json").write_text(json.dumps({"accuracy": 0.8}))
    stdout_log = str(gen_dir / "target_agent_stdout.log")

    status, section = _build_feedback_context(
        current_gen=1,
        gen_dir=str(gen_dir),
        dataset_dir="/data/public",
        target_agent_success=True,
        target_agent_error_msg="",
        target_agent_stdout="processing q0\nprocessing q1\ndone\n",
        target_agent_stderr="",
        stdout_log_file=stdout_log,
        task_files=TASK_FILES,
    )
    assert_golden("feedback_context_success_multi.txt", _snapshot(gen_dir, stdout_log, status, section))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_generation_loop.py =====

"""Integration tests for generation loop with mocked agents."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from sia.config import Config
from sia.context_manager import ContextManager
from sia.orchestrator import (
    RunSetup,
    TaskFiles,
    _run_target_agent,
    run_generation,
)
from sia.profiles import load_meta_agent_profile, load_target_agent_profile

DEFAULT_META_PROFILE = load_meta_agent_profile("default-meta")
DEFAULT_TARGET_PROFILE = load_target_agent_profile("default-target")


def _make_task_files(tmp_path):
    """Create minimal task structure with all required files."""
    task_dir = tmp_path / "task"
    shared_dir = task_dir / "_shared"
    ref_dir = task_dir / "reference"
    pub_dir = task_dir / "data" / "public"

    for d in (shared_dir, ref_dir, pub_dir):
        d.mkdir(parents=True)

    (ref_dir / "SAMPLE_TASK_DESCRIPTIONS.md").write_text("Sample task description text.")
    (ref_dir / "reference_target_agent.py").write_text("print('ref agent')")
    (shared_dir / "sample_agent_execution.json").write_text(json.dumps([{"role": "user"}]))
    (pub_dir / "task.md").write_text("# Test task\nSolve the problem.")
    return task_dir, shared_dir


def _make_run_setup(tmp_path, task_dir):
    """Create a RunSetup with initialized context manager."""
    run_dir = tmp_path / "runs" / "run_1"
    gen1 = run_dir / "gen_1"
    gen1.mkdir(parents=True)
    (gen1 / "target_agent.py").write_text("print('agent')\n")

    context_mgr = ContextManager(
        str(run_dir),
        {
            "task_dir": str(task_dir),
            "meta_model": "haiku",
            "task_model": "haiku",
            "agent_impl": "claude",
            "max_gen": 1,
        },
    )
    context_mgr.initialize()

    return RunSetup(
        run_directory=str(run_dir),
        meta_agent_working_directory=str(gen1),
        venv_dir=str(tmp_path / "venv"),
        context_mgr=context_mgr,
    )


@patch("sia.orchestrator.subprocess.Popen")
def test_run_target_agent_success(mock_popen_cls, tmp_path):
    """_run_target_agent with sandbox=none uses standard Popen path."""
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    stdout_log = str(gen_dir / "stdout.log")
    (gen_dir / "target_agent.py").write_text("print('ok')")

    # Mock Popen to simulate a process that writes one line then exits 0
    mock_process = MagicMock()
    mock_process.stdout = iter(["line1\n"])
    mock_process.wait.return_value = 0
    mock_popen_cls.return_value = mock_process

    success, _stdout, _stderr, err = _run_target_agent(
        venv_dir="/fake/venv",
        target_agent_path=str(gen_dir / "target_agent.py"),
        abs_dataset_dir="/data",
        gen_dir=str(gen_dir),
        stdout_log_file=stdout_log,
        sandbox="none",
        env_config=Config(),
    )

    assert success is True
    assert err == ""
    mock_popen_cls.assert_called_once()
    # Verify no Docker args in the command
    cmd = mock_popen_cls.call_args[0][0]
    assert "docker" not in cmd


@patch("sia.orchestrator.subprocess.Popen")
def test_run_target_agent_failure(mock_popen_cls, tmp_path):
    """_run_target_agent returns (False, ...) on non-zero exit."""
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    stdout_log = str(gen_dir / "stdout.log")
    (gen_dir / "target_agent.py").write_text("raise SystemExit(1)")

    mock_process = MagicMock()
    mock_process.stdout = iter(["error\n"])
    mock_process.wait.return_value = 1
    mock_popen_cls.return_value = mock_process

    success, _stdout, _stderr, err = _run_target_agent(
        venv_dir="/fake/venv",
        target_agent_path=str(gen_dir / "target_agent.py"),
        abs_dataset_dir="/data",
        gen_dir=str(gen_dir),
        stdout_log_file=stdout_log,
        sandbox="none",
        env_config=Config(),
    )

    assert success is False
    assert "exit code 1" in err


@patch("sia.orchestrator._run_feedback_agent")
@patch("sia.orchestrator._run_target_agent")
def test_single_generation_creates_context(mock_run_ta, mock_run_fb, tmp_path):
    """run_generation with max_gen=1 creates context.md entry."""
    task_dir, _shared_dir = _make_task_files(tmp_path)
    run_setup = _make_run_setup(tmp_path, task_dir)

    mock_run_ta.return_value = (True, "output", "", "")

    task_files = TaskFiles(
        sample_task_descriptions="desc",
        reference_target_agent_py="ref",
        sample_agent_execution={},
        task_md="# Task",
    )

    run_generation(
        current_gen=1,
        max_gen=1,
        run_setup=run_setup,
        task_files=task_files,
        abs_dataset_dir=str(task_dir / "data" / "public"),
        dataset_dir=str(task_dir / "data" / "public"),
        meta_profile=DEFAULT_META_PROFILE,
        sandbox="none",
        env_config=Config(),
        task_model=DEFAULT_TARGET_PROFILE.model,
        target_provider=DEFAULT_TARGET_PROFILE.provider,
    )

    # Verify context.md was updated
    ctx = (Path(run_setup.run_directory) / "context.md").read_text()
    assert "Generation 1" in ctx
    assert "SUCCESS" in ctx

    # Feedback agent should NOT be called (last generation)
    mock_run_fb.assert_not_called()


@patch("sia.orchestrator._run_feedback_agent")
@patch("sia.orchestrator._run_target_agent")
def test_run_generation_directory_structure(mock_run_ta, mock_run_fb, tmp_path):
    """Verify gen directory structure is preserved after run."""
    task_dir, _ = _make_task_files(tmp_path)
    run_setup = _make_run_setup(tmp_path, task_dir)

    mock_run_ta.return_value = (True, "output", "", "")

    run_generation(
        current_gen=1,
        max_gen=1,
        run_setup=run_setup,
        task_files=TaskFiles("d", "r", {}, "# T"),
        abs_dataset_dir="/data",
        dataset_dir="/data",
        meta_profile=DEFAULT_META_PROFILE,
        sandbox="none",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_load_execution_formats.py =====

"""Characterization: lock the exact return contract of load_agent_execution.

Complements the looser assertions in test_orchestrator_helpers.py by pinning the
precise dict shapes the feedback path depends on.
"""

import json

from sia.orchestrator import load_agent_execution


def test_missing_returns_exact_error(tmp_path):
    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi is False
    assert data == {"error": "Execution log not found"}


def test_empty_multi_folder_returns_exact_error(tmp_path):
    (tmp_path / "agent_execution").mkdir()
    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi is True
    assert data == {"error": "Empty execution folder", "type": "multi-trajectory"}


def test_malformed_single_returns_partial_preview(tmp_path):
    (tmp_path / "agent_execution.json").write_text("{not valid json")
    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi is False
    assert data["error"] == "Parse error"
    assert data["raw_preview"] == "{not valid json"
    assert data["file_size"] == len("{not valid json")
    assert "parse_error" in data


def test_multi_trajectory_shape(tmp_path):
    exec_dir = tmp_path / "agent_execution"
    exec_dir.mkdir()
    for i in range(3):
        (exec_dir / f"execution_q{i}.json").write_text(json.dumps([{"role": "user", "content": f"q{i}"}]))
    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi is True
    assert data["type"] == "multi-trajectory"
    assert data["count"] == 3
    assert [t[0]["content"] for t in data["trajectories"]] == ["q0", "q1", "q2"]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_orchestrator_helpers.py =====

"""Unit tests for orchestrator helper functions."""

import json

from sia.orchestrator import load_agent_execution


def test_load_single_trajectory(tmp_path):
    trajectory = [{"role": "user", "content": "hello"}]
    (tmp_path / "agent_execution.json").write_text(json.dumps(trajectory))

    data, is_multi = load_agent_execution(str(tmp_path))
    assert not is_multi
    assert isinstance(data, list)
    assert data[0]["role"] == "user"


def test_load_multi_trajectory(tmp_path):
    exec_dir = tmp_path / "agent_execution"
    exec_dir.mkdir()

    for i in range(3):
        traj = [{"role": "user", "content": f"question {i}"}]
        (exec_dir / f"execution_q{i}.json").write_text(json.dumps(traj))

    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi
    assert data["count"] == 3
    assert len(data["trajectories"]) == 3


def test_load_missing_execution(tmp_path):
    data, _is_multi = load_agent_execution(str(tmp_path))
    assert "error" in data


def test_load_malformed_json(tmp_path):
    (tmp_path / "agent_execution.json").write_text("{not valid json")

    data, is_multi = load_agent_execution(str(tmp_path))
    assert not is_multi
    assert "error" in data or "raw_preview" in data


def test_load_empty_multi_trajectory_folder(tmp_path):
    (tmp_path / "agent_execution").mkdir()

    data, is_multi = load_agent_execution(str(tmp_path))
    assert is_multi
    assert "error" in data


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_profiles.py =====

"""Tests for the JSON-defined agent-profile registry."""

import json

import pytest

from sia.profiles import (
    MetaAgentProfile,
    TargetAgentProfile,
    available_profiles,
    load_meta_agent_profile,
    load_target_agent_profile,
)


def test_bundled_profiles_present():
    assert set(available_profiles()) >= {"default-meta", "default-target", "kimi-nebius-target"}


def test_default_meta_profile():
    p = load_meta_agent_profile("default-meta")
    assert isinstance(p, MetaAgentProfile)
    assert p.profile_id == "default-meta"
    assert p.agent_impl == "claude"
    assert p.model == "haiku"
    assert p.provider.provider_id == "anthropic"


def test_default_target_profile_uses_default_reference():
    p = load_target_agent_profile("default-target")
    assert isinstance(p, TargetAgentProfile)
    assert p.agent_reference.kind == "default"
    assert p.model == "claude-haiku-4-5-20251001"
    assert p.provider.client_kind == "anthropic"


def test_kimi_nebius_target_profile_resolves_provider():
    p = load_target_agent_profile("kimi-nebius-target")
    assert p.agent_reference.kind == "default"
    assert p.model == "moonshotai/Kimi-K2.6"
    assert p.provider.provider_id == "nebius"
    assert p.provider.base_url is not None
    assert p.provider.base_url.endswith("nebius.com/v1/")


def test_unknown_profile_raises():
    with pytest.raises(SystemExit):
        load_meta_agent_profile("nope")


def _write_profile(tmp_path, data):
    path = tmp_path / "p.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_invalid_agent_impl_raises(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "agent_impl": "bogus", "model": "m", "provider_id": "anthropic"}
    )
    with pytest.raises(SystemExit):
        load_meta_agent_profile(path)


def test_claude_agent_impl_requires_anthropic_provider(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "agent_impl": "claude", "model": "m", "provider_id": "nebius"}
    )
    with pytest.raises(SystemExit):
        load_meta_agent_profile(path)


def test_openhands_agent_impl_allows_non_anthropic_provider(tmp_path):
    path = _write_profile(
        tmp_path, {"profile_id": "p", "name": "p", "agent_impl": "openhands", "model": "m", "provider_id": "nebius"}
    )
    profile = load_meta_agent_profile(path)
    assert profile.agent_impl == "openhands"
    assert profile.provider.provider_id == "nebius"


def test_target_profile_defaults_reference_when_omitted(tmp_path):
    path = _write_profile(tmp_path, {"profile_id": "p", "name": "p", "model": "m", "provider_id": "anthropic"})
    profile = load_target_agent_profile(path)
    assert profile.agent_reference.kind == "default"


def test_target_profile_file_reference(tmp_path):
    (tmp_path / "my_agent.py").write_text("print('hi')")
    path = _write_profile(
        tmp_path,
        {
            "profile_id": "p",
            "name": "p",
            "model": "m",
            "provider_id": "anthropic",
            "agent_reference": {"source": "./my_agent.py"},
        },
    )
    profile = load_target_agent_profile(path)
    assert profile.agent_reference.kind == "file"
    assert profile.agent_reference.source is not None
    assert profile.agent_reference.source.name == "my_agent.py"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_prompts_snapshot.py =====

"""Characterization: lock the exact text of the meta and feedback prompts.

These prompts are the product's core business logic and are written verbatim to
disk (meta_agent_prompt.txt / feedback_agent_prompt.txt). The refactor must not
change a single character of them on the default path.
"""

from golden_master import assert_golden

from sia.orchestrator import TaskFiles, build_feedback_prompt, build_meta_prompt
from sia.providers import load_provider

# Fixed, path-free inputs so the prompt text is fully deterministic.
TASK_FILES = TaskFiles(
    sample_task_descriptions="SAMPLE DESCRIPTIONS BODY",
    reference_target_agent_py="print('reference target agent')",
    sample_agent_execution={"messages": [{"role": "user", "content": "hi"}]},
    task_md="# Example Task\nSolve the example problem precisely.",
)


def test_meta_prompt_golden():
    prompt = build_meta_prompt(
        task_files=TASK_FILES,
        task_model="claude-haiku-4-5-20251001",
        working_dir="/WORK/run_1/gen_1",
    )
    assert_golden("meta_prompt.txt", prompt)


def test_meta_prompt_anthropic_provider_is_byte_identical():
    """An explicit anthropic provider must not change the default prompt text."""
    with_provider = build_meta_prompt(
        task_files=TASK_FILES,
        task_model="claude-haiku-4-5-20251001",
        working_dir="/WORK/run_1/gen_1",
        provider=load_provider("anthropic"),
    )
    assert_golden("meta_prompt.txt", with_provider)


def test_meta_prompt_openai_provider_golden():
    """OpenAI-compatible providers prepend the client-setup block (new golden)."""
    prompt = build_meta_prompt(
        task_files=TASK_FILES,
        task_model="moonshotai/Kimi-K2.6",
        working_dir="/WORK/run_1/gen_1",
        provider=load_provider("nebius"),
    )
    assert_golden("meta_prompt_openai.txt", prompt)


def test_feedback_prompt_golden():
    prompt = build_feedback_prompt(
        current_gen=2,
        max_gen=3,
        task_files=TASK_FILES,
        agent_py="print('current target agent gen 2')",
        task="# Example Task\nSolve the example problem precisely.",
        execution_status="SUCCESS: example status block",
        execution_section="EXECUTION SECTION BODY",
        run_dir="/RUN/run_1",
        next_gen_dir="/RUN/run_1/gen_3",
        previous_gens="1",
        task_model="claude-haiku-4-5-20251001",
    )
    assert_golden("feedback_prompt.txt", prompt)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_providers.py =====

"""Tests for the JSON-defined provider registry."""

import json

import pytest

from sia.providers import Provider, available_providers, load_provider


def test_bundled_providers_present():
    assert set(available_providers()) >= {"anthropic", "gemini", "openai", "together", "nebius"}


def test_load_anthropic_provider():
    p = load_provider("anthropic")
    assert isinstance(p, Provider)
    assert p.provider_id == "anthropic"
    assert p.client_kind == "anthropic"
    assert p.base_url is None
    assert p.api_key_env == "ANTHROPIC_API_KEY"


def test_load_nebius_provider():
    p = load_provider("nebius")
    assert p.client_kind == "openai"
    assert p.base_url == "https://api.tokenfactory.us-central1.nebius.com/v1/"
    assert p.api_key_env == "NEBIUS_API_KEY"


def test_unknown_provider_name_raises():
    with pytest.raises(SystemExit):
        load_provider("does-not-exist")


def test_load_provider_from_path(tmp_path):
    path = tmp_path / "custom.json"
    path.write_text(
        json.dumps(
            {
                "provider_id": "custom",
                "name": "Custom",
                "client_kind": "openai",
                "base_url": "https://x/v1",
                "api_key_env": "X_KEY",
            }
        )
    )
    p = load_provider(str(path))
    assert p.provider_id == "custom"
    assert p.base_url == "https://x/v1"


def test_missing_path_raises():
    with pytest.raises(SystemExit):
        load_provider("/no/such/provider.json")


def test_invalid_client_kind_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"provider_id": "bad", "name": "Bad", "client_kind": "mystery", "api_key_env": "K"}))
    with pytest.raises(SystemExit):
        load_provider(str(path))


def test_user_dir_overrides_bundled(tmp_path, monkeypatch):
    providers_dir = tmp_path / "providers"
    providers_dir.mkdir()
    (providers_dir / "nebius.json").write_text(
        json.dumps(
            {
                "provider_id": "nebius",
                "name": "nebius",
                "client_kind": "openai",
                "base_url": "https://override/v1",
                "api_key_env": "NEBIUS_API_KEY",
            }
        )
    )
    monkeypatch.setenv("SIA_PROVIDERS_DIR", str(providers_dir))
    assert load_provider("nebius").base_url == "https://override/v1"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_run_evaluation.py =====

"""Tests for orchestrator.run_evaluation with mocked subprocess."""

import json
from unittest.mock import MagicMock, patch

from sia.orchestrator import run_evaluation


def test_skipped_when_no_evaluate_py(tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    task_dir = tmp_path / "task"
    task_dir.mkdir()

    result = run_evaluation(str(gen_dir), str(task_dir), "/fake/venv")
    assert result["status"] == "skipped"


def _make_task_with_eval(task_dir):
    """Create a minimal task dir with evaluate.py in data/public/."""
    pub = task_dir / "data" / "public"
    pub.mkdir(parents=True)
    (pub / "evaluate.py").write_text("pass")


@patch("sia.orchestrator.subprocess.run")
def test_success_when_results_json_created(mock_run, tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    (gen_dir / "results.json").write_text(json.dumps({"accuracy": 0.9}))
    _make_task_with_eval(tmp_path / "task")

    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    result = run_evaluation(str(gen_dir), str(tmp_path / "task"), "/fake/venv")
    assert result["status"] == "success"
    mock_run.assert_called_once()


@patch("sia.orchestrator.subprocess.run")
def test_error_on_nonzero_exit(mock_run, tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    _make_task_with_eval(tmp_path / "task")

    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="traceback")

    result = run_evaluation(str(gen_dir), str(tmp_path / "task"), "/fake/venv")
    assert result["status"] == "error"
    assert "code 1" in result["reason"]


@patch("sia.orchestrator.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(cmd="eval", timeout=600))
def test_timeout_handled(mock_run, tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    _make_task_with_eval(tmp_path / "task")

    result = run_evaluation(str(gen_dir), str(tmp_path / "task"), "/fake/venv")
    assert result["status"] == "error"
    assert "timed out" in result["reason"]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_run_evaluation_outcomes.py =====

"""Characterization: lock the run_evaluation 'warning' outcome (results.json not
created). The skipped/success/error/timeout outcomes are covered in
test_run_evaluation.py.
"""

from unittest.mock import MagicMock, patch

from sia.orchestrator import run_evaluation


def _make_task_with_eval(task_dir):
    pub = task_dir / "data" / "public"
    pub.mkdir(parents=True)
    (pub / "evaluate.py").write_text("pass")


@patch("sia.orchestrator.subprocess.run")
def test_warning_when_results_json_missing(mock_run, tmp_path):
    gen_dir = tmp_path / "gen_1"
    gen_dir.mkdir()
    _make_task_with_eval(tmp_path / "task")

    # exit 0 but evaluate.py never wrote results.json
    mock_run.return_value = MagicMock(returncode=0, stdout="done, no results written", stderr="")

    result = run_evaluation(str(gen_dir), str(tmp_path / "task"), "/fake/venv")
    assert result["status"] == "warning"
    assert result["reason"] == "results.json not created by evaluate.py"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_sandbox.py =====

"""Tests for Docker sandbox execution in orchestrator."""

from unittest.mock import MagicMock, patch

from sia.config import Config
from sia.orchestrator import _run_target_agent, _run_target_agent_sandboxed


@patch("sia.orchestrator.subprocess.Popen")
def test_docker_command_has_network_none(mock_popen):
    """Sandboxed run must include --network none."""
    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    _run_target_agent_sandboxed(
        python_exec="/venv/bin/python",
        target_agent_path="/work/target_agent.py",
        dataset_dir="/data",
        working_dir="/work",
        stdout_log_file="/dev/null",
        config=Config(),
    )

    cmd = mock_popen.call_args[0][0]
    assert "--network" in cmd
    idx = cmd.index("--network")
    assert cmd[idx + 1] == "none"


@patch("sia.orchestrator.subprocess.Popen")
def test_docker_dataset_mounted_readonly(mock_popen):
    """Dataset mount must have :ro suffix."""
    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    _run_target_agent_sandboxed(
        python_exec="/venv/bin/python",
        target_agent_path="/work/target_agent.py",
        dataset_dir="/data",
        working_dir="/work",
        stdout_log_file="/dev/null",
        config=Config(),
    )

    cmd = mock_popen.call_args[0][0]
    # Find the -v flag for dataset
    vol_idx = cmd.index("-v")
    dataset_vol = cmd[vol_idx + 1]
    assert ":/data:ro" in dataset_vol


@patch("sia.orchestrator.subprocess.Popen")
def test_docker_working_dir_mounted_readwrite(mock_popen):
    """Working dir mount must have :rw suffix."""
    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    _run_target_agent_sandboxed(
        python_exec="/venv/bin/python",
        target_agent_path="/work/target_agent.py",
        dataset_dir="/data",
        working_dir="/work",
        stdout_log_file="/dev/null",
        config=Config(),
    )

    cmd = mock_popen.call_args[0][0]
    # Find all -v flags
    vol_indices = [i for i, x in enumerate(cmd) if x == "-v"]
    work_vol = cmd[vol_indices[1] + 1]
    assert ":/work:rw" in work_vol


@patch("sia.orchestrator.subprocess.Popen")
def test_docker_image_and_resource_limits(mock_popen):
    """Docker command uses image and resource limits from Config."""
    mock_process = MagicMock()
    mock_process.stdout = iter([])
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    cfg = Config()
    _run_target_agent_sandboxed(
        python_exec="/venv/bin/python",
        target_agent_path="/work/target_agent.py",
        dataset_dir="/data",
        working_dir="/work",
        stdout_log_file="/dev/null",
        config=cfg,
    )

    cmd = mock_popen.call_args[0][0]
    assert cfg.DOCKER_IMAGE in cmd
    assert "--memory" in cmd
    mem_idx = cmd.index("--memory")
    assert cmd[mem_idx + 1] == cfg.DOCKER_MEMORY_LIMIT
    # CPU limit in --cpus=N format
    cpu_args = [a for a in cmd if a.startswith("--cpus=")]
    assert len(cpu_args) == 1
    assert str(cfg.DOCKER_CPU_LIMIT) in cpu_args[0]


@patch("sia.orchestrator.subprocess.Popen")
def test_sandbox_none_uses_standard_popen(mock_popen):
    """sandbox='none' bypasses Docker entirely."""
    gen_dir = "/tmp/gen"
    mock_process = MagicMock()
    mock_process.stdout = iter(["line\n"])
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name

    _run_target_agent(
        venv_dir="/fake/venv",
        target_agent_path=f"{gen_dir}/target_agent.py",
        abs_dataset_dir="/data",
        gen_dir=gen_dir,
        stdout_log_file=log_path,
        sandbox="none",
        env_config=Config(),
    )

    cmd = mock_popen.call_args[0][0]
    assert cmd[0] == "/fake/venv/bin/python"
    assert "docker" not in cmd[0]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_size_limits.py =====

"""Tests for file size limit enforcement in context_manager."""

import json

from sia.context_manager import _safe_load_json, _safe_read_file


def test_read_file_under_limit(tmp_path):
    f = tmp_path / "small.txt"
    f.write_text("hello world")
    result = _safe_read_file(str(f), max_bytes=1024)
    assert result == "hello world"


def test_read_file_over_limit(tmp_path):
    f = tmp_path / "big.txt"
    f.write_text("x" * 2000)
    result = _safe_read_file(str(f), max_bytes=1000)
    assert result is None


def test_read_file_at_exact_limit(tmp_path):
    content = "a" * 1000
    f = tmp_path / "exact.txt"
    f.write_text(content)
    # File size equals limit (not >), should succeed
    result = _safe_read_file(str(f), max_bytes=1000)
    assert result == content


def test_load_json_under_limit(tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"accuracy": 0.95}))
    result = _safe_load_json(str(f), max_bytes=4096)
    assert result == {"accuracy": 0.95}


def test_load_json_over_limit(tmp_path):
    data = {"key": "x" * 5000}
    f = tmp_path / "big.json"
    f.write_text(json.dumps(data))
    result = _safe_load_json(str(f), max_bytes=1000)
    assert result is None


def test_load_json_nonexistent(tmp_path):
    result = _safe_load_json(str(tmp_path / "nope.json"), max_bytes=4096)
    assert result is None


def test_load_json_invalid_json(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json")
    result = _safe_load_json(str(f), max_bytes=4096)
    assert result is None


def test_read_file_nonexistent(tmp_path):
    result = _safe_read_file(str(tmp_path / "missing.txt"), max_bytes=4096)
    assert result is None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_task_structure.py =====

"""Validate that all task directories have the required structure."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
TASKS_DIR = REPO_ROOT / "sia" / "tasks"

# Directories that aren't actual tasks
SKIP_DIRS = {"_shared"}


def _task_dirs():
    """Yield task directory paths (skip _shared, __pycache__, and hidden dirs)."""
    for p in sorted(TASKS_DIR.iterdir()):
        if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith((".", "_")):
            yield p


@pytest.fixture(params=list(_task_dirs()), ids=lambda p: p.name)
def task_dir(request):
    return request.param


def test_task_has_public_data(task_dir):
    public = task_dir / "data" / "public"
    assert public.is_dir(), f"{task_dir.name}: missing data/public/"


def test_task_has_task_md(task_dir):
    task_md = task_dir / "data" / "public" / "task.md"
    assert task_md.is_file(), f"{task_dir.name}: missing data/public/task.md"
    content = task_md.read_text()
    assert len(content) > 50, f"{task_dir.name}: task.md is too short"


def test_task_has_reference_dir(task_dir):
    ref = task_dir / "reference"
    assert ref.is_dir(), f"{task_dir.name}: missing reference/"


def test_task_has_reference_agent(task_dir):
    agent = task_dir / "reference" / "reference_target_agent.py"
    assert agent.is_file(), f"{task_dir.name}: missing reference/reference_target_agent.py"


def test_task_has_sample_descriptions(task_dir):
    desc = task_dir / "reference" / "SAMPLE_TASK_DESCRIPTIONS.md"
    assert desc.is_file(), f"{task_dir.name}: missing reference/SAMPLE_TASK_DESCRIPTIONS.md"


def test_shared_sample_execution_exists():
    sample = TASKS_DIR / "_shared" / "sample_agent_execution.json"
    assert sample.is_file(), "Missing tasks/_shared/sample_agent_execution.json"
    data = json.loads(sample.read_text())
    assert isinstance(data, (list, dict)), "sample_agent_execution.json must be valid JSON"


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/test_web.py =====

"""Tests for the runs-visualizer data layer and HTTP API."""

import json
from pathlib import Path

import pytest

from sia.web import runs as rd


@pytest.fixture
def runs_root(tmp_path: Path) -> Path:
    """A minimal but realistic runs/ tree: one run, two generations."""
    root = tmp_path / "runs"
    gen1 = root / "run_7" / "gen_1"
    gen2 = root / "run_7" / "gen_2"
    (gen1 / "agent_execution").mkdir(parents=True)
    gen2.mkdir(parents=True)

    (root / "run_7" / "context.md").write_text(
        "# Run Context: run_7\n\n"
        "**Task**: /tasks/gpqa\n"
        "**Meta Model**: kimi\n"
        "**Task Model**: haiku\n"
        "**Agent impl**: openhands\n"
        "**Started**: 2026-06-05 13:31:32\n"
        "**Max Generations**: 3\n\n"
        "---\n\n## Generation 1\n**Status**: ok\n",
        encoding="utf-8",
    )

    (gen1 / "target_agent.py").write_text("print('hello')\n", encoding="utf-8")
    (gen1 / "meta_agent_prompt.txt").write_text("meta prompt body", encoding="utf-8")
    (gen1 / "evaluation_results.json").write_text(
        json.dumps(
            {
                "total_questions": 4,
                "correct": 2,
                "incorrect": 2,
                "accuracy": 0.5,
                "accuracy_percent": 50.0,
                "details": [
                    {"question_id": 1, "domain": "Physics", "is_correct": True},
                    {"question_id": 2, "domain": "Physics", "is_correct": False},
                    {"question_id": 3, "domain": "Biology", "is_correct": True},
                    {"question_id": 4, "domain": "Biology", "is_correct": False},
                ],
            }
        ),
        encoding="utf-8",
    )
    (gen1 / "agent_execution" / "execution_q1.json").write_text(
        json.dumps(
            [
                {"role": "system", "content": [{"type": "text", "text": "You are an expert."}]},
                {"role": "user", "content": "Question 1?"},
                {"role": "assistant", "content": [{"type": "text", "text": "Answer: A"}]},
            ]
        ),
        encoding="utf-8",
    )

    (gen2 / "improvement.md").write_text("# Plan\n- do better\n", encoding="utf-8")
    return root


def test_list_runs_summary(runs_root):
    runs = rd.list_runs(runs_root)
    assert len(runs) == 1
    r = runs[0]
    assert r.name == "run_7"
    assert r.agent_impl == "openhands"
    assert r.task_model == "haiku"
    assert r.max_generations == 3
    assert r.num_generations == 2
    assert r.best_accuracy_percent == 50.0


def test_get_run_detail_and_domains(runs_root):
    detail = rd.get_run(runs_root, "run_7")
    assert detail is not None
    assert detail.context_md is not None
    assert detail.context_md.startswith("# Run Context")
    gen1 = next(g for g in detail.generations if g.name == "gen_1")
    assert gen1.eval is not None
    assert gen1.eval.accuracy_percent == 50.0
    assert "target_agent" in gen1.artifacts
    assert "meta_prompt" in gen1.artifacts
    assert gen1.trajectories == [1]
    domains = {d.domain: d for d in gen1.domains}
    assert domains["Physics"].correct == 1 and domains["Physics"].total == 2
    assert domains["Biology"].accuracy_percent == 50.0


def test_eval_details_and_artifacts(runs_root):
    details = rd.get_eval_details(runs_root, "run_7", "gen_1")
    assert details is not None and len(details) == 4
    assert rd.get_artifact_text(runs_root, "run_7", "gen_1", "target_agent") == "print('hello')\n"
    improvement = rd.get_artifact_text(runs_root, "run_7", "gen_2", "improvement")
    assert improvement is not None and improvement.startswith("# Plan")


def test_trajectory_normalization(runs_root):
    turns = rd.get_trajectory(runs_root, "run_7", "gen_1", 1)
    assert turns is not None
    assert [t["role"] for t in turns] == ["system", "user", "assistant"]
    assert turns[0]["text"] == "You are an expert."
    assert turns[1]["text"] == "Question 1?"
    assert turns[2]["text"] == "Answer: A"


def test_missing_lookups_return_none(runs_root):
    assert rd.get_run(runs_root, "run_999") is None
    assert rd.get_trajectory(runs_root, "run_7", "gen_1", 999) is None
    assert rd.get_artifact_text(runs_root, "run_7", "gen_1", "nope") is None


@pytest.mark.parametrize("evil", ["..", "../etc", "run_7/../run_7", "foo/bar", ".", "/abs"])
def test_path_traversal_is_blocked(runs_root, evil):
    assert rd.get_run(runs_root, evil) is None
    assert rd._resolve_gen(runs_root, evil, "gen_1") is None
    assert rd._resolve_gen(runs_root, "run_7", evil) is None


def test_api_endpoints(runs_root):
    from fastapi.testclient import TestClient

    from sia.web import create_app

    client = TestClient(create_app(runs_root))

    assert client.get("/api/runs").json()[0]["name"] == "run_7"
    assert client.get("/api/runs/run_7").json()["agent_impl"] == "openhands"
    assert len(client.get("/api/runs/run_7/gens/gen_1/eval").json()) == 4
    assert "hello" in client.get("/api/runs/run_7/gens/gen_1/artifact/target_agent").text
    assert client.get("/api/runs/run_7/gens/gen_1/trajectory/1").json()[0]["role"] == "system"
    assert client.get("/api/runs/run_404").status_code == 404
    assert client.get("/").status_code == 200


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/default-meta.json =====

{
  "profile_id": "default-meta",
  "name": "Default meta agent (Claude Haiku)",
  "agent_impl": "claude",
  "model": "haiku",
  "provider_id": "anthropic"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/default-target.json =====

{
  "profile_id": "default-target",
  "name": "Default target agent (Claude Haiku)",
  "model": "claude-haiku-4-5-20251001",
  "provider_id": "anthropic",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/gemini-meta.json =====

{
  "profile_id": "gemini-meta",
  "name": "Gemini 3.1 Pro meta agent (OpenHands)",
  "agent_impl": "openhands",
  "model": "gemini/gemini-3.1-pro-preview",
  "provider_id": "gemini"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/gptoss-nebius-target.json =====

{
  "profile_id": "gptoss-nebius-target",
  "name": "GPT OSS 120B on Nebius",
  "model": "openai/gpt-oss-120b-fast",
  "provider_id": "nebius",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/gptoss-tinker-target.json =====

{
  "profile_id": "gptoss-tinker",
  "name": "GPT OSS 120B on Tinker",
  "model": "openai/gpt-oss-120b",
  "provider_id": "tinker",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/kimi-nebius-meta.json =====

{
  "profile_id": "kimi-nebius-meta",
  "name": "Kimi K2.6 on Nebius",
  "agent_impl": "openhands",
  "model": "moonshotai/Kimi-K2.6",
  "provider_id": "nebius"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/kimi-nebius-target.json =====

{
  "profile_id": "kimi-nebius-target",
  "name": "Kimi K2.6 on Nebius",
  "model": "moonshotai/Kimi-K2.6",
  "provider_id": "nebius",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/qwen-nebius-target.json =====

{
  "profile_id": "qwen-nebius-target",
  "name": "Qwen 80B on Nebius",
  "model": "Qwen/Qwen3-Next-80B-A3B-Thinking-fast",
  "provider_id": "nebius",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/profiles/qwen3-tinker-target.json =====

{
  "profile_id": "qwen3-tinker",
  "name": "Qwen3 4B Instruct on Tinker",
  "model": "Qwen/Qwen3-4B-Instruct-2507",
  "provider_id": "tinker",
  "agent_reference": "default"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/anthropic.json =====

{
  "provider_id": "anthropic",
  "name": "Anthropic",
  "client_kind": "anthropic",
  "base_url": null,
  "api_key_env": "ANTHROPIC_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/gemini.json =====

{
  "provider_id": "gemini",
  "name": "Google Gemini",
  "client_kind": "google",
  "base_url": null,
  "api_key_env": "GEMINI_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/nebius.json =====

{
  "provider_id": "nebius",
  "name": "Nebius Token Factory",
  "client_kind": "openai",
  "base_url": "https://api.tokenfactory.us-central1.nebius.com/v1/",
  "api_key_env": "NEBIUS_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/openai.json =====

{
  "provider_id": "openai",
  "name": "OpenAI",
  "client_kind": "openai",
  "base_url": "https://api.openai.com/v1",
  "api_key_env": "OPENAI_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/tinker.json =====

{
  "provider_id": "tinker",
  "name": "Tinker API",
  "client_kind": "openai",
  "base_url": "https://tinker.thinkingmachines.dev/services/tinker-prod/oai/api/v1",
  "api_key_env": "TINKER_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/defaults/providers/together.json =====

{
  "provider_id": "together",
  "name": "Together AI",
  "client_kind": "openai",
  "base_url": "https://api.together.ai/v1",
  "api_key_env": "TOGETHER_API_KEY"
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/_shared/sample_agent_execution.json =====

[
    {
      "role": "system",
      "content": [
        {
          "type": "text",
          "text": "You are a helpful financial assistant that can look up stock prices and provide market information."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is the stock price of AAPL?"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "I'll look up the current market data for Apple (AAPL) right now."
        }
      ],
      "tool_calls": [
        {
          "id": "call_98765",
          "type": "function",
          "function": {
            "name": "get_ticker_price",
            "arguments": "{\"symbol\": \"AAPL\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_98765",
      "content": "{\"price\": 185.20, \"currency\": \"USD\"}"
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "Apple (AAPL) is currently trading at $185.20 USD."
        }
      ]
    }
  ]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/data/private/diamond_questions.json =====

[
  {
    "id": 1,
    "domain": "Physics",
    "subdomain": "Physics (general)",
    "Question": "Two quantum states with energies E1 and E2 have a lifetime of 10^-9 sec and 10^-8 sec, respectively. We want to clearly distinguish these two energy levels. Which one of the following options could be their energy difference so that they can be clearly resolved?\n",
    "options": {
      "A": "10^-4 eV",
      "B": "10^-9 eV",
      "C": "10^-11 eV",
      "D": "10^-8 eV"
    },
    "correct_answer": "10^-4 eV",
    "correct_answer_letter": "A",
    "Explanation": "According to the uncertainty principle, Delta E* Delta t=hbar/2. Delta t is the lifetime and Delta E is the width of the energy level. With Delta t=10^-9 s==> Delta E1= 3.3 10^-7 ev. And Delta t=10^-11 s gives Delta E2=3.310^-8 eV.\nTherefore, the energy difference between the two states must be significantly greater than 10^-7 ev. So the answer is 10^-4 ev."
  },
  {
    "id": 2,
    "domain": "Chemistry",
    "subdomain": "Organic Chemistry",
    "Question": "trans-cinnamaldehyde was treated with methylmagnesium bromide, forming product 1.\n\n1 was treated with pyridinium chlorochromate, forming product 2.\n\n3 was treated with (dimethyl(oxo)-l6-sulfaneylidene)methane in DMSO at elevated temperature, forming product 3.\n\nhow many carbon atoms are there in product 3?",
    "options": {
      "A": "11",
      "B": "14",
      "C": "12",
      "D": "10"
    },
    "correct_answer": "11",
    "correct_answer_letter": "A",
    "Explanation": "trans-cinnamaldehyde was treated with methylmagnesium bromide, forming (E)-4-phenylbut-3-en-2-ol.\n(E)-4-phenylbut-3-en-2-ol was treated with pyridinium chlorochromate, forming (E)-4-phenylbut-3-en-2-one.\n\n(E)-4-phenylbut-3-en-2-one was treated with (dimethyl(oxo)-l6-sulfaneylidene)methane in DMSO at elevated temperature, forming 1-(2-phenylcyclopropyl)ethan-1-one\n\nChemical Formula: C11H12O."
  },
  {
    "id": 3,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "A spin-half particle is in a linear superposition 0.5|\\uparrow\\rangle+sqrt(3)/2|\\downarrow\\rangle of its spin-up and spin-down states. If |\\uparrow\\rangle and |\\downarrow\\rangle are the eigenstates of \\sigma{z} , then what is the expectation value up to one decimal place, of the operator 10\\sigma{z}+5\\sigma_{x} ? Here, symbols have their usual meanings",
    "options": {
      "A": "0.85",
      "B": "-0.7",
      "C": "-1.4",
      "D": "1.65"
    },
    "correct_answer": "-0.7",
    "correct_answer_letter": "B",
    "Explanation": "|psi> = 0.5 |up=0> + sqrt(3)/2|down=1> \nIf the operator can be written as A,\nthen the expectation value is,\n = -0.7"
  },
  {
    "id": 4,
    "domain": "Physics",
    "subdomain": "Electromagnetism and Photonics",
    "Question": "In a parallel universe where a magnet can have an isolated North or South pole, Maxwell\u2019s equations look different. But, specifically, which of those equations are different?",
    "options": {
      "A": "The one related to the circulation of the magnetic field and the flux of the electric field. ",
      "B": "The one related to the divergence of the magnetic field. ",
      "C": "The ones related to the circulation of the electric field and the divergence of the magnetic field.  ",
      "D": "The ones related to the divergence and the curl of the magnetic field."
    },
    "correct_answer": "The ones related to the circulation of the electric field and the divergence of the magnetic field.  ",
    "correct_answer_letter": "C",
    "Explanation": "Let\u2019s call E and B the electric and magnetic fields, respectively:\nThe ones related to the circulation of the electric field and the divergence of the magnetic field is correct, since knowing that magnets can have an isolated pole means that magnetic monopoles exist and, thus, the contributions of magnetic charges and magnetic currents must be included in the equations. The way to include them is to \u201csymmetry-copy\u201d the other equations, with the following dictionary: E <-> B; electric charge <-> magnetic charge; electric current <-> magnetic current. In this way, the equations that become modified, with added terms, are the ones related to the circulation (or curl, in differential form) of E, and to the divergence (or flux in integral form) of B. \nThe ones related to the divergence and the curl of the magnetic field is incorrect, because the one with the curl does not change, since it already includes all symmetric contributions appearing in its symmetric equation (curl of electric field). \nThe one related to the divergence of the magnetic field is incorrect because that equation does get changed, but it\u2019s not the only one; the equation for the curl (or circulation) of E also changes.\nThe one related to the circulation of the magnetic field and the flux of the electric field is incorrect because none of those equations are changed, since they already include the symmetric terms appearing in their symmetric equations (circulation of E and flux of B)."
  },
  {
    "id": 5,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "Calculate the eigenvector of a quantum mechanical operator $\\vec{P}$ for a muon along an arbitrary direction $\\vec{n}$ lying in the x-z plane corresponding to the eigenvalue $+\\hbar/2$. Given the $X-$component, $P_x$ of the operator $P$ as $\\hbar/2$ times a 2 by 2 square matrix having elements in the first row as $(0 1)$, and that in the second row as $(1, 0)$. The $Y-$component, $P_y$ of the operator is given by the product of $\\hbar/2$ and a 2 by 2 square matrix having elements in the first row as $(0, -i)$, and that in the second row as $(i, 0)$. Finally, the $Z-$component, $P_z$ of the operator is given by the product of $\\hbar/2$  and another 2 by 2 square matrix having elements in the first row as $(1, 0)$, and that in the second row as $(0, -1)$.  What are the elements of the normalized eigenvector? \n",
    "options": {
      "A": "(\\cos(\\theta), e^{i\\phi}\\sin (\\theta))",
      "B": "(\\cos(\\theta/2), \\sin (\\theta/2))\n",
      "C": "(\\sqrt{2/3}\\hbar, \\sqrt{1/3}\\hbar)",
      "D": "(\\sqrt{2/3}\\hbar \\cos(\\theta/2), \\sqrt{1/3}\\hbar \\sin (\\theta/2))"
    },
    "correct_answer": "(\\cos(\\theta/2), \\sin (\\theta/2))\n",
    "correct_answer_letter": "B",
    "Explanation": "The arbitrary unit vector $\\vec{n}$ in two dimensional x-z plane can be written as $\\vec{n} = \\sin \\theta \\vec{i} + \\cos\\theta \\vec{k}$. Here, $0 \\leq \\theta \\leq \\pi$. The dot product $\\vec{P}.\\vec{n}$ thus becomes the product of $\\hbar/2$  and a square matrix having elements in the first row as $(\\cos\\theta, \\sin\\theta)$, and that in the second row as $(\\sin\\theta, -\\cos\\theta)$. Solving usual matrix form of the eigenvalue equation having eigenvalue as $\\hbar/2$ with unknown parameters, e.g. (a, b), as the elements of eigenvector, and then using normalizing condition one gets the elements as  $(\\cos(\\theta/2), \\sin (\\theta/2))$. "
  },
  {
    "id": 6,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "A quantum mechanical particle of mass m moves in two dimensions in the following potential, as a function of (r,\u03b8): V (r, \u03b8) = 1/2 kr^2 + 3/2 kr^2 cos^2(\u03b8)\nFind the energy spectrum.",
    "options": {
      "A": "E = (3n_x+2n_y+1/2) \u210f*sqrt(k/m))",
      "B": "E = (2n_x+n_y+3/2)\u210f*sqrt(k/m)",
      "C": "E = (n_x+3*n_y+3/2) \u210f*sqrt(k/m))",
      "D": "E = (2n_x+3n_y+1/2) \u210f*sqrt(k/m))"
    },
    "correct_answer": "E = (2n_x+n_y+3/2)\u210f*sqrt(k/m)",
    "correct_answer_letter": "B",
    "Explanation": "Potential can be written in cartesian coordinates as : V=1/2 k(4x^2+y^2).\nThis is potential of 2-dimensional non-isotropic harmonic oscillator. The energy of such oscillator in cartesian coordinates is: E=(n_x+1/2)\u210f\u03c9_1 +(n_y+1/2)\u210f\u03c9_2, where \u03c9_1=sqrt(4k/m)=2sqrt(k/m) and \u03c9_2=sqrt(k/m)=1/2 \u03c9_1\nSo E=(n_x+1/2)\u210f*2*\u03c9_2+(n_y+1/2)\u210f\u03c9_2=(2n_x+*n_y+3/2)\u210f\u03c9_2\nTherefore, the correction answer is: E = (2n_x+n_y+3/2)\u210fsqrt(k/m)"
  },
  {
    "id": 7,
    "domain": "Physics",
    "subdomain": "High-energy particle physics",
    "Question": "The universe is filled with the Cosmic Microwave Background. Consider the annihilation of high energy \\gamma-rays with a photon from the CMB Radiation into electron-positron, i.e. $\\gamma\\gamma\\rightarrow e^{+}e^{-}$. From what energy \\gamma-rays would have their lifetimes in the universe limited by this process? Knowing that the average photon energy of the CMB is $10^{-3}eV$.",
    "options": {
      "A": "1.8*1e5 GeV",
      "B": "3.9*1e5 GeV",
      "C": "2.6*1e5 GeV",
      "D": "9.5*1e4 GeV"
    },
    "correct_answer": "2.6*1e5 GeV",
    "correct_answer_letter": "C",
    "Explanation": "The CMB photon and the \\gamma-rays are denoted respectively $E{1},\\vec{p}{1},E{2},\\vec{p}{2}$. For the e^{+}e^{-} production, we have\n\n$\\left(E{1}+E{2}\\right)^{2}-\\left(\\vec{p}{1}+\\vec{p}{2}\\right)^{2}\\geq\\left(2m_{e}\\right)^{2}$\n\nSince $E{1}=p{1},E{2}=p{2}$ we obtain\n\n$2E{1}E{2}-2\\vec{p}{1}\\vec{p}{2}\\geq\\left(2m_{e}\\right)^{2}$\n\nLet's say that the angle between $\\vec{p}{1}$ and $\\vec{p}{2}$ is \\theta,\n\n$E{1}E{2}\\left(1-\\cos\\theta\\right)\\geq2m_{e}^{2}$\n\nTherefore\n\n$E{1}\\geq\\frac{2m{e}^{2}}{E_{2}\\left(1-\\cos\\theta\\right)}$\n\nThe minimum is when \\theta=\\pi, the minimum energy for pair production is\n\n$E{min}=\\frac{m{e}^{2}}{E_{2}}=2.6\\times10^{14}eV=2.6\\times10^{5}GeV$"
  },
  {
    "id": 8,
    "domain": "Biology",
    "subdomain": "Genetics",
    "Question": "You perform a high-throughput experiment on white lupine to find genes contributing to resistance to the fungal disease anthracnose. As a result, you receive three candidate genes of unknown function \u2013 G1, G2, and G3. You create three knock-out mutants, g1, g2, and g3, and a set of double-mutants, g1g2, g1g3, and g2g3. You know that at least one of these genes is a transcription factor acting upstream of (an)other gene(s). You start to test those mutant plants: do they have a higher sensitivity to anthracnose than the wild-type because they cannot produce certain gene products? \nAfter tests with the pathogen, you receive the following results where 100% is the level of resistance to the pathogen in control; 50% is half of the control\u2019s resistance; 25% is a quarter of the control\u2019s resistance; 0% \u2012 all plants show signs of infection:\n- resistance of g1: 75% of control\n- resistance of g2: 0% from control\n- resistance of g3: 50% from control\n-resistance of g1g3: 10% from control\n- resistance of g2g3: 0% from control\n- resistance of g1g2: 0% from control\n\nWhich conclusion regarding those genes' interaction can you draw from this experiment?\n",
    "options": {
      "A": "G1 is a transcription factor, G2 and G3 show pleiotropy, G2 is epistatic towards G1",
      "B": "G2 is a transcription factor, G1 and G3 has the same promoter, G3 is epistatic towards G1",
      "C": "G2 is a transcription factor, G1 and G3 show pleiotropy, G1 is epistatic towards G3",
      "D": "G2 is a transcription factor, G1 and G3 show gene redundancy, G1 is epistatic towards G3"
    },
    "correct_answer": "G2 is a transcription factor, G1 and G3 show gene redundancy, G1 is epistatic towards G3",
    "correct_answer_letter": "D",
    "Explanation": "The experimental conditions and output are simplified. Looking at the data, we must reply to three questions:\n-\tWhich gene(s) is a transcription factor?\n-\tAre there signs of gene redundancy or pleiotropy?\n-\tIs any of the genes epistatic towards (an)other one(s)?\n\nWe can identify a transcription factor upstream of other genes by a decrease in resistance after its knock-out. In single mutants, we can see that knockout of G2 drastically decreases the resistance, while knockout of the other two genes reduces the resistance much less. This allows us to suggest that G2 controls the expression of two other genes, as its knockout leads to the loss of their functionality. Looking at the single-mutant data of G1 and G3, we can see that both genes contribute to the resistance if G2 is active \u2013 therefore, they are examples of gene redundancy. We see that G1 alone (with knockout G3) contributes to half of the total resistance (50%). We would expect that G3 would contribute another 50% if G1 is knockout, but it contributes 75%, which suggests that G1 has epistatic interactions towards G3 and decreases its expression when active.\n\nTherefore, the correct answer: G2 is a transcription factor, and G1 and G3 show gene redundancy. G1 is epistatic towards G3."
  },
  {
    "id": 9,
    "domain": "Chemistry",
    "subdomain": "Organic Chemistry",
    "Question": "which of the following molecules has c3h symmetry?\ntriisopropyl borate\nquinuclidine\nbenzo[1,2-c:3,4-c':5,6-c'']trifuran-1,3,4,6,7,9-hexaone\ntriphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone",
    "options": {
      "A": "quinuclidine",
      "B": "benzo[1,2-c:3,4-c':5,6-c'']trifuran-1,3,4,6,7,9-hexaone",
      "C": "triphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone",
      "D": "triisopropyl borate\n"
    },
    "correct_answer": "triphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone",
    "correct_answer_letter": "C",
    "Explanation": "all of the molecules have a C3 principal axis.\n\ntriisopropyl borate has no other symmetry elements (besides the identity element) so it has point group C3.\n\nquinuclidine has 3 mirror planes about the C3 axis, so it is point group C3V.\n\nbenzo[1,2-c:3,4-c':5,6-c'']trifuran-1,3,4,6,7,9-hexaone has 3 mirror planes about the C3 axis, and also a mirror plane normal to the C3 axis (it also has C2 axes normal to the C3 axis). this puts it in group D3H\n\ntriphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone has no mirror planes about the C3 axis, but has a mirror plane normal to the C3 axis. this puts it in point group C3H.\n"
  },
  {
    "id": 10,
    "domain": "Physics",
    "subdomain": "Astrophysics",
    "Question": "Among the following exoplanets, which one has the highest density?\n\na) An Earth-mass and Earth-radius planet.\nb) A planet with 2 Earth masses and a density of approximately 5.5 g/cm^3.\nc) A planet with the same composition as Earth but 5 times more massive than Earth.\nd) A planet with the same composition as Earth but half the mass of Earth.",
    "options": {
      "A": "d",
      "B": "b",
      "C": "a",
      "D": "c"
    },
    "correct_answer": "c",
    "correct_answer_letter": "D",
    "Explanation": "Gravitational compression tends to decrease the radius of an object as its mass increases, resulting in an increase in density. You can refer to Ref1, Ref2, and the table of Radius-Mass Dependence for Earth-like Composition in Ref3 (this table comes from Ref2) for more information.\n\nFrom the table, it is evident that for a composition similar to Earth's, a mass of 0.53 times that of Earth corresponds to a radius of 0.833 times Earth's radius, resulting in an approximate density of 0.93 times that of Earth's (Earth's density is approximately 5.5 g/cm^3).\n\nFor a mass of 5.2 times that of Earth, the radius is 1.56 times Earth's radius, leading to a density of approximately 1.36 times Earth's density. Therefore, the planet with the greatest mass will have the highest density.\n\n\nRef1 - https://en.wikipedia.org/wiki/Gravitational_compression\nRef2 - https://lweb.cfa.harvard.edu/~lzeng/planetmodels.html\nRef3 - https://lweb.cfa.harvard.edu/~lzeng/tables/massradiusEarthlikeRocky.txt"
  },
  {
    "id": 11,
    "domain": "Biology",
    "subdomain": "Molecular Biology",
    "Question": "All the following statements about the molecular biology of Severe Acute Respiratory Syndrome Coronavirus 2 (SARS\u2011CoV\u20112) are correct except\n\n\n",
    "options": {
      "A": "SARS-CoV-2 nsp10/nsp14-ExoN operates as heterodimers in a mismatch repair mechanism. The N-terminal ExoN domain of nsp14 could bind to nsp10 making an active exonuclease complex that prevents the breakdown of dsRNA. ",
      "B": "Programmed ribosomal frameshifting creates two polyproteins near to 5` end of the genome by moving back by 1 nucleotide with the help of slippery nucleotides, and pseudoknot. The SARS-CoV-2 programmed ribosomal frameshifting mostly has the same conformation as the SARS-CoV programmed ribosomal frameshifting.",
      "C": "The rate of frameshifting in vitro is linearly correlated with the number of conformations that a pseudoknot can adopt. Both SARS-CoV and SARS-CoV-2 Programmed -1 Frameshift Signals show two conformations when under tension, similar to other pseudoknots that induce comparable frameshifting rates. ",
      "D": "SARS-CoV-2 ORF3a has the ability to trigger caspase-8 activation/cleavage, without affecting the expression levels of Bcl-2. Caspase-8 activation is recognized as a characteristic feature of the extrinsic apoptotic pathway via death receptors, while Bcl-2 plays a crucial role in initiating the mitochondrial pathway. This suggests that the mechanism through which SARS-CoV-2 ORF3a induces apoptosis is via the extrinsic apoptotic pathway.\n"
    },
    "correct_answer": "SARS-CoV-2 nsp10/nsp14-ExoN operates as heterodimers in a mismatch repair mechanism. The N-terminal ExoN domain of nsp14 could bind to nsp10 making an active exonuclease complex that prevents the breakdown of dsRNA. ",
    "correct_answer_letter": "A",
    "Explanation": "The rate of frameshifting in vitro is linearly correlated with the number of conformations that a pseudoknot can adopt. Both SARS-CoV and SARS-CoV-2 Programmed -1 Frameshift Signals show two conformations when under tension, similar to other pseudoknots that induce comparable frameshifting rates. This is a correct statement.\nhttps://www.ncbi.nlm.nih.gov/pmc/articles/PMC8353986/ \n\nSARS-CoV-2 nsp10/nsp14-ExoN operates as heterodimers in a mismatch repair mechanism. The N-terminal ExoN domain of nsp14 could bind to nsp10 making an active exonuclease complex that prevents the breakdown of dsRNA. This is an incorrect statement because it preferentially degrades dsRNA https://www.pnas.org/doi/10.1073/pnas.2106379119\n\n\nProgrammed ribosomal frameshifting creates two polyproteins near to 5` end of the genome by moving back by 1 nucleotide with the help of slippery nucleotides, and pseudoknot. The SARS-CoV-2 programmed ribosomal frameshifting mostly has the same conformation as the SARS-CoV programmed ribosomal frameshifting. This is correct https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8353986/ \n\nSARS-CoV-2 ORF3a has the ability to trigger caspase-8 activation/cleavage, without affecting the expression levels of Bcl-2. Caspase-8 activation is recognized as a characteristic feature of the extrinsic apoptotic pathway via death receptors, while Bcl-2 plays a crucial role in initiating the mitochondrial pathway. This suggests that the mechanism through which SARS-CoV-2 ORF3a induces apoptosis is via the extrinsic apoptotic pathway. This is correct https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7844099/ \n\n"
  },
  {
    "id": 12,
    "domain": "Physics",
    "subdomain": "High-energy particle physics",
    "Question": "Find KE of product particles in,\nPi(+) = mu(+) + nu\nhere Pi(+) is stationary.\nRest mass of Pi(+) &  mu(+) is 139.6 MeV & 105.7 MeV respectively.",
    "options": {
      "A": "3.52 MeV, 20.8 MeV",
      "B": "4.12 MeV, 29.8 MeV",
      "C": "2.84 MeV, 26.8 MeV",
      "D": "7.2 MeV, 32.8 MeV"
    },
    "correct_answer": "4.12 MeV, 29.8 MeV",
    "correct_answer_letter": "B",
    "Explanation": "Knowing the rest mass energies of the\nproducts and reactants, we can find out the energy difference because that energy difference will be the kinetic energy,\n33.9 MeV = k_mu + k_nu\n\nNow, we apply the principle of conservation of linear momentum, \nP_mu = P_nu.\nWhere P represent the magnitude of linear momentum. \nWe can write the relativistic relation between\nthe K.E of a particle and its momentum P:\n (Pc)^2 = k^2 + 2kmc^2\nApplying this,\nk_mu^2 + 2k_mu*m_mu*c^2 = k_nu^2\nApplying this to first equation we get the respective values."


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/data/public/diamond_questions.json =====

[
  {
    "id": 1,
    "domain": "Physics",
    "subdomain": "Physics (general)",
    "Question": "Two quantum states with energies E1 and E2 have a lifetime of 10^-9 sec and 10^-8 sec, respectively. We want to clearly distinguish these two energy levels. Which one of the following options could be their energy difference so that they can be clearly resolved?\n",
    "options": {
      "A": "10^-4 eV",
      "B": "10^-9 eV",
      "C": "10^-11 eV",
      "D": "10^-8 eV"
    }
  },
  {
    "id": 2,
    "domain": "Chemistry",
    "subdomain": "Organic Chemistry",
    "Question": "trans-cinnamaldehyde was treated with methylmagnesium bromide, forming product 1.\n\n1 was treated with pyridinium chlorochromate, forming product 2.\n\n3 was treated with (dimethyl(oxo)-l6-sulfaneylidene)methane in DMSO at elevated temperature, forming product 3.\n\nhow many carbon atoms are there in product 3?",
    "options": {
      "A": "11",
      "B": "14",
      "C": "12",
      "D": "10"
    }
  },
  {
    "id": 3,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "A spin-half particle is in a linear superposition 0.5|\\uparrow\\rangle+sqrt(3)/2|\\downarrow\\rangle of its spin-up and spin-down states. If |\\uparrow\\rangle and |\\downarrow\\rangle are the eigenstates of \\sigma{z} , then what is the expectation value up to one decimal place, of the operator 10\\sigma{z}+5\\sigma_{x} ? Here, symbols have their usual meanings",
    "options": {
      "A": "0.85",
      "B": "-0.7",
      "C": "-1.4",
      "D": "1.65"
    }
  },
  {
    "id": 4,
    "domain": "Physics",
    "subdomain": "Electromagnetism and Photonics",
    "Question": "In a parallel universe where a magnet can have an isolated North or South pole, Maxwell\u2019s equations look different. But, specifically, which of those equations are different?",
    "options": {
      "A": "The one related to the circulation of the magnetic field and the flux of the electric field. ",
      "B": "The one related to the divergence of the magnetic field. ",
      "C": "The ones related to the circulation of the electric field and the divergence of the magnetic field.  ",
      "D": "The ones related to the divergence and the curl of the magnetic field."
    }
  },
  {
    "id": 5,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "Calculate the eigenvector of a quantum mechanical operator $\\vec{P}$ for a muon along an arbitrary direction $\\vec{n}$ lying in the x-z plane corresponding to the eigenvalue $+\\hbar/2$. Given the $X-$component, $P_x$ of the operator $P$ as $\\hbar/2$ times a 2 by 2 square matrix having elements in the first row as $(0 1)$, and that in the second row as $(1, 0)$. The $Y-$component, $P_y$ of the operator is given by the product of $\\hbar/2$ and a 2 by 2 square matrix having elements in the first row as $(0, -i)$, and that in the second row as $(i, 0)$. Finally, the $Z-$component, $P_z$ of the operator is given by the product of $\\hbar/2$  and another 2 by 2 square matrix having elements in the first row as $(1, 0)$, and that in the second row as $(0, -1)$.  What are the elements of the normalized eigenvector? \n",
    "options": {
      "A": "(\\cos(\\theta), e^{i\\phi}\\sin (\\theta))",
      "B": "(\\cos(\\theta/2), \\sin (\\theta/2))\n",
      "C": "(\\sqrt{2/3}\\hbar, \\sqrt{1/3}\\hbar)",
      "D": "(\\sqrt{2/3}\\hbar \\cos(\\theta/2), \\sqrt{1/3}\\hbar \\sin (\\theta/2))"
    }
  },
  {
    "id": 6,
    "domain": "Physics",
    "subdomain": "Quantum Mechanics",
    "Question": "A quantum mechanical particle of mass m moves in two dimensions in the following potential, as a function of (r,\u03b8): V (r, \u03b8) = 1/2 kr^2 + 3/2 kr^2 cos^2(\u03b8)\nFind the energy spectrum.",
    "options": {
      "A": "E = (3n_x+2n_y+1/2) \u210f*sqrt(k/m))",
      "B": "E = (2n_x+n_y+3/2)\u210f*sqrt(k/m)",
      "C": "E = (n_x+3*n_y+3/2) \u210f*sqrt(k/m))",
      "D": "E = (2n_x+3n_y+1/2) \u210f*sqrt(k/m))"
    }
  },
  {
    "id": 7,
    "domain": "Physics",
    "subdomain": "High-energy particle physics",
    "Question": "The universe is filled with the Cosmic Microwave Background. Consider the annihilation of high energy \\gamma-rays with a photon from the CMB Radiation into electron-positron, i.e. $\\gamma\\gamma\\rightarrow e^{+}e^{-}$. From what energy \\gamma-rays would have their lifetimes in the universe limited by this process? Knowing that the average photon energy of the CMB is $10^{-3}eV$.",
    "options": {
      "A": "1.8*1e5 GeV",
      "B": "3.9*1e5 GeV",
      "C": "2.6*1e5 GeV",
      "D": "9.5*1e4 GeV"
    }
  },
  {
    "id": 8,
    "domain": "Biology",
    "subdomain": "Genetics",
    "Question": "You perform a high-throughput experiment on white lupine to find genes contributing to resistance to the fungal disease anthracnose. As a result, you receive three candidate genes of unknown function \u2013 G1, G2, and G3. You create three knock-out mutants, g1, g2, and g3, and a set of double-mutants, g1g2, g1g3, and g2g3. You know that at least one of these genes is a transcription factor acting upstream of (an)other gene(s). You start to test those mutant plants: do they have a higher sensitivity to anthracnose than the wild-type because they cannot produce certain gene products? \nAfter tests with the pathogen, you receive the following results where 100% is the level of resistance to the pathogen in control; 50% is half of the control\u2019s resistance; 25% is a quarter of the control\u2019s resistance; 0% \u2012 all plants show signs of infection:\n- resistance of g1: 75% of control\n- resistance of g2: 0% from control\n- resistance of g3: 50% from control\n-resistance of g1g3: 10% from control\n- resistance of g2g3: 0% from control\n- resistance of g1g2: 0% from control\n\nWhich conclusion regarding those genes' interaction can you draw from this experiment?\n",
    "options": {
      "A": "G1 is a transcription factor, G2 and G3 show pleiotropy, G2 is epistatic towards G1",
      "B": "G2 is a transcription factor, G1 and G3 has the same promoter, G3 is epistatic towards G1",
      "C": "G2 is a transcription factor, G1 and G3 show pleiotropy, G1 is epistatic towards G3",
      "D": "G2 is a transcription factor, G1 and G3 show gene redundancy, G1 is epistatic towards G3"
    }
  },
  {
    "id": 9,
    "domain": "Chemistry",
    "subdomain": "Organic Chemistry",
    "Question": "which of the following molecules has c3h symmetry?\ntriisopropyl borate\nquinuclidine\nbenzo[1,2-c:3,4-c':5,6-c'']trifuran-1,3,4,6,7,9-hexaone\ntriphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone",
    "options": {
      "A": "quinuclidine",
      "B": "benzo[1,2-c:3,4-c':5,6-c'']trifuran-1,3,4,6,7,9-hexaone",
      "C": "triphenyleno[1,2-c:5,6-c':9,10-c'']trifuran-1,3,6,8,11,13-hexaone",
      "D": "triisopropyl borate\n"
    }
  },
  {
    "id": 10,
    "domain": "Physics",
    "subdomain": "Astrophysics",
    "Question": "Among the following exoplanets, which one has the highest density?\n\na) An Earth-mass and Earth-radius planet.\nb) A planet with 2 Earth masses and a density of approximately 5.5 g/cm^3.\nc) A planet with the same composition as Earth but 5 times more massive than Earth.\nd) A planet with the same composition as Earth but half the mass of Earth.",
    "options": {
      "A": "d",
      "B": "b",
      "C": "a",
      "D": "c"
    }
  },
  {
    "id": 11,
    "domain": "Biology",
    "subdomain": "Molecular Biology",
    "Question": "All the following statements about the molecular biology of Severe Acute Respiratory Syndrome Coronavirus 2 (SARS\u2011CoV\u20112) are correct except\n\n\n",
    "options": {
      "A": "SARS-CoV-2 nsp10/nsp14-ExoN operates as heterodimers in a mismatch repair mechanism. The N-terminal ExoN domain of nsp14 could bind to nsp10 making an active exonuclease complex that prevents the breakdown of dsRNA. ",
      "B": "Programmed ribosomal frameshifting creates two polyproteins near to 5` end of the genome by moving back by 1 nucleotide with the help of slippery nucleotides, and pseudoknot. The SARS-CoV-2 programmed ribosomal frameshifting mostly has the same conformation as the SARS-CoV programmed ribosomal frameshifting.",
      "C": "The rate of frameshifting in vitro is linearly correlated with the number of conformations that a pseudoknot can adopt. Both SARS-CoV and SARS-CoV-2 Programmed -1 Frameshift Signals show two conformations when under tension, similar to other pseudoknots that induce comparable frameshifting rates. ",
      "D": "SARS-CoV-2 ORF3a has the ability to trigger caspase-8 activation/cleavage, without affecting the expression levels of Bcl-2. Caspase-8 activation is recognized as a characteristic feature of the extrinsic apoptotic pathway via death receptors, while Bcl-2 plays a crucial role in initiating the mitochondrial pathway. This suggests that the mechanism through which SARS-CoV-2 ORF3a induces apoptosis is via the extrinsic apoptotic pathway.\n"
    }
  },
  {
    "id": 12,
    "domain": "Physics",
    "subdomain": "High-energy particle physics",
    "Question": "Find KE of product particles in,\nPi(+) = mu(+) + nu\nhere Pi(+) is stationary.\nRest mass of Pi(+) &  mu(+) is 139.6 MeV & 105.7 MeV respectively.",
    "options": {
      "A": "3.52 MeV, 20.8 MeV",
      "B": "4.12 MeV, 29.8 MeV",
      "C": "2.84 MeV, 26.8 MeV",
      "D": "7.2 MeV, 32.8 MeV"
    }
  },
  {
    "id": 13,
    "domain": "Chemistry",
    "subdomain": "Organic Chemistry",
    "Question": "A methanol solution of (R)-(+)-Limonene is stirred with Pd/C under a Hydrogen atmosphere. After 1 equivalent of hydrogen is consumed, product 1 is isolated as the major product.\n\n1 is treated with 3-chloroperbenzoic acid, forming product 2.\n\nProduct 2 is treated with sodium methoxide, forming product 3.\n\nProduct 3 is treated with propanoic acid, dicyclohexylcarbodiimide. and a catalytic amount of  4-dimethylaminopyridine, forming product 4.\n\nwhat is a valid structure of product 4? (product 4 exists as a mixture of isomers. the correct answer is one of them).",
    "options": {
      "A": "(1S,2R,4R)-4-isopropyl-2-methoxy-1-methylcyclohexyl propionate",
      "B": "(1S,2S,4R)-4-isopropyl-2-methoxy-1-methylcyclohexyl propionate",
      "C": "(1S,2S,5R)-5-isopropyl-2-methoxy-2-methylcyclohexyl propionate",
      "D": "1-methoxy-2-((S)-4-methylcyclohex-3-en-1-yl)propan-2-yl propionate"
    }
  },
  {
    "id": 14,
    "domain": "Biology",
    "subdomain": "Molecular Biology",
    "Question": "ChIP-seq on a PFA-fixed sample with an antibody to the IKAROS transcription factor in human B cells followed by next-generation sequencing and standard quality control, alignment and peak-calling steps produced ChIP peaks that disappeared when PFA+DSG fixation was used. Where are we most likely to find such disappearing peaks?",
    "options": {
      "A": "At active promoters and enhancers",
      "B": "In the introns of large genes",
      "C": "At random locations in the genome",
      "D": "At repeats"
    }
  },
  {
    "id": 15,
    "domain": "Physics",
    "subdomain": "Physics (general)",
    "Question": "Researchers are attempting to detect transits of two Earth-like planets: Planet_1 and Planet_2. They have limited observing time and want to observe the one that has the highest probability of transiting. Both of these planets have already been detected via the RV method, allowing us to know their minimum masses and orbital periods. Although both planets share the same masses, the orbital period of Planet_1 is three times shorter than that of Planet_2. Interestingly, they both have circular orbits. Furthermore, we know the masses and radii of the host stars of these two planets. The star hosting Planet_1 has a mass that is twice that of the host star of Planet_2. As the host of Planet_2 is slightly evolved, both host stars have the same radii. Based on the provided information, the researchers have chosen to observe:",
    "options": {
      "A": "Planet_1 is preferred due to its ~2.7 times higher probability to transit.\n",
      "B": "Planet_2 is preferred due to its ~2.25 times higher probability to transit.\n",
      "C": "Planet_1 is preferred due to its ~1.65 times higher probability to transit.\n",
      "D": "Planet_2 is preferred due to its ~1.5 times higher probability to transit.\n"
    }


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/data/public/classes.json =====

[
  "[走私、贩卖、运输、制造]毒品",
  "盗窃",
  "非法占用农用地",
  "[生产、销售]不符合安全标准的食品",
  "重大责任事故",
  "[生产、销售]假药",
  "非法种植毒品原植物",
  "失火",
  "污染环境",
  "销售假冒注册商标的商品",
  "非法行医",
  "[生产、销售][有毒、有害]食品",
  "过失致人死亡",
  "假冒注册商标",
  "拒不执行[判决、裁定]",
  "[虚开增值税专用发票、用于骗取出口退税、抵扣税款发票]",
  "非法经营",
  "滥伐林木",
  "故意杀人",
  "盗伐林木",
  "故意伤害",
  "拒不支付劳动报酬",
  "交通肇事",
  "诈骗",
  "非法吸收公众存款",
  "强奸",
  "骗取[贷款、票据承兑、金融票证]",
  "挪用资金",
  "信用卡诈骗",
  "非国家工作人员受贿",
  "玩忽职守",
  "受贿",
  "行贿",
  "非法[制造、买卖、运输、邮寄、储存][枪支、弹药、爆炸物]",
  "放火",
  "合同诈骗",
  "职务侵占",
  "[窝藏、包庇]",
  "挪用公款",
  "敲诈勒索",
  "故意毁坏财物",
  "非法拘禁",
  "非法[采伐、毁坏]国家重点保护植物",
  "非法狩猎",
  "伪造[公司、企业、事业单位、人民团体]印章",
  "贪污",
  "[伪造、变造、买卖]国家机关[公文、证件、印章]",
  "赌博",
  "危险驾驶",
  "[组织、领导]传销活动",
  "开设赌场",
  "聚众斗殴",
  "非法侵入住宅",
  "单位行贿",
  "[生产、销售]伪劣产品",
  "[掩饰、隐瞒][犯罪所得、犯罪所得收益]",
  "非法[持有、私藏][枪支、弹药]",
  "非法持有毒品",
  "妨害公务",
  "抢劫",
  "过失致人重伤",
  "滥用职权",
  "寻衅滋事",
  "招摇撞骗",
  "走私普通[货物、物品]",
  "以危险方法危害公共安全",
  "妨害信用卡管理",
  "非法捕捞水产品",
  "猥亵儿童",
  "抢夺",
  "非法采矿",
  "破坏生产经营",
  "虚开发票",
  "破坏[广播电视设施、公用电信设施]",
  "拐卖[妇女、儿童]",
  "集资诈骗",
  "重婚",
  "持有伪造的发票",
  "绑架",
  "非法[收购、运输、加工、出售][国家重点保护植物、国家重点保护植物制品]",
  "破坏电力设备",
  "扰乱无线电通讯管理秩序",
  "投放危险物质",
  "非法处置[查封、扣押、冻结]的财产",
  "重大劳动安全事故",
  "强制[猥亵、侮辱]妇女",
  "侵犯著作权",
  "非法[猎捕、杀害][珍贵、濒危]野生动物",
  "[持有、使用]假币",
  "非法[转让、倒卖]土地使用权",
  "爆炸",
  "盗掘[古文化遗址、古墓葬]",
  "保险诈骗",
  "聚众扰乱社会秩序",
  "对非国家工作人员行贿",
  "破坏易燃易爆设备",
  "非法获取公民个人信息",
  "违法发放贷款",
  "贷款诈骗",
  "冒充军人招摇撞骗",
  "票据诈骗",
  "非法[收购、运输][盗伐、滥伐]的林木",
  "[伪造、变造]居民身份证",
  "[出售、购买、运输]假币",
  "非法买卖制毒物品",
  "[制作、复制、出版、贩卖、传播]淫秽物品牟利",
  "聚众扰乱[公共场所秩序、交通秩序]",
  "[伪造、变造]金融票证",
  "非法进行节育手术",
  "诬告陷害",
  "强迫交易",
  "单位受贿",
  "逃税",
  "介绍贿赂",
  "过失以危险方法危害公共安全",
  "[编造、故意传播]虚假恐怖信息",
  "非法出售发票",
  "拐骗儿童",
  "遗弃",
  "对单位行贿",
  "串通投标",
  "伪证",
  "帮助犯罪分子逃避处罚",
  "走私[珍贵动物、珍贵动物制品]",
  "侵占",
  "虚报注册资本",
  "妨害作证",
  "走私国家禁止进出口的[货物、物品]",
  "动植物检疫徇私舞弊",
  "[引诱、教唆、欺骗]他人吸毒",
  "徇私枉法",
  "非法携带[枪支、弹药、管制刀具、危险物品]危及公共安全",
  "破坏计算机信息系统",
  "非法[生产、销售]间谍专用器材",
  "非法[制造、出售]非法制造的发票",
  "侮辱",
  "[隐匿、故意销毁][会计凭证、会计帐簿、财务会计报告]",
  "非法[制造、销售]非法制造的注册商标标识",
  "传播性病",
  "利用影响力受贿",
  "脱逃",
  "走私[武器、弹药]",
  "私分国有资产",
  "非法组织卖血",
  "破坏监管秩序",
  "非法[制造、买卖、运输、储存]危险物质",
  "[窃取、收买、非法提供]信用卡信息",
  "[窝藏、转移、收购、销售]赃物",
  "危险物品肇事",
  "聚众冲击国家机关",
  "破坏交通设施",
  "过失损坏[广播电视设施、公用电信设施]",
  "[生产、销售]伪劣[农药、兽药、化肥、种子]",
  "招收[公务员、学生]徇私舞弊",
  "非法[生产、买卖]警用装备",
  "过失投放危险物质",
  "[盗窃、侮辱]尸体",
  "[伪造、变造、买卖]武装部队[公文、证件、印章]",
  "走私废物",
  "帮助[毁灭、伪造]证据",
  "虐待",
  "收买被拐卖的[妇女、儿童]",
  "非法获取国家秘密",
  "诽谤",
  "挪用特定款物",
  "徇私舞弊不移交刑事案件",
  "强迫劳动",
  "[伪造、倒卖]伪造的有价票证",
  "提供[侵入、非法控制计算机信息系统][程序、工具]",
  "过失损坏[武器装备、军事设施、军事通信]",
  "非法[收购、运输、出售][珍贵、濒危野生动物、珍贵、濒危野生动物]制品",
  "传授犯罪方法",
  "倒卖[车票、船票]",
  "伪造货币",
  "洗钱",
  "金融凭证诈骗",
  "破坏交通工具",
  "聚众哄抢",
  "倒卖文物",


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/data/private/answers.json =====

{
  "best_3_moves_hard_1": [
    "c4",
    "bxc4",
    "bxc4"
  ],
  "best_3_moves_hard_2": [
    "Kg4",
    "Kb3",
    "Kh3"
  ],
  "best_3_moves_hard_3": [
    "h3",
    "d6",
    "h2"
  ],
  "best_3_moves_hard_4": [
    "d2",
    "Ke6",
    "d1=Q"
  ],
  "best_3_moves_hard_5": [
    "g4",
    "f4",
    "h3"
  ],
  "best_3_moves_hard_6": [
    "Rf2",
    "Rxe2",
    "Rxe2"
  ],
  "best_3_moves_hard_7": [
    "Rf3",
    "Kg2",
    "Qf5"
  ],
  "knight_path_hard_1": "218",
  "knight_path_hard_2": "218",
  "knight_path_hard_3": "217",
  "knight_path_hard_4": "226",
  "knight_path_hard_5": "230",
  "knight_path_hard_6": "245",
  "knight_path_hard_7": "234",
  "knight_path_hard_8": "204",
  "knight_path_hard_9": "222",
  "best_3_moves_hard_8": [
    "Bd8",
    "Rc8+",
    "Ka7"
  ],
  "knight_path_hard_10": "200",
  "knight_path_hard_11": "199",
  "knight_path_hard_12": "245",
  "knight_path_hard_13": "218",
  "knight_path_hard_14": "219",
  "knight_path_hard_15": "230",
  "knight_path_hard_16": "232",
  "knight_path_hard_17": "251",
  "knight_path_hard_18": "245",
  "knight_path_hard_19": "249",
  "best_3_moves_hard_9": [
    "Bd3",
    "Ne4",
    "Bxe4"
  ],
  "knight_path_hard_20": "210",
  "knight_path_hard_21": "231",
  "knight_path_hard_22": "231",
  "knight_path_hard_23": "248",
  "knight_path_hard_24": "232",
  "knight_path_hard_25": "223",
  "knight_path_hard_26": "225",
  "knight_path_hard_27": "240",
  "knight_path_hard_28": "219",
  "knight_path_hard_29": "248",
  "best_3_moves_hard_10": [
    "Re5",
    "Qxe5",
    "Nf3+"
  ],
  "knight_path_hard_30": "224",
  "knight_path_hard_31": "238",
  "knight_path_hard_32": "239",
  "knight_path_hard_33": "225",
  "knight_path_hard_34": "224",
  "knight_path_hard_35": "238",
  "knight_path_hard_36": "213",
  "knight_path_hard_37": "236",
  "knight_path_hard_38": "212",
  "knight_path_hard_39": "229",
  "best_3_moves_hard_11": [
    "Qe3",
    "Ng6",
    "Nd2"
  ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/data/public/chess_hard.json =====

[
  {
    "question_id": "best_3_moves_hard_1",
    "prompt": "You are given a chess position using this FEN: 8/8/4k2K/1pp5/3pP1P1/pP6/P1P5/8 b - - 0 38\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_2",
    "prompt": "You are given a chess position using this FEN: 8/7p/p7/P4p1k/1K1B1P2/6P1/p3b2P/8 b - - 7 45\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_3",
    "prompt": "You are given a chess position using this FEN: 8/5Q2/8/3P4/4K2p/6q1/6k1/8 b - - 0 57\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_4",
    "prompt": "You are given a chess position using this FEN: 5k2/6R1/5P2/2pKP2p/p6P/3p4/r1P5/8 b - - 2 49\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_5",
    "prompt": "You are given a chess position using this FEN: 8/8/3k4/1P2ppp1/2K4p/5PP1/7P/8 w - - 0 37\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_6",
    "prompt": "You are given a chess position using this FEN: 8/7K/7P/8/5k2/8/2R1p1r1/8 b - - 0 50\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "best_3_moves_hard_7",
    "prompt": "You are given a chess position using this FEN: 4R3/5p1k/5qpp/8/3P4/2r4P/3Q1P1K/8 b - - 3 40\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "knight_path_hard_1",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (51, 43)\nTarget Squares: [(64, 27), (9, 77), (53, 72), (26, 16), (18, 97), (46, 3), (84, 17), (66, 45), (88, 76), (80, 74), (67, 32), (17, 40), (88, 9), (37, 18), (71, 89), (68, 89), (81, 82), (80, 17), (34, 76), (5, 18), (48, 23), (32, 17), (22, 85), (39, 98), (9, 9), (19, 93), (80, 9), (50, 92), (70, 38), (1, 74)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_2",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (22, 3)\nTarget Squares: [(81, 9), (83, 2), (30, 79), (24, 68), (19, 13), (87, 39), (11, 2), (22, 58), (60, 0), (0, 51), (54, 11), (9, 28), (40, 66), (20, 4), (93, 46), (29, 19), (13, 73), (3, 62), (45, 48), (57, 60), (97, 35), (5, 62), (22, 57), (25, 62), (52, 71), (83, 80), (93, 2), (74, 54), (14, 83), (84, 24)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_3",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (81, 97)\nTarget Squares: [(9, 62), (80, 4), (23, 48), (11, 40), (14, 84), (65, 42), (87, 15), (89, 24), (38, 15), (66, 37), (11, 51), (78, 34), (6, 48), (36, 86), (8, 47), (22, 57), (7, 49), (99, 88), (98, 21), (93, 71), (54, 86), (52, 0), (82, 89), (77, 56), (71, 88), (98, 85), (63, 21), (83, 20), (95, 39), (20, 77)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_4",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (9, 25)\nTarget Squares: [(23, 78), (17, 27), (35, 3), (60, 11), (87, 54), (97, 80), (36, 95), (64, 49), (59, 33), (64, 69), (24, 26), (70, 81), (8, 78), (54, 72), (35, 43), (21, 71), (33, 23), (61, 28), (97, 29), (9, 21), (53, 34), (9, 72), (67, 60), (17, 58), (36, 34), (26, 93), (79, 98), (74, 90), (60, 47), (41, 67)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_5",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (80, 10)\nTarget Squares: [(67, 88), (65, 2), (93, 3), (30, 3), (89, 70), (8, 16), (26, 94), (16, 21), (57, 11), (97, 77), (39, 99), (44, 42), (94, 96), (71, 55), (85, 54), (91, 37), (52, 38), (18, 92), (82, 92), (86, 81), (41, 75), (14, 72), (61, 95), (91, 3), (58, 11), (28, 68), (60, 72), (58, 80), (86, 4), (60, 97)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_6",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (46, 95)\nTarget Squares: [(60, 93), (98, 79), (29, 4), (45, 51), (50, 90), (37, 98), (31, 54), (54, 63), (82, 37), (60, 42), (72, 17), (94, 98), (63, 42), (92, 8), (78, 24), (57, 10), (8, 36), (66, 21), (5, 48), (99, 11), (51, 77), (83, 62), (5, 88), (13, 30), (89, 28), (5, 77), (79, 79), (62, 28), (90, 32), (81, 10)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_7",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (28, 27)\nTarget Squares: [(63, 7), (13, 24), (93, 19), (95, 66), (7, 21), (95, 35), (81, 54), (85, 98), (60, 93), (2, 59), (33, 52), (26, 61), (14, 58), (75, 9), (10, 20), (96, 19), (15, 98), (24, 43), (52, 1), (55, 33), (72, 62), (76, 94), (31, 79), (13, 67), (98, 17), (5, 78), (52, 93), (32, 31), (99, 24), (77, 38)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_8",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (35, 75)\nTarget Squares: [(99, 65), (87, 89), (76, 26), (64, 92), (14, 43), (96, 98), (53, 48), (50, 94), (7, 43), (55, 52), (58, 36), (69, 1), (37, 54), (97, 86), (45, 81), (83, 42), (70, 68), (74, 51), (91, 34), (84, 39), (75, 11), (81, 14), (92, 47), (71, 15), (41, 36), (72, 68), (89, 7), (65, 30), (59, 29), (53, 38)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_9",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (65, 16)\nTarget Squares: [(92, 59), (0, 8), (5, 54), (40, 4), (7, 22), (9, 96), (60, 89), (12, 29), (59, 26), (24, 20), (20, 72), (64, 61), (0, 72), (35, 92), (61, 51), (36, 60), (25, 42), (21, 87), (47, 12), (67, 24), (21, 82), (5, 76), (49, 34), (94, 69), (14, 61), (74, 70), (29, 99), (60, 35), (9, 21), (84, 59)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "best_3_moves_hard_8",
    "prompt": "You are given a chess position using this FEN: k3r3/1bR1b1p1/1p2Qn1p/p2p1P2/1q1P1B2/5NP1/6KP/2R5 b - - 3 30\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "knight_path_hard_10",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (55, 49)\nTarget Squares: [(34, 64), (49, 24), (68, 89), (47, 25), (29, 57), (48, 97), (48, 15), (47, 18), (2, 86), (59, 10), (32, 23), (8, 90), (28, 30), (73, 48), (28, 54), (34, 34), (35, 17), (29, 19), (91, 94), (96, 84), (79, 16), (80, 1), (32, 43), (70, 2), (99, 26), (55, 54), (24, 34), (11, 82), (58, 28), (35, 70)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_11",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (62, 80)\nTarget Squares: [(22, 22), (60, 92), (77, 79), (80, 92), (33, 90), (56, 32), (82, 53), (85, 31), (90, 57), (45, 56), (21, 91), (78, 69), (97, 26), (85, 40), (46, 38), (12, 26), (21, 50), (93, 28), (52, 43), (64, 78), (53, 37), (34, 39), (5, 52), (41, 90), (27, 34), (70, 78), (10, 89), (77, 66), (94, 21), (49, 94)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_12",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (36, 11)\nTarget Squares: [(65, 93), (88, 46), (15, 55), (22, 13), (5, 39), (56, 70), (98, 46), (28, 53), (30, 36), (23, 79), (48, 80), (48, 10), (61, 42), (20, 29), (31, 4), (88, 3), (1, 51), (1, 26), (68, 85), (55, 31), (87, 51), (66, 61), (56, 39), (87, 79), (90, 30), (94, 51), (52, 61), (71, 29), (72, 12), (31, 97)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_13",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (33, 81)\nTarget Squares: [(35, 34), (36, 75), (49, 45), (7, 84), (40, 28), (43, 83), (20, 23), (84, 81), (86, 93), (64, 20), (53, 86), (9, 46), (20, 2), (29, 77), (26, 23), (33, 79), (31, 71), (65, 81), (86, 32), (54, 16), (7, 79), (86, 31), (13, 25), (77, 28), (64, 80), (74, 0), (98, 90), (0, 65), (78, 61), (40, 64)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_14",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (37, 94)\nTarget Squares: [(17, 43), (11, 20), (12, 96), (21, 99), (25, 64), (24, 10), (17, 16), (66, 90), (33, 47), (60, 40), (96, 17), (63, 54), (23, 67), (86, 8), (19, 78), (14, 29), (36, 31), (94, 76), (97, 58), (45, 65), (21, 65), (67, 23), (17, 38), (43, 20), (21, 11), (60, 49), (12, 12), (16, 71), (23, 34), (95, 4)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_15",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (33, 69)\nTarget Squares: [(19, 93), (60, 93), (65, 64), (56, 41), (66, 19), (41, 69), (83, 88), (71, 34), (81, 95), (1, 17), (46, 16), (83, 50), (44, 90), (66, 35), (49, 37), (98, 62), (75, 45), (42, 99), (26, 51), (43, 28), (9, 39), (37, 27), (75, 61), (84, 82), (61, 58), (76, 8), (46, 99), (6, 42), (53, 12), (92, 7)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_16",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (15, 84)\nTarget Squares: [(71, 42), (71, 27), (5, 72), (61, 85), (69, 24), (39, 76), (35, 96), (46, 92), (26, 67), (86, 7), (43, 62), (89, 48), (89, 96), (80, 76), (42, 90), (44, 57), (55, 10), (66, 53), (20, 78), (65, 61), (32, 39), (78, 88), (1, 77), (19, 52), (23, 58), (14, 71), (11, 17), (1, 84), (73, 70), (61, 77)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_17",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (19, 4)\nTarget Squares: [(35, 78), (12, 16), (88, 80), (2, 85), (66, 35), (71, 34), (98, 1), (22, 68), (0, 40), (3, 1), (6, 93), (46, 12), (99, 92), (70, 62), (24, 89), (57, 64), (10, 9), (50, 73), (84, 44), (94, 23), (63, 80), (8, 50), (9, 18), (76, 99), (10, 69), (46, 91), (96, 92), (90, 25), (91, 51), (93, 78)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  },
  {
    "question_id": "knight_path_hard_18",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format:\n\nStarting Postion: (68, 6)\nTarget Squares: [(73, 65), (54, 90), (18, 99), (7, 20), (79, 18), (51, 32), (97, 54), (65, 42), (62, 79), (20, 87), (51, 81), (27, 34), (46, 17), (56, 9), (21, 28), (19, 9), (60, 66), (86, 59), (11, 30), (69, 55), (90, 85), (75, 90), (98, 4), (37, 72), (25, 28), (19, 0), (41, 55), (71, 6), (69, 85), (15, 60)]\n\nReturn your answer in the format: solution = <integer>",
    "problem": {


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/.github/workflows/ci.yml =====

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install package
        run: |
          uv pip install --system -e ".[dev]"

      - name: Verify CLI entry point
        run: |
          sia --help

      - name: Verify package imports
        run: |
          python -c "from sia.orchestrator import main, load_agent_execution; print('orchestrator OK')"
          python -c "from sia.context_manager import ContextManager; print('context_manager OK')"
          python -c "from sia.util import run_agent; print('util OK')"

      - name: Build package
        run: |
          uv pip install --system build
          python -m build --sdist --wheel

      - name: Verify built artifacts
        run: |
          ls -la dist/
          test -f dist/*.tar.gz
          test -f dist/*.whl

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12","3.13", "3.14"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install package with test dependencies
        run: |
          uv pip install --system -e ".[dev]"

      - name: Run tests
        run: |
          python -m pytest tests/ -v

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install linters
        run: |
          uv pip install --system ruff ty

      - name: Ruff check
        run: ruff check sia/ tests/

      - name: Ruff format check
        run: ruff format --check sia/ tests/

      - name: Type check with ty
        run: ty check sia/


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/.github/workflows/publish.yml =====

name: Publish to PyPI

on:
  push:
    tags: ["v*"]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13", "3.14"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install package with test dependencies
        run: uv pip install --system -e ".[dev]"

      - name: Run tests
        run: python -m pytest tests/ -v

  publish:
    needs: test
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Verify tag matches package version
        run: |
          TAG="${GITHUB_REF#refs/tags/v}"
          PKG_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
          if [ "$TAG" != "$PKG_VERSION" ]; then
            echo "ERROR: Tag v$TAG does not match pyproject.toml version $PKG_VERSION"
            exit 1
          fi
          echo "Tag v$TAG matches package version $PKG_VERSION"

      - name: Build package
        run: |
          uv pip install --system build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/environment.yml =====

name: sia
channels:
  - defaults
dependencies:
  - python=3.12
  - pip=23.2.1
  - packaging
  - pip:
    - ipykernel


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/CONTRIBUTING.md =====

# Contributing to SIA

Thank you for your interest in contributing to SIA (Self-Improving AI). This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/hexo-ai/sia/issues/new) with:

- A clear, descriptive title
- Steps to reproduce the problem
- Expected vs actual behavior
- Python version and OS
- Relevant logs or error messages

### Feature Requests

Have an idea for a new feature or improvement? [Open an issue](https://github.com/hexo-ai/sia/issues/new) and describe:

- What you'd like to see added or changed
- Why it would be useful
- Any implementation ideas you have

### Submitting Changes

1. Fork the repository
2. Create a branch from `master` (`git checkout -b my-change`)
3. Make your changes
4. Run the checks (see below)
5. Commit with a clear message describing the change
6. Push to your fork and open a pull request against `master`

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/sia.git
cd sia

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode with all extras
pip install -e ".[dev]"
```

## Running Checks

All of these must pass before submitting a PR:

```bash
# Run tests
python -m pytest tests/ -v

# Lint
ruff check sia/ tests/

# Format check
ruff format --check sia/ tests/

# Type check
ty check sia/
```

To auto-fix lint and formatting issues:

```bash
ruff check --fix sia/ tests/
ruff format sia/ tests/
```

## Adding a New Task

To add a new task for SIA to work on, create the following structure:

```
tasks/<task-name>/
  data/
    public/
      task.md          # Task specification (required)
      evaluate.py      # Evaluation script (recommended)
    private/
      <ground-truth>   # Private evaluation data
  reference/
    reference_target_agent.py      # Agent template (required)
    SAMPLE_TASK_DESCRIPTIONS.md    # Similar task examples (required)
```

See existing tasks (`tasks/spaceship-titanic/`, `tasks/lawbench/`) for examples. The test suite validates that all tasks follow this structure.

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting (configured in `pyproject.toml`)
- Line length limit is 120 characters
- Use type hints where they aid clarity
- Follow existing patterns in the codebase

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/EVALUATION_GUIDE.md =====

# Evaluation Guide

## Overview

After each generation, the orchestrator automatically runs evaluation:

1. Target agent saves output to generation directory (e.g., `gen_1/submission.csv`)
2. Orchestrator runs: `python evaluate.py --gen-dir gen_1/`
3. Your `evaluate.py` finds the submission file, evaluates it, and saves `results.json`
4. Orchestrator loads `results.json` and adds metrics to feedback prompt

## Location

Place `evaluate.py` in: `tasks/<task_name>/data/public/evaluate.py`

## What You Need to Write

Your `evaluate.py` must have an `evaluate()` function:

```python
from pathlib import Path

def evaluate(submission_path: Path) -> dict:
    """
    Load submission file, evaluate against ground truth, return metrics.

    Args:
        submission_path: Path to the submission file (e.g., gen_1/submission.csv)

    Returns:
        dict with your metrics (any structure you want)
    """
    # 1. Load the submission file (you decide the format)
    # 2. Load ground truth from data/private/
    # 3. Compare and calculate metrics
    # 4. Return dict with results

    return {
        "accuracy": 0.85,
        "n_correct": 170,
        "n_total": 200
    }
```

## Complete Example

```python
"""Evaluate predictions against ground truth."""

import pandas as pd
from pathlib import Path

# Path to ground truth (private data)
TASK_DIR = Path(__file__).parent.parent.parent  # Go up from data/public/
TRUTH_PATH = TASK_DIR / "data/private/test.csv"


def evaluate(submission_path: Path) -> dict:
    """Evaluate submission against ground truth."""

    # Load ground truth
    truth = pd.read_csv(TRUTH_PATH)

    # Load submission
    pred = pd.read_csv(submission_path)

    # Merge and calculate accuracy
    merged = truth.merge(pred, on="id", how="left")
    correct = (merged["label"] == merged["prediction"]).sum()
    total = len(merged)
    accuracy = correct / total

    return {
        "accuracy": float(accuracy),
        "n_correct": int(correct),
        "n_total": int(total)
    }


def main():
    """For manual testing."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--gen-dir", type=Path, required=True)
    args = parser.parse_args()

    # Find submission file (YOU handle this - check for whatever filename you expect)
    submission = args.gen_dir / "submission.csv"
    if not submission.exists():
        print(f"Error: {submission} not found")
        sys.exit(1)

    # Evaluate
    print("Evaluating...")
    results = evaluate(submission)

    # IMPORTANT: Save results.json (required by orchestrator)
    results_path = args.gen_dir / "results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {results_path}")

    # Print summary
    print(f"Accuracy: {results['accuracy']:.4f}")


if __name__ == "__main__":
    main()
```

## Key Points

1. **Orchestrator passes `--gen-dir`**: Your script receives the generation directory path
2. **YOU find the submission file**: Check for whatever filename you told the agent to create (e.g., `submission.csv`)
3. **YOU save `results.json`**: Write the results dict to `gen_dir/results.json` - orchestrator expects this file
4. **Ground truth in `data/private/`**: Store ground truth here so agents can't access it
5. **Return format is flexible**: Any dict structure works - top-level scalars will be shown in context.md

## Testing

Test before running the orchestrator:

```bash
python tasks/<task_name>/data/public/evaluate.py --gen-dir runs/run_1/gen_1
```

Make sure `results.json` gets created with your metrics!


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/README.md =====

# SIA (Self-Improving AI)

[![arXiv](https://img.shields.io/badge/arXiv-2605.27276-b31b1b.svg)](https://arxiv.org/abs/2605.27276)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/pypi/v/sia-agent.svg)](https://pypi.org/project/sia-agent/)

<p align="center">
  <a href="https://star-history.com/#hexo-ai/sia&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hexo-ai/sia&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hexo-ai/sia&type=Date" />
      <img alt="SIA Star History Chart" src="https://api.star-history.com/svg?repos=hexo-ai/sia&type=Date" width="600" />
    </picture>
  </a>
</p>

Official implementation of [**SIA: Self Improving AI with Harness & Weight Updates**](https://arxiv.org/abs/2605.27276) (Hebbar et al., 2026) — a self-improving loop where a language-model agent updates both the harness and the weights of a task-specific agent. The paper reports a 56.6% gain on LawBench, 91.9% runtime reduction on GPU kernels, and 502% improvement on single-cell RNA denoising over baseline.

SIA is a Self Improving AI framework to autonomously improve the performance of any AI system (Model / Agent) on a benchmark task.

> **Just want to try it?** Skip to [Run SIA locally](#2-run-sia-locally-with-built-in-tasks).

## Introduction Videos

- [SIA setup](https://www.loom.com/share/be0534bc818d408bab937033c6457ec9)
- [SIA Runs Visualizer](https://www.loom.com/share/5b1dc2dc858b4493b4b348f0b88d5b9e)

### Architecture

<p align="center"><img src="docs/flow.png" alt="SIA orchestration flow" width="720"></p>
<p align="center"><i>Control flow between Meta, Target, and Feedback agents over successive generations.</i></p>

SIA operates by coordinating three main types of AI agents that work together to continuously improve task performance:

### Glossary
1. **Meta-Agent**: Reads the task description and generates an initial Target Agent tailored to the task.
2. **Target / Task Specific Agent**: Attempts to complete the task and records its actions and results.
3. **Feedback/Improvement Agent**: Reviews the Target Agent's performance logs, identifies improvements, and updates the Target Agent accordingly.

This iterative process allows the system to autonomously refine and enhance its ability to solve scientific tasks.


### Benchmark Results

<p align="center"><img src="docs/mlebench.png" alt="MLE Bench Results" width="720"><br><i>OpenAI MLE-Bench Hard: a gauntlet of real Kaggle ML competitions where agents must write, run, and iterate full ML pipelines. SIA ranks #1 across all generations tested.</i></p>

<p align="center"><img src="docs/lawbench.png" alt="LawBench Results" width="720"><br><i>LawBench: predict the criminal charge from Chinese court case descriptions across 191 charge categories. SIA-W+H reaches 70.1% Top-1 accuracy, beating the prior SOTA of 45%.</i></p>

<p align="center"><img src="docs/trimul_cuda.png" alt="TriMul CUDA Results" width="720"><br><i>AlphaFold-3 TriMul Triton Kernel: implement and optimize the Triangle Multiplicative Update as a Triton kernel, preserving correctness while hitting H100 latency targets. SIA-W+H achieves 14x speedup over baseline.</i></p>

<p align="center"><img src="docs/denoising.png" alt="Denoising Results" width="720"><br><i>scRNA-seq Denoising: impute missing gene expression values in single-cell RNA sequencing data. SIA-W+H scores 0.289 MSE<sub>norm</sub>, surpassing the prior SOTA of 0.220.</i></p>

---

## Run SIA locally with built-in tasks

SIA ships with four built-in tasks: `gpqa`, `lawbench`, `longcot-chess`, `spaceship-titanic`.

### Install

Pick the agent impl that matches the LLMs you want to run.

**Claude agent impl** (Claude Agent SDK, Claude models only):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install 'sia-agent[claude]'
export ANTHROPIC_API_KEY="..."
```

**OpenHands agent impl** (multi-provider — Gemini, OpenAI, Anthropic, etc.):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install 'sia-agent[openhands]'

# Export the key(s) for the provider(s) you'll use:
export ANTHROPIC_API_KEY="..."   # for anthropic/* models
export GEMINI_API_KEY="..."      # for gemini/* models (or GOOGLE_API_KEY)
export OPENAI_API_KEY="..."      # for openai/* models
```

Full provider/model reference: [docs/configuration.md](docs/configuration.md#api-keys).

### Run

The CLI has two sub-commands: **`sia run`** (the self-improvement loop) and
**`sia web`** (the runs visualizer, see [Visualize runs](#visualize-runs)).

```bash
sia run --task gpqa --max_gen 5 --run_id 1
```

Swap `--task` for any of the four bundled tasks. (`sia --task ...` without the
`run` sub-command still works and is treated as `sia run ...`.)

Artifacts land in `runs/run_{run_id}/gen_{n}/`:
- `target_agent.py` — the agent for that generation
- `agent_execution.json` — execution logs
- `improvement.md` — diff rationale (gen 2+)

While a run is in progress a **live dashboard** auto-starts at
`http://127.0.0.1:8000` (requires the `web` extra; disable with `--no-web`).

### Common flags (`sia run`)

| Flag | Default | Description |
|---|---|---|
| `--task` | — | Bundled task name (mutually exclusive with `--task_dir`) |
| `--task_dir` | — | Path to an external task directory |
| `--max_gen` | 3 | Number of self-improvement generations |
| `--run_id` | 1 | Unique run identifier |
| `--meta-agent-profile` | `default-meta` | Profile for the meta/feedback agent (name or path to a `.json`) |
| `--target-agent-profile` | `default-target` | Profile for the target agent (name or path to a `.json`) |
| `--no-web` | off | Don't auto-start the live dashboard during the run |
| `--web-port` | 8000 | Port for the live dashboard (`--web-host` to change the bind host) |

The model, agent impl, and provider for each agent come from a **profile** (see below). For example,
to evaluate Kimi-K2.6 on Nebius as the target model:

```bash
export NEBIUS_API_KEY="..."        # + ANTHROPIC_API_KEY for the default meta agent
sia run --task gpqa --target-agent-profile kimi-nebius-target --max_gen 5 --run_id 2
```

Full agent-impl, model, and API-key reference: [docs/configuration.md](docs/configuration.md). Hit a snag? [docs/troubleshooting.md](docs/troubleshooting.md).

### Visualize runs

A built-in web dashboard renders everything under `runs/`: the per-generation
target-agent code (syntax-highlighted), meta/feedback prompts, improvement
plans, evaluation scores (with an accuracy-across-generations chart and
per-domain breakdown), execution trajectories, and logs.

```bash
sia web                          # serve ./runs at http://127.0.0.1:8000
sia web --runs-dir ./runs --port 8080
```

It also starts automatically alongside `sia run` (disable with `--no-web`), so
you can watch generations land live.

| Flag | Default | Description |
|---|---|---|
| `--runs-dir` | `./runs` | Directory of runs to visualize |
| `--host` | `127.0.0.1` | Bind host |
| `--port` | 8000 | Bind port |
| `--no-browser` | off | Don't open a browser window automatically |

### Author your own profile

A **provider** is an endpoint + credentials; a **profile** configures one agent role. A meta-agent
profile bundles `(agent_impl, model, provider)`; a target-agent profile bundles `(model, provider,
agent_reference)`. Both are JSON files — bundled defaults live in `sia/defaults/{providers,profiles}/`,
and you can add your own under `./providers/` and `./profiles/` (or set `$SIA_PROVIDERS_DIR` /
`$SIA_PROFILES_DIR`). No code change required.

```bash
mkdir -p providers profiles
```

```jsonc
// providers/my-endpoint.json   — an OpenAI-compatible provider
{
  "provider_id": "my-endpoint",
  "name": "My Endpoint",
  "client_kind": "openai",                 // anthropic | openai | google
  "base_url": "https://api.example.com/v1",
  "api_key_env": "MY_ENDPOINT_API_KEY"
}
```

```jsonc
// profiles/my-target.json      — the target agent's model + provider + reference
{
  "profile_id": "my-target",
  "name": "My model on My Endpoint",
  "model": "vendor/my-model",
  "provider_id": "my-endpoint",             // references the provider above


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/SECURITY.md =====

# Security Model

## Agent Execution

SIA spawns AI agents that can execute code on the host system. The security implications depend on the execution mode.

### Execution Modes

| Mode | Flag | Isolation | Risk Level |
|------|------|-----------|------------|
| Direct | `--sandbox none` (default) | None | High |
| Docker | `--sandbox docker` | Container + no network | Low |

### Direct Mode (default)

In direct mode, the target agent runs as a subprocess with full access to:
- The host filesystem (within the user's permissions)
- Network resources
- Environment variables (including API keys)

This is appropriate for **trusted research environments** where:
- The task data is controlled
- The agent model is trusted
- The execution environment is isolated (VM, container, etc.)

### Docker Sandbox Mode

When `--sandbox docker` is used:
- Target agent runs in a Docker container
- Dataset directory is mounted **read-only**
- Working directory is mounted **read-write**
- Network access is **disabled** (`--network none`)
- Memory and CPU limits are enforced
- The agent cannot access the host filesystem or environment variables

Requirements: Docker must be installed and the user must have permission to run containers.

### bypassPermissions in util.py

The Claude Code SDK agent runner uses `permission_mode="bypassPermissions"`. This is required for automated agent execution -- without it, the agent would pause and wait for human approval on every file operation. This is safe when:
- Operating in a controlled workspace
- Using the Docker sandbox for untrusted tasks
- The agent model is trusted

## Reference Agent Templates

Files in `sia/tasks/_shared/` and `sia/tasks/*/reference/` are **template code** that the meta-agent reads and uses as examples. They use `subprocess.run(shell=True)` because they are not executed by the framework directly -- they are rewritten by the meta-agent into new target agents.

## Reporting

Report security vulnerabilities to security@hexo.ai.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/docs/architecture.md =====

# Architecture

SIA coordinates three AI agents in a loop. Each generation, the system inspects the previous attempt, rewrites the agent, and runs it again.

## The three agents

1. **Meta-Agent** — Reads the task description and generates the initial Target Agent tailored to the task.
2. **Target Agent** — Attempts to complete the task and records its actions and results.
3. **Feedback / Improvement Agent** — Reviews the Target Agent's execution logs, identifies improvements, and rewrites the Target Agent for the next generation.

## What happens during a run

**Generation 1:**
- Meta-agent reads the task and writes `target_agent.py`
- Target agent executes the task and logs to `agent_execution.json`
- Feedback agent analyzes the run and writes an improved agent for Gen 2

**Generation 2 through N:**
- The current generation's target agent executes the task
- The feedback agent analyzes and produces the next generation
- Continues until `--max_gen` is reached

**Output:**
- All artifacts saved under `runs/run_{run_id}/gen_{n}/`
- Each generation has its own `target_agent.py` and `agent_execution.json`
- Improvement notes land in `improvement.md` (gen 2 onwards)

## Directory layout

```
sia/
├── sia/
│   ├── orchestrator.py             # Main orchestration logic
│   ├── context_manager.py          # Run/context tracking
│   ├── util.py                     # Agent runner utilities
│   ├── prepare_mlebench_dataset.py # MLE-Bench dataset preparation
│   └── tasks/                      # Bundled with the wheel
│       ├── _shared/
│       │   ├── reference_target_agent.py
│       │   └── sample_agent_execution.json
│       └── {task-id}/              # gpqa, lawbench, longcot-chess, spaceship-titanic
│           ├── data/
│           │   ├── public/         # Public dataset
│           │   │   ├── task.md         # Task description
│           │   │   └── *.csv           # Data files
│           │   └── private/        # Held-out evaluation data
│           └── reference/
│               ├── SAMPLE_TASK_DESCRIPTIONS.md
│               └── reference_target_agent.py
└── runs/                           # Generated during execution
    └── run_{id}/
        ├── venv/                   # Isolated Python environment per run
        └── gen_{n}/                # Each generation's artifacts
            ├── target_agent.py
            ├── agent_execution.json
            └── improvement.md      # gen 2 onwards
```

## Customizing prompts

The two prompts that drive self-improvement live in [`sia/orchestrator.py`](../sia/orchestrator.py):

- `META_AGENT_PROMPT` — controls how the initial Target Agent is created
- `FEEDBACK_AGENT_PROMPT` — controls how improvements are suggested


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/docs/configuration.md =====

# Configuration

Full reference for SIA's agent **profiles**, **providers**, and command-line arguments.

## Command-line arguments

SIA has two sub-commands: **`sia run`** (the self-improvement loop) and **`sia web`**
(the runs visualizer, see [Visualizing runs](#visualizing-runs)). For backward
compatibility, `sia <flags>` with no sub-command is treated as `sia run <flags>`.

### `sia run`

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--task` | one of | — | Name of a bundled task: `gpqa`, `lawbench`, `longcot-chess`, `spaceship-titanic` |
| `--task_dir` | one of | — | Path to an external task directory (mutually exclusive with `--task`) |
| `--max_gen` | no | `3` | Number of self-improvement generations |
| `--run_id` | no | `1` | Unique run identifier |
| `--meta-agent-profile` | no | `default-meta` | Profile for the meta/feedback agent (name or path to a `.json`) |
| `--target-agent-profile` | no | `default-target` | Profile for the target agent (name or path to a `.json`) |
| `--focus` | no | `harness` | Improvement focus: `harness` (code/prompt changes) or `weights` (RL-based tuning) |
| `--training_sandbox` | no | `modal` | Sandbox environment for code execution during training rollouts (weights mode): `modal` (default) or `sandboxfusion` |
| `--sandbox` | no | `none` | Target-agent isolation: `none` or `docker` |
| `--no-web` | no | off | Don't auto-start the live dashboard during the run |
| `--web-host` | no | `127.0.0.1` | Bind host for the live dashboard |
| `--web-port` | no | `8000` | Bind port for the live dashboard |

### `sia web`

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--runs-dir` | no | `./runs` | Directory of runs to visualize |
| `--host` | no | `127.0.0.1` | Bind host |
| `--port` | no | `8000` | Bind port |
| `--no-browser` | no | off | Don't open a browser window automatically |

There are two agent roles, each selected by a profile:

- the **meta/feedback agent** runs *inside* SIA via an agent impl (`claude` / `openhands` /
  `pydantic-ai`) — selected with `--meta-agent-profile`;
- the **target agent** is *generated code* SIA never runs as an engine — its model/provider come
  from `--target-agent-profile`, and the meta-agent refactors that profile's `agent_reference`
  (the seed code) to the provider's SDK and iteratively improves it.

## Profiles and providers

Configuration is **declarative JSON** you can extend without touching code.

### Provider — an endpoint + credentials

```jsonc
// sia/defaults/providers/nebius.json
{
  "provider_id": "nebius",                                   // stable id (also the filename stem)
  "name": "Nebius Token Factory",                            // human-readable display name
  "client_kind": "openai",                                   // anthropic | openai | google
  "base_url": "https://api.tokenfactory.us-central1.nebius.com/v1/",
  "api_key_env": "NEBIUS_API_KEY"
}
```

Bundled providers: `anthropic`, `gemini`, `openai`, `together`, `nebius`.

### Profiles — one per agent role

A **meta-agent profile** bundles `(agent_impl, model, provider)`:

```jsonc
// sia/defaults/profiles/kimi-nebius-meta.json
{
  "profile_id": "kimi-nebius-meta", // stable id (also the value you pass to --meta-agent-profile)
  "name": "Kimi K2.6 on Nebius",    // human-readable display name
  "agent_impl": "openhands",        // claude | openhands | pydantic-ai
  "model": "moonshotai/Kimi-K2.6",
  "provider_id": "nebius"           // references a provider by its provider_id
}
```

A **target-agent profile** bundles `(model, provider, agent_reference)` — no agent impl, because
SIA never runs the target as an engine; it generates and improves the code:

```jsonc
// sia/defaults/profiles/kimi-nebius-target.json
{
  "profile_id": "kimi-nebius-target", // stable id (also the value you pass to --target-agent-profile)
  "name": "Kimi K2.6 on Nebius",
  "model": "moonshotai/Kimi-K2.6",
  "provider_id": "nebius",
  "agent_reference": "default"        // "default" = the task package's reference; see below
}
```

Each file carries both a stable `*_id` (used for references and on the CLI — keep it equal to the
filename stem so name lookups resolve) and a friendly `name` for display.

Bundled profiles:

| Profile | role | agent_impl / reference | model | provider |
|---------|------|------------------------|-------|----------|
| `default-meta` | meta | `agent_impl: claude` | `haiku` | `anthropic` |
| `default-target` | target | `agent_reference: default` | `claude-haiku-4-5-20251001` | `anthropic` |
| `kimi-nebius-meta` | meta | `agent_impl: openhands` | `moonshotai/Kimi-K2.6` | `nebius` |
| `kimi-nebius-target` | target | `agent_reference: default` | `moonshotai/Kimi-K2.6` | `nebius` |

### agent_reference — the target agent's seed code + deps

A target-agent profile's `agent_reference` is the improvable seed the meta-agent starts from and the
feedback-agent rewrites each generation:

- `"default"` — the task package's bundled `reference/` directory (entrypoint
  `reference_target_agent.py`). This is the historical behavior.
- `{ "source": "./my_agent.py" }` — a single user file; its text is embedded in the meta prompt.
- `{ "source": "./my_agent_dir/", "entrypoint": "main.py" }` — a multi-file directory copied into
  each generation's working dir; the agent reads it with its own tools rather than via the prompt.

Dependencies live in a `requirements.txt` **inside the reference** (not a profile field), installed
per generation on top of the baseline packages — so the meta/feedback agents can evolve them.

### Resolution — name or path

A profile/provider value that contains `/` or ends in `.json` is loaded as a **file path**.
Otherwise a bare **name** resolves in order:

1. the user directory — `$SIA_PROFILES_DIR` / `$SIA_PROVIDERS_DIR`, else `./profiles` / `./providers`;
2. the bundled defaults shipped in the package.

Add your own by dropping a JSON file in `./providers/` or `./profiles/` (no code change):

```bash
sia run --task gpqa --target-agent-profile kimi-nebius-target   # bundled name
sia run --task gpqa --target-agent-profile ./profiles/mine.json # explicit path
```

## Running

### Default (Claude target, Claude meta)

```bash
sia run --task gpqa --max_gen 5 --run_id 1
```

Claude model shortcuts (used by the `claude` agent impl and `claude-*` target models):
`haiku` → `claude-haiku-4-5-20251001`, `sonnet` → `claude-sonnet-4-5-20250929`,
`opus` → `claude-opus-4-5-20251101`.

### Kimi-K2.6 on Nebius as the target model

```bash
export NEBIUS_API_KEY="..."        # target provider
export ANTHROPIC_API_KEY="..."     # default-meta agent
sia run --task gpqa --target-agent-profile kimi-nebius-target --max_gen 5 --run_id 2
```

The meta-agent refactors the reference agent to call the `openai` SDK at the Nebius
`base_url` with `NEBIUS_API_KEY` (dollar-cost is reported as 0 — per-provider pricing is unknown).

### Pointing the meta/feedback agent at another provider

The `claude` agent impl is Anthropic-only (a profile pairing `agent_impl: claude` with a non-anthropic
provider is rejected at load time). To run the meta agent elsewhere, author a profile with the
`openhands` or `pydantic-ai` agent impl:

```jsonc
// ./profiles/gemini-meta.json
{ "profile_id": "gemini-meta", "name": "Gemini meta agent", "agent_impl": "openhands",
  "model": "gemini/gemini-3.1-pro-preview", "provider_id": "gemini" }
```

```bash
sia run --task gpqa --meta-agent-profile gemini-meta
```

Agent-impl model-spec conventions: OpenHands uses fully-qualified `provider/model`
(`gemini/gemini-3.1-pro-preview`, `openai/gpt-4`); PydanticAI uses native specs
(`openai:gpt-4o`, `anthropic:claude-sonnet-4-5-20250929`, `google-gla:gemini-3.1-pro-preview`).
Install the PydanticAI extra with `pip install 'sia-agent[pydantic-ai]'`.

## API keys

Set the `api_key_env` for each provider you use (the orchestrator warns at startup if one is unset):


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/docs/troubleshooting.md =====

# Troubleshooting

## "Run directory already exists"

The orchestrator refuses to overwrite an existing run. Either:

- Use a different `--run_id`, or
- Delete the existing run: `rm -rf runs/run_1`

## Target agent fails during execution

Check the logs in the generation directory:

```bash
cat runs/run_1/gen_1/agent_execution.json
```

Common causes:

- Dataset paths are wrong — make sure absolute paths are used in your task
- Required Python packages are missing from the per-run venv
- The `api_key_env` for your profile's provider is not set (e.g. `ANTHROPIC_API_KEY` for the
  default profiles, `NEBIUS_API_KEY` for `kimi-nebius`) — the orchestrator warns at startup

## `ImportError: No module named 'anthropic'`

SIA creates a fresh venv per run. If packages are missing:

1. Check the venv creation step in the orchestrator logs
2. Install manually into that venv:
   ```bash
   runs/run_1/venv/bin/pip install anthropic
   ```

## "No GEMINI_API_KEY environment variable set"

This only affects `prepare_mlebench_dataset.py` when it tries to generate similar task descriptions. Either:

- Set the variable: `export GEMINI_API_KEY="..."`
- Or skip that step: pass `--skip-gemini`

## `PermissionError: Kaggle authentication failed!`

`mle-bench` downloads competitions via the Kaggle API and needs credentials. Two ways to provide them:

- Env vars: `export KAGGLE_USERNAME="..." KAGGLE_KEY="..."`
- File: drop the API token from Kaggle (Account → Create New Token) at `~/.kaggle/kaggle.json`

You also need to accept the competition's rules on Kaggle's website before `mlebench prepare -c <competition>` can fetch it.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/docs/walkthrough.md =====

# Walkthrough: building a custom task

A detailed, step-by-step guide for preparing your own dataset and running SIA against it. For the short version, see the [Bring your own task](../README.md#3-bring-your-own-task) section of the README.

## Step 1: Set up the task directory

Create the layout SIA expects:

```bash
mkdir -p my-tasks/gpqa/{data/public,data/private,reference}
```

### Add your dataset and task description

Place dataset files in the appropriate folders:

```bash
# Public inputs — the agent is allowed to see these
cp questions.json my-tasks/gpqa/data/public/

# Private answers / ground truths — held out from the agent
cp answers.json my-tasks/gpqa/data/private/
```

> **Note:** The LLM is **not** told about `data/private/` during evaluation. This prevents the agent from cheating and ensures fair scoring.

Write the task description in `my-tasks/gpqa/data/public/task.md`. SIA's meta-agent reads this file to understand what to build.

### Copy the reference agent template

From a clone of this repo:

```bash
cp sia/tasks/_shared/reference_target_agent.py my-tasks/gpqa/reference/
```

### (Optional) Add sample task descriptions

Create `my-tasks/gpqa/reference/SAMPLE_TASK_DESCRIPTIONS.md` with examples of similar tasks. This helps the meta-agent generalize and reduces overfitting to the exact phrasing of `task.md`.

## Step 2: Run the orchestrator

External custom task:

```bash
sia run --task_dir ./my-tasks/gpqa --max_gen 5 --run_id 1
```

Bundled task (for comparison):

```bash
sia run --task gpqa --max_gen 5 --run_id 1
```

With a meta agent on OpenHands + Gemini (author `./profiles/gemini-meta.json` with
`"agent_impl": "openhands"`, `"model": "gemini/gemini-3.1-pro-preview"`, `"provider_id": "gemini"`):

```bash
sia run \
  --task_dir ./my-tasks/gpqa \
  --max_gen 5 \
  --run_id 1 \
  --meta-agent-profile gemini-meta
```

See [configuration.md](configuration.md) for the full profile/provider schema and more examples.

## Step 3: Analyze results

```bash
# View execution logs for a generation
cat runs/run_1/gen_1/agent_execution.json

# View improvements the feedback agent proposed
cat runs/run_1/gen_2/improvement.md

# Diff successive agent versions
diff runs/run_1/gen_1/target_agent.py runs/run_1/gen_2/target_agent.py
```

Or browse it all in the web dashboard:

```bash
sia web                  # → http://127.0.0.1:8000
```

The dashboard also auto-starts during `sia run`, so you can watch generations
land live (disable with `--no-web`).

## Task directory requirements

Every task directory — bundled or custom — must look like this:

```
{task-id}/
├── data/
│   ├── public/
│   │   ├── task.md                    # Task description (orchestrator reads this)
│   │   ├── train.csv
│   │   ├── test.csv
│   │   └── sample_submission.csv
│   └── private/
│       └── ...                        # Held-out evaluation data
└── reference/
    ├── SAMPLE_TASK_DESCRIPTIONS.md    # Similar tasks (for meta-agent context)
    └── reference_target_agent.py      # Template agent structure
```

## Preparing an MLE-Bench task

The `prepare_mlebench_dataset.py` script automates the steps above for any MLE-Bench competition. First install the extras (mle-bench is not on PyPI):

```bash
pip install 'sia-agent[mlebench]'
pip install git+https://github.com/openai/mle-bench
export KAGGLE_USERNAME="..." KAGGLE_KEY="..."   # mle-bench downloads via the Kaggle API
export GEMINI_API_KEY="..."                     # optional; required only without --skip-gemini
```

Kaggle credentials come from your account's API token (Kaggle → Account → Create New Token); the downloaded `kaggle.json` can also live at `~/.kaggle/kaggle.json` instead of env vars. Accept the competition's rules on Kaggle first or `mlebench prepare` will fail to download it.

Then run:

```bash
python -m sia.prepare_mlebench_dataset -c "spaceship-titanic"
```

This will:

1. Run `mlebench prepare -c "spaceship-titanic"`
2. Copy public and private datasets from `~/.cache/mle-bench/data/prepared/`
3. Rename `description.md` → `task.md` in `data/public/`
4. Use Gemini to generate similar task descriptions (optional)
5. Create `SAMPLE_TASK_DESCRIPTIONS.md` in `reference/`
6. Copy `reference_target_agent.py` from `_shared/` into `reference/`

**Options:**

- `--skip-gemini` — Skip the Gemini API call for similar tasks
- `--tasks-dir PATH` — Custom tasks directory (default: `./tasks`)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/data/public/task.md =====

# GPQA-style benchmark (`diamond_questions.json`)

You are evaluated on **how many questions you answer correctly** on a fixed set of **graduate-level** multiple-choice items in the spirit of [GPQA](https://arxiv.org/abs/2311.12022): biology, chemistry, physics, and related domains at expert difficulty.

## Data

Each record in `diamond_questions.json` has:

- `id` — stable question identifier
- `domain`, `subdomain` — topic labels
- `Question` — stem (may include LaTeX-style notation or units)
- `options` — dictionary with keys `A`, `B`, `C`, `D` mapping to option text

The options are **pre-shuffled deterministically** (seeded on question text), so the correct answer is already randomly distributed across A-D. You must output which letter (`A`, `B`, `C`, or `D`) corresponds to the option you believe is correct.

## Objective

**Maximize the number of correct answers** over the full dataset. Accuracy (correct / attempted) is the primary success metric. Failed or invalid responses count against you as incorrect or errors depending on the harness.

## Output Format

Your agent must save results to `results/submission.json` (or timestamped filename) with this structure:

```json
{
  "model": "model_name",
  "dataset_config": "diamond_qna",
  "total_questions": 198,
  "errors": 0,
  "total_input_tokens": 12345,
  "total_output_tokens": 5678,
  "total_reasoning_tokens": 0,
  "total_cost_usd": 1.234,
  "timestamp": "2025-05-27T10:00:00",
  "details": [
    {
      "question_id": 1,
      "model_answer": "A",
      "model_answer_raw": "{\"answer\": \"A\"}",
      "input_tokens": 100,
      "output_tokens": 10,
      "reasoning_tokens": 0,
      "cost_usd": 0.01
    }
  ]
}
```

**Required fields in `details`:**
- `question_id` — matches the `id` from the dataset
- `model_answer` — single letter `A`, `B`, `C`, or `D`

**Optional fields** (for tracking):
- `model_answer_raw` — raw model output before parsing
- Token counts and costs (if available)

For errors, include `{"question_id": N, "error": "error message"}` instead.

## Model

Use **`models/gemini-3.1-flash-lite`** (Google Gemini) as the solver for each question. Configure generation so the model returns a **valid, parseable choice** (for example structured JSON `{"answer": "A"}` with `A`–`D` only).

## Constraints

- Answer **only** from the four given option strings for that question; do not invent a fifth option.  
- Follow the required output format exactly so automated grading can map your letter to the shuffled options. 
- All questions are independent and should not be kept in a single loop to solve all.
- Questions cannot share context with each other.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/gpqa/reference/SAMPLE_TASK_DESCRIPTIONS.md =====


## Sample Task 1: Physics - Quantum Mechanics

**Question**: A particle is confined to a one-dimensional infinite square well of width L. The particle is in its ground state. What is the probability of finding the particle in the middle third of the well (between L/3 and 2L/3)?

**Options**:
A) 0.333
B) 0.609
C) 0.500
D) 0.195

**Correct Answer**: B) 0.609

**Domain**: Physics
**Subdomain**: Quantum Mechanics

---

## Sample Task 2: Chemistry - Organic Chemistry

**Question**: When 2-methylpropene is treated with HBr in the presence of peroxides, which of the following products is formed as the major product?

**Options**:
A) 2-bromo-2-methylpropane
B) 1-bromo-2-methylpropane
C) 2-bromo-3-methylpropane
D) 1-bromo-1-methylpropane

**Correct Answer**: B) 1-bromo-2-methylpropane

**Domain**: Chemistry
**Subdomain**: Organic Chemistry

---

## Sample Task 3: Biology - Molecular Biology

**Question**: In eukaryotic cells, which of the following RNA polymerases is responsible for transcribing genes that encode proteins?

**Options**:
A) RNA polymerase I
B) RNA polymerase II
C) RNA polymerase III
D) RNA polymerase IV

**Correct Answer**: B) RNA polymerase II

**Domain**: Biology
**Subdomain**: Molecular Biology

---

## Sample Task 4: Physics - Thermodynamics

**Question**: An ideal gas undergoes an adiabatic expansion from state A to state B. During this process, the temperature of the gas decreases from 400 K to 300 K. If the gas has a heat capacity ratio (γ) of 1.4, what is the ratio of the final volume to the initial volume (V_B/V_A)?

**Options**:
A) 1.33
B) 1.54
C) 1.75
D) 2.05

**Correct Answer**: D) 2.05

**Domain**: Physics
**Subdomain**: Thermodynamics

---

## Sample Task 5: Chemistry - Physical Chemistry

**Question**: Consider a galvanic cell with a zinc electrode in 1.0 M Zn²⁺ solution and a copper electrode in 1.0 M Cu²⁺ solution at 25°C. If the standard reduction potentials are E°(Cu²⁺/Cu) = +0.34 V and E°(Zn²⁺/Zn) = -0.76 V, what is the standard cell potential?

**Options**:
A) +0.42 V
B) +1.10 V
C) -0.42 V
D) +0.76 V

**Correct Answer**: B) +1.10 V

**Domain**: Chemistry
**Subdomain**: Physical Chemistry

---

## Task Format

Each question follows the GPQA (Graduate-level Google-Proof Q&A) benchmark format:
- Graduate-level difficulty across STEM domains
- Multiple-choice with exactly 4 options (A, B, C, D)
- Single correct answer
- Requires deep domain knowledge and reasoning
- Often involves calculations, conceptual understanding, or synthesis of multiple concepts

The target agent must:
1. Parse the question and all four options
2. Reason about the problem using domain knowledge
3. Return a single letter answer (A, B, C, or D) in the specified format
4. Handle questions across multiple STEM domains (physics, chemistry, biology, etc.)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/data/public/task.md =====

# LawBench — Criminal Charge Prediction

You are evaluated on **how many criminal charges you predict correctly** from a fixed set of Chinese court case descriptions.

## Background

Each record comes from a real Chinese criminal case. The case description (事实, *facts*) is the text submitted by the procuratorate at trial. Your task is to predict which **criminal charge** (罪名) the court ultimately convicted the defendant of.

## Data

- **test.csv** — in `dataset_dir`; 913 cases to predict (`id`, `text` only)
- **sample_submission.csv** — correct submission format
- **classes.json** — exhaustive list of all 191 valid charge labels

## Objective

**Maximize accuracy** (correct / attempted) across all 913 test cases.

## Evaluation

Your submission will be **automatically evaluated by the orchestrator** after you complete your work.

- Save your predictions as `submission.csv` to your `working_dir`

## Constraints

- Predict **only** from the 191 labels in `classes.json`. Any prediction not in this list counts as wrong.
- Output must be a CSV named `submission.csv` with columns `id` and `label` (exact case-sensitive match).
- All 913 test IDs must appear in your submission.

## Submission Format

```
id,label
0,盗窃
1,故意伤害
2,非法占用农用地
...
```

## Baseline Context

- A zero-shot LLM approach achieves ~7% accuracy (191 classes, hard to guess).
- A strong few-shot harness (Meta-Harness paper) achieves ~45%.
- Your goal is to exceed both — a well-engineered agent should reach 70%+.

## Model

Use **`openai/gpt-oss-120b`** as the solver for all LLM-based predictions.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/data/training_data/task.md =====

# LawBench — Criminal Charge Prediction

You are evaluated on **how many criminal charges you predict correctly** from a fixed set of Chinese court case descriptions.

## Background

Each record comes from a real Chinese criminal case. The case description (事实, *facts*) is the text submitted by the procuratorate at trial. Your task is to predict which **criminal charge** (罪名) the court ultimately convicted the defendant of.

## Data

- **train.csv** — 5,332 labeled cases for training and validation
  - `id` — unique integer ID
  - `text` — Chinese case description (平均 ≈ 400 characters)
  - `label` — criminal charge string (one of 191 valid classes)
- **test.csv** — 913 unlabeled cases to predict
  - `id`, `text` — same as above, **no label column**
- **sample_submission.csv** — correct submission format
- **classes.json** — exhaustive list of all 191 valid charge labels

## Objective

**Maximize accuracy** (correct / attempted) across all 913 test cases.

## Evaluation (required)

After generating predictions, evaluate them by comparing against the ground-truth labels in the private split. Report the resulting accuracy. This check against true solutions is required — do not stop at generating predictions.

## Constraints

- Predict **only** from the 191 labels in `classes.json`. Any prediction not in this list counts as wrong.
- Output must be a CSV named `submission.csv` with columns `id` and `label` (exact case-sensitive match).
- All 913 test IDs must appear in your submission.

## Submission Format

```
id,label
0,盗窃
1,故意伤害
2,非法占用农用地
...
```

## Baseline Context

- A zero-shot LLM approach achieves ~7% accuracy (191 classes, hard to guess).
- A strong few-shot harness (Meta-Harness paper) achieves ~45%.
- Your goal is to exceed both — a well-engineered ML agent should reach 70%+.

## Model

If you use an LLM to generate predictions, use **`claude-haiku-4-5-20251001`** as the solver. For traditional ML approaches (TF-IDF, SVM, etc.), no model restriction applies.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/lawbench/reference/SAMPLE_TASK_DESCRIPTIONS.md =====

# Sample Task Descriptions

These are examples of similar text-classification tasks the target agent may encounter.

**Sample Examples:**

### Example 1: 非法占用农用地 (Illegal Occupation of Agricultural Land)
```
青冈县人民检察院指控，2007年，被告人盛某某和王2某合伙承包位于青冈县中和镇五排六村徐某厂北、大壕南的160亩草原。2015年5月，因为草场草质不好，盛某某同王2某提出，把二人共同承包的草原开垦成耕地，用于种植大豆，王2某表示同意。后盛某某用自家的四轮车私自将承包的草原开垦了56.65亩用于种植大豆。草原破坏程度深度约20公分。该草原现已恢复原始状态。经侦查，被告人盛某某于2016年7月6日向青冈县公安局投案。
```
**Label:** 非法占用农用地

### Example 2: 保险诈骗 (Insurance Fraud)
```
北京市丰台区人民检察院起诉书指控：2014年2月26日，被告人贾×伙同潘×、孙×（均另案处理）经事先预谋，在本市丰台区梆子井村甲37号路边，利用贾×投保的车牌号为京PF1G×丰田汽车故意制造交通事故，后到本市丰台区六里桥中国人民财产保险有限公司北京分公司定损中心进行理赔，骗取保险金人民币4万余元。
```
**Label:** 保险诈骗

### Example 3: 非法拘禁 (Illegal Detention)
```
经审理查明，2015年5月27日凌晨1许，被告人郑某某获悉与其有债务纠纷的被害人莫某乙在清远市××区太和镇××大道万州烤鱼石锅鱼大排档吃夜宵后，便伙同郑1某、郑2某等人驾驶一辆面包车去到上述大排档将莫某乙抓上车，带至浸潭镇大陂头村委会大围村郑2某家中看管。为防止莫某龙逃跑，郑某某又安排其他人员轮流在旁看管。期间，郑某某等人恐吓和殴打莫某乙，并多次催促莫某乙用电话联系家人筹钱还债。
```
**Label:** 非法拘禁

### Example 4: [持有、使用]假币 (Possession/Use of Counterfeit Currency)
```
经审理查明：2015年10月22日，被告人臧某某在盖州市鼓楼办事处平安刷车厂附近被公安机关抓获。当场在被告人臧某某身上搜出十万元假币，后又在其家中搜出二千一百元假币（面值均为百元，共计一千零二十一张）。经中国人民银行营口分行鉴定：送检的1021张百元人民币为机制伪造假币。
```
**Label:** [持有、使用]假币

### Example 5: 贪污 (Embezzlement)
```
阿2某人民检察院指控，2014年，阿2某xxx乡xxx村民委员会，向阿2某民族宗教事务局申请xxx村标准化边沟建设项目扶贫资金20万元。该项目于2014年10月30日竣工。2015年4月份，20万元项目资金到阿2某民族宗教事务局，由涂某负责管理。20万元扶贫资金转入涂某账户后，涂某实际结算工程款139256元，剩余60744元被涂某非法据为己有。
```
**Label:** 贪污

### Example 6: [走私、贩卖、运输、制造]毒品 (Drug Trafficking)
```
山东省胶州市人民检察院指控，2015年2月9日14时许，被告人张某在胶州市李哥庄镇中国农业银行门口将一克冰毒以人民币500元的价格贩卖给刘某。2014年7月份的一天，被告人张某在胶州市李哥庄镇石拉子村永乐超市门口将一克冰毒以人民币500元的价格贩卖给刘某。
```
**Label:** [走私、贩卖、运输、制造]毒品


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/data/public/task.md =====

# Chess Hard Task - LLM Evaluation Benchmark

## Task Overview

This task evaluates Large Language Models (LLMs) on 50 challenging chess problems. The questions require the model to analyze chess positions and provide strategic moves using Standard Algebraic Notation (SAN).

### Problem Types

1. **Best 3 Moves**: Given a chess position (FEN notation), find the 3 best next moves
2. **Knight Path**: Calculate minimum moves for a knight to visit all target squares on a 100x100 board

## Dataset Format

### Question Format (`chess_hard.json`)

The dataset contains 50 questions in the following format:

```json
[
  {
    "question_id": "best_3_moves_hard_1",
    "prompt": "You are given a chess position using this FEN: 8/8/4k2K/1pp5/3pP1P1/pP6/P1P5/8 b - - 0 38\nGive the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format. Return your answer in the format: solution = [move1, move2, move3]",
    "problem": {
      "template": "best_3_moves"
    }
  },
  {
    "question_id": "knight_path_hard_1",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares...\n\nReturn your answer in the format: solution = <integer>",
    "problem": {
      "template": "knight_path"
    }
  }
]
```

**Important Notes:**
- The dataset file (`chess_hard.json`) does **NOT** contain answers
- Questions use a specific response format that models must follow

### Expected Response Format

Models must respond in one of these formats:

**For best moves (list):**
```
solution = ["c4", "bxc4", "bxc4"]
```

**For knight path (integer):**
```
solution = 218
```

## Result Format for Evaluation

Your inference script must save results in a single `responses.json` file containing all results as an array.

### Responses File Format (`responses.json`)

```json
[
  {
    "question_id": "best_3_moves_hard_1",
    "prompt": "You are given a chess position using this FEN: 8/8/4k2K/1pp5/3pP1P1/pP6/P1P5/8 b - - 0 38\nGive the 3 best next moves...",
    "solution": ["c4", "bxc4", "Kd5"],
    "model_response": "Let me analyze this chess position... solution = [\"c4\", \"bxc4\", \"Kd5\"]",
    "success": true,
    "usage": {
      "prompt_tokens": 123,
      "completion_tokens": 45,
      "total_tokens": 168
    },
    "elapsed_seconds": 1.2,
    "timestamp": "2024-01-15 10:30:45"
  },
  {
    "question_id": "knight_path_hard_1",
    "prompt": "There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves...",
    "solution": 218,
    "model_response": "After calculating the optimal knight path... solution = 218",
    "success": true,
    "usage": {
      "prompt_tokens": 125,
      "completion_tokens": 48,
      "total_tokens": 173
    },
    "elapsed_seconds": 1.4,
    "timestamp": "2024-01-15 10:30:46"
  },
  {
    "question_id": "best_3_moves_hard_3",
    "prompt": "You are given a chess position...",
    "solution": null,
    "model_response": "Error occurred during processing",
    "success": false,
    "error": {
      "type": "APIError",
      "message": "Rate limit exceeded"
    },
    "elapsed_seconds": 0.5,
    "timestamp": "2024-01-15 10:30:47"
  }
]
```

### Required Fields for Each Response

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_id` | string | ✅ **Required** | Must match ID from dataset (e.g., "best_3_moves_hard_1") |
| `prompt` | string | ✅ **Required** | The original question/prompt from dataset |
| `solution` | array/number/null | ✅ **Required** | Extracted answer: array of strings for moves (e.g., `["c4", "bxc4"]`), number for knight path (e.g., `218`), or `null` if failed |
| `model_response` | string | ❌ Optional | Full text response from the model (for debugging) |
| `success` | boolean | ❌ Optional | Whether inference succeeded (default: true if solution is not null) |
| `usage` | object | ❌ Optional | Token usage stats: `{prompt_tokens, completion_tokens, total_tokens}` |
| `elapsed_seconds` | number | ❌ Optional | Time taken for inference |
| `timestamp` | string | ❌ Optional | When inference ran (ISO format or any readable format) |
| `error` | object | ❌ Optional | Error details if failed: `{type, message}` |
| `domain` | string | ❌ Optional | Task domain (e.g., "chess") |
| `difficulty` | string | ❌ Optional | Difficulty level (e.g., "hard") |

### Solution Field Format

The `solution` field must contain the extracted answer in the correct format:

**For best moves questions** (e.g., `best_3_moves_hard_*`):
- Type: `array` of strings
- Format: `["move1", "move2", "move3"]`
- Example: `["c4", "bxc4", "Kd5"]`

**For knight path questions** (e.g., `knight_path_hard_*`):
- Type: `number` (integer)
- Format: Single integer value
- Example: `218`

**For failed inference**:
- Type: `null`
- Use when: Model failed to respond or answer couldn't be extracted

### Directory Structure

Your working directory should look like this:

```
working_dir/
├── responses.json        # All results in a single file (array format)
└── summary.json          # Optional: aggregate stats
```


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/longcot-chess/reference/SAMPLE_TASK_DESCRIPTIONS.md =====

# Sample Task Descriptions

This document contains sample tasks from the longcot evaluation dataset.

---

## Sample Task 1: Chess Best Moves (Hard)

**Question ID:** best_3_moves_hard_1

**Description:**
You are given a chess position using this FEN: `8/8/4k2K/1pp5/3pP1P1/pP6/P1P5/8 b - - 0 38`

Give the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format.

**Return Format:**
```
solution = [move1, move2, move3]
```

**Problem Type:** best_3_moves

---

## Sample Task 2: Knight Path Optimization (Hard)

**Question ID:** knight_path_hard_1

**Description:**
There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format.

**Starting Position:** `(51, 43)`

**Target Squares:**
```
[(64, 27), (9, 77), (53, 72), (26, 16), (18, 97), (46, 3), (84, 17), (66, 45),
 (88, 76), (80, 74), (67, 32), (17, 40), (88, 9), (37, 18), (71, 89), (68, 89),
 (81, 82), (80, 17), (34, 76), (5, 18), (48, 23), (32, 17), (22, 85), (39, 98),
 (9, 9), (19, 93), (80, 9), (50, 92), (70, 38), (1, 74)]
```

**Return Format:**
```
solution = <integer>
```

**Problem Type:** knight_path

---

## Sample Task 3: Chess Best Moves with Complex Position

**Question ID:** best_3_moves_hard_8

**Description:**
You are given a chess position using this FEN: `k3r3/1bR1b1p1/1p2Qn1p/p2p1P2/1q1P1B2/5NP1/6KP/2R5 b - - 3 30`

Give the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format.

**Return Format:**
```
solution = [move1, move2, move3]
```

**Problem Type:** best_3_moves

---

## Sample Task 4: Knight Path with 30 Targets

**Question ID:** knight_path_hard_10

**Description:**
There is a chess board of size 100x100 and certain target squares. Calculate the minimum number of moves it takes for the knight at the given starting position to touch all the target squares. Both target squares and the starting position is given in a 0-indexed format.

**Starting Position:** `(55, 49)`

**Target Squares:**
```
[(34, 64), (49, 24), (68, 89), (47, 25), (29, 57), (48, 97), (48, 15), (47, 18),
 (2, 86), (59, 10), (32, 23), (8, 90), (28, 30), (73, 48), (28, 54), (34, 34),
 (35, 17), (29, 19), (91, 94), (96, 84), (79, 16), (80, 1), (32, 43), (70, 2),
 (99, 26), (55, 54), (24, 34), (11, 82), (58, 28), (35, 70)]
```

**Return Format:**
```
solution = <integer>
```

**Problem Type:** knight_path

---

## Sample Task 5: Chess Tactical Position

**Question ID:** best_3_moves_hard_9

**Description:**
You are given a chess position using this FEN: `r6N/pQpk2pp/3bp3/5b2/7q/1KN1p3/PP1P1PPP/R1B4R b - - 0 14`

Give the 3 best next moves in this position using the Standard Algebraic Notation (SAN) format.

**Return Format:**
```
solution = [move1, move2, move3]
```

**Problem Type:** best_3_moves

---

## Notes

- **Chess Best Moves Tasks:** These require analyzing a chess position given in FEN (Forsyth-Edwards Notation) format and determining the best 3 moves using Standard Algebraic Notation (SAN).

- **Knight Path Tasks:** These are optimization problems requiring calculation of the minimum number of moves for a knight to visit all target squares on a 100x100 chess board. This is a variation of the Traveling Salesman Problem with knight move constraints.

- All tasks are labeled as "hard" difficulty level.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/spaceship-titanic/data/public/task.md =====

# Overview

## Description
Welcome to the year 2912, where your data science skills are needed to solve a cosmic mystery. We've received a transmission from four lightyears away and things aren't looking good.

The *Spaceship Titanic* was an interstellar passenger liner launched a month ago. With almost 13,000 passengers on board, the vessel set out on its maiden voyage transporting emigrants from our solar system to three newly habitable exoplanets orbiting nearby stars.

While rounding Alpha Centauri en route to its first destination—the torrid 55 Cancri E—the unwary *Spaceship Titanic* collided with a spacetime anomaly hidden within a dust cloud. Sadly, it met a similar fate as its namesake from 1000 years before. Though the ship stayed intact, almost half of the passengers were transported to an alternate dimension!

![joel-filipe-QwoNAhbmLLo-unsplash.jpg](https://storage.googleapis.com/kaggle-media/competitions/Spaceship%20Titanic/joel-filipe-QwoNAhbmLLo-unsplash.jpg)

To help rescue crews and retrieve the lost passengers, you are challenged to predict which passengers were transported by the anomaly using records recovered from the spaceship’s damaged computer system.

Help save them and change history!

### Acknowledgments

Photos by [Joel Filipe](https://unsplash.com/@joelfilip?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText), [Richard Gatley](https://unsplash.com/@uncle_rickie?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) and [ActionVance](https://unsplash.com/@actionvance?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText) on Unsplash.

## Evaluation

### Metric

Submissions are evaluated based on their [classification accuracy](https://developers.google.com/machine-learning/crash-course/classification/accuracy), the percentage of predicted labels that are correct.

### Submission Format

The submission format for the competition is a csv file with the following format:

```
PassengerId,Transported
0013_01,False
0018_01,False
0019_01,False
0021_01,False
etc.
```

## Frequently Asked Questions

### What is a Getting Started competition?

Getting Started competitions were created by Kaggle data scientists for people who have little to no machine learning background. They are a great place to begin if you are new to data science or just finished a MOOC and want to get involved in Kaggle.

Getting Started competitions are a non-competitive way to get familiar with Kaggle’s platform, learn basic machine learning concepts, and start meeting people in the community. They have no cash prize and are on a rolling timeline.

### How do I create and manage a team?

When you accept the competition rules, a team will be created for you. You can invite others to your team, accept a merger with another team, and update basic information like team name by going to the [Team](https://www.kaggle.com/c/spaceship-titanic/team) page.

We've heard from many Kagglers that teaming up is the best way to learn new skills AND have fun. If you don't have a teammate already, consider asking if anyone wants to team up in the [discussion forum](https://www.kaggle.com/c/spaceship-titanic/discussion).

### What are Notebooks?

Kaggle Notebooks is a cloud computational environment that enables reproducible and collaborative analysis. Notebooks support scripts in Python and R, Jupyter Notebooks, and RMarkdown reports. You can visit the [Notebooks](https://www.kaggle.com/c/spaceship-titanic/notebooks) tab to view all of the publicly shared code for the Spaceship Titanic competition. For more on how to use Notebooks to learn data science, check out our [Courses](https://www.kaggle.com/learn/overview)!

### Why did my team disappear from the leaderboard?

To keep with the spirit of getting-started competitions, we have implemented a two month rolling window on submissions. Once a submission is more than two months old, it will be invalidated and no longer count towards the leaderboard.

If your team has no submissions in the previous two months, the team will also drop from the leaderboard. This will keep the leaderboard at a manageable size, freshen it up, and prevent newcomers from getting lost in a sea of abandoned scores.

*"I worked so hard to get that score! Give it back!"* Read more about our decision to implement a rolling leaderboard [here](https://www.kaggle.com/c/titanic/discussion/6240).

### How do I contact Support?

Kaggle does not have a dedicated support team so you’ll typically find that you receive a response more quickly by asking your question in the appropriate forum. (For this competition, you’ll want to use the [Spaceship Titanic discussion forum](https://www.kaggle.com/c/spaceship-titanic/discussion)).

Support is only able to help with issues that are being experienced by all participants. Before contacting support, please check the discussion forum for information on your problem. If you can’t find it, you can post your problem in the forum so a fellow participant or a Kaggle team member can provide help. The forums are full of useful information on the data, metric, and different approaches. We encourage you to use the forums often. If you share your knowledge, you'll find that others will share a lot in turn!

If your problem persists or it seems to be effective all participants then please [contact us](https://www.kaggle.com/contact).

# Dataset Description

In this competition your task is to predict whether a passenger was transported to an alternate dimension during the Spaceship Titanic's collision with the spacetime anomaly. To help you make these predictions, you're given a set of personal records recovered from the ship's damaged computer system.

## File and Data Field Descriptions

- **train.csv** - Personal records for about two-thirds (~8700) of the passengers, to be used as training data.
    - `PassengerId` - A unique Id for each passenger. Each Id takes the form `gggg_pp` where `gggg` indicates a group the passenger is travelling with and `pp` is their number within the group. People in a group are often family members, but not always.
    - `HomePlanet` - The planet the passenger departed from, typically their planet of permanent residence.
    - `CryoSleep` - Indicates whether the passenger elected to be put into suspended animation for the duration of the voyage. Passengers in cryosleep are confined to their cabins.
    - `Cabin` - The cabin number where the passenger is staying. Takes the form `deck/num/side`, where `side` can be either `P` for *Port* or `S` for *Starboard*.
    - `Destination` - The planet the passenger will be debarking to.
    - `Age` - The age of the passenger.
    - `VIP` - Whether the passenger has paid for special VIP service during the voyage.
    - `RoomService`, `FoodCourt`, `ShoppingMall`, `Spa`, `VRDeck` - Amount the passenger has billed at each of the *Spaceship Titanic*'s many luxury amenities.
    - `Name` - The first and last names of the passenger.
    - `Transported` - Whether the passenger was transported to another dimension. This is the target, the column you are trying to predict.
- **test.csv** - Personal records for the remaining one-third (~4300) of the passengers, to be used as test data. Your task is to predict the value of `Transported` for the passengers in this set.
- **sample_submission.csv** - A submission file in the correct format.
    - `PassengerId` - Id for each passenger in the test set.
    - `Transported` - The target. For each passenger, predict either `True` or `False`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/sia/tasks/spaceship-titanic/reference/SAMPLE_TASK_DESCRIPTIONS.md =====


## Task 1: OceanDepth 2050 — Global Sea Level Forecasting

# Overview

## Description
The year is 2050, and the effects of climate change have shifted from theoretical models to daily realities. The United Nations Global Climate Task Force (GCTF) has deployed a massive network of autonomous buoys, known as the "Sentinel Grid," across the world’s oceans. These buoys collect real-time data on water temperature, salinity, atmospheric pressure, and glacial melt rates.

To protect coastal cities and plan infrastructure for the next decade, we need precise predictions of sea-level fluctuations. While we have historical data dating back to the late 19th century, the non-linear acceleration of polar ice melt has made traditional linear models obsolete. Your challenge is to develop a regression model that can forecast mean sea-level rise for various coastal coordinates over the next 24 months.

Success in this task will allow governments to deploy flood defenses more effectively and save trillions of dollars in urban infrastructure.

## Evaluation

### Metric
Submissions are evaluated on the **Root Mean Squared Error (RMSE)** between the predicted sea-level change (in millimeters) and the actual observed change. 

### Submission Format
The submission should be a CSV file with the following format:
```
Station_Timestamp_Id,SeaLevelChange
NYC_2051_01,4.2
LON_2051_01,3.1
TOK_2051_01,5.8
etc.
```

# Dataset Description

You are provided with historical sensor data from 500 global stations.

## File and Data Field Descriptions

- **train.csv** - Monthly sensor readings from 2020 to 2049.
    - `Station_Id` - A unique identifier for the buoy station.
    - `Latitude / Longitude` - Geographic coordinates.
    - `Avg_Temp` - Average water temperature at 10m depth.
    - `Salinity` - Practical Salinity Units (PSU) measured at the surface.
    - `Ice_Melt_Index` - A composite score of nearby glacial runoff.
    - `Atmospheric_Pressure` - Mean sea-level pressure in hPa.
    - `SeaLevelRise` - The target variable (millimeter change from the 2020 baseline).
- **test.csv** - The same features for the years 2050–2051, excluding the target variable.
- **sample_submission.csv** - A submission file in the correct format.

-----

## Task 2: NeuroScan-X — Automated Brain Lesion Segmentation

# Overview

## Description
In the field of neurology, early detection of microscopic lesions is the key to halting degenerative diseases like Multiple Sclerosis. The "NeuroScan-X" initiative is a collaborative effort between leading research hospitals to standardize the analysis of high-resolution 3D MRI scans.

Manual segmentation of these lesions by radiologists is a time-consuming process and prone to inter-observer variability. We are challenging the community to build a computer vision model capable of performing automated image segmentation. You are provided with thousands of multi-modal MRI scans where expert neurologists have hand-labeled the "damaged" voxels. 

Your goal is to produce a model that generates a binary mask for each slice of an MRI, identifying the exact pixels where a lesion is present.

## Evaluation

### Metric
Submissions are evaluated based on the **Dice Coefficient**, which measures the overlap between the predicted segmentation mask and the ground truth.

### Submission Format
To reduce file size, submissions must use **Run-Length Encoding (RLE)** for the predicted masks. The CSV should contain:
```
ImageId,EncodedPixels
Scan001_Slice1,1 1 5 10
Scan001_Slice2,1 5 22 3
etc.
```

# Dataset Description

The dataset consists of NIfTI formatted 3D volumes, but for ease of use, they have been converted into 2D PNG slices.

## File and Data Field Descriptions

- **train_images/** - A folder of MRI slices (T1-weighted, T2-weighted, and FLAIR modalities).
- **train_masks/** - Binary PNG images where white pixels (255) represent a lesion and black (0) represents healthy tissue.
- **test_images/** - The slices for which you must predict the masks.
- **metadata.csv** - Supplemental data for each scan.
    - `Patient_ID` - Unique ID for the patient.
    - `Age` - Patient age at the time of scan.
    - `Manufacturer` - The brand of the MRI machine used (GE, Siemens, Philips).
    - `Field_Strength` - Magnetic field strength (1.5T or 3.0T).

-----

## Task 3: FinGuard — Fraudulent Transaction Network Analysis

# Overview

## Description
In the hyper-connected world of digital finance, money laundering has become a complex web of "smurfing" and "layering" across thousands of shell accounts. Traditional rule-based systems are failing to catch sophisticated syndicates that move small amounts of money through vast networks of seemingly unrelated individuals.

FinGuard is a large-scale graph dataset representing three months of transactions within a digital neo-bank. Your task is to perform **Node Classification**. Specifically, you must identify which "Accounts" (Nodes) are involved in a known money laundering ring. This is not just about the individual's behavior, but who they are connected to and how money flows through them.

Can you spot the "mules" and "architects" hidden in the noise of millions of legitimate transactions?

## Evaluation

### Metric
Submissions are evaluated using the **Area Under the Receiver Operating Characteristic Curve (ROC AUC)**. This ensures that models are penalized for false positives while maintaining a high catch rate for rare fraudulent nodes.

### Submission Format
```
AccountId,FraudProbability
ACC_0921,0.98
ACC_4412,0.02
ACC_8819,0.45
etc.
```

# Dataset Description

The data is provided as a set of CSVs representing a directed graph.

## File and Data Field Descriptions

- **nodes.csv** - Details of the accounts.
    - `AccountId` - Unique node ID.
    - `AccountType` - Individual, Business, or Non-Profit.
    - `CreationDate` - Date the account was opened.
    - `VerifiedStatus` - Level of identity verification (KYC level).
- **edges.csv** - The transactions between nodes.
    - `SourceId` - The account sending money.
    - `TargetId` - The account receiving money.
    - `Amount` - Value in USD.
    - `Timestamp` - Exact time of transaction.
    - `Type` - Wire, P2P, or Internal Transfer.
- **train_labels.csv** - The target labels for the training set (1 for Fraud, 0 for Legitimate).

-----

## Task 4: RetailMind — Customer Persona Clustering

# Overview

## Description
Global retailer "OmniMart" has a problem: they have too much data and not enough insight. Their marketing department is currently sending the same generic coupons to 50 million customers, resulting in a very low conversion rate. To solve this, they want to move toward "Hyper-Personalization."

This is an **Unsupervised Learning** task. You are provided with a year's worth of anonymized customer behavior data, including purchase history, app engagement, and demographic hints. Your goal is to identify distinct, stable clusters of customers (Personas). 

Unlike other competitions, there is no "Target" column. You must prove that your clusters are meaningful. The winning solution will be used to tailor the OmniMart shopping experience for millions of people.

## Evaluation

### Metric
Since this is unsupervised, submissions will be evaluated using a combination of the **Silhouette Score** (for cluster cohesion/separation) and a **Stability Index** (measuring how consistent the clusters remain when the data is sub-sampled). 

*Note: For the leaderboard, we provide a "Validation Set" where we have hidden the labels of 5 predefined shopping segments (e.g., "Budget Parents," "Tech Enthusiasts") to check for alignment with known business categories.*

### Submission Format
```
CustomerId,ClusterId
CUST_001,0
CUST_002,4
CUST_003,1
etc.
```

# Dataset Description

## File and Data Field Descriptions

- **customer_profiles.csv** - Static data.
    - `CustomerId` - Unique ID.
    - `Region` - Geographic territory.
    - `Signup_Method` - Social media, Email, or In-store.
- **transaction_summary.csv** - Aggregated behavior.
    - `Total_Spend` - Total USD spent in 12 months.
    - `Category_Preference` - The department they visit most (e.g., Electronics, Grocery).
    - `Return_Rate` - Percentage of items returned.
- **app_logs.json** - Semi-structured data.
    - Contains clickstream data (average time on app, number of searches, night vs. day usage).

-----

## Task 5: VoxCritique — Multi-Language Sentiment & Intent Generation



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/context.md =====

# Run Context: run_1

**Task**: /tasks/example
**Meta Model**: haiku
**Task Model**: claude-haiku-4-5-20251001
**Agent impl**: claude
**Started**: <TS>
**Max Generations**: 2

---

## Generation 1

**Status**: ✓ SUCCESS
**Timestamp**: <TS>
**Duration**: 1.5s

### Target Agent Changes
- Initial agent created by meta-agent
- File size: 21 bytes
- Lines of code: 1

### Execution Summary
- Execution status: ✓ SUCCESS
- Output format: Single

### Performance Metrics
- accuracy: 50.00
- correct: 99
- total: 198

---

## Generation 2

**Status**: ✓ SUCCESS
**Timestamp**: <TS>
**Duration**: 2.5s

### Target Agent Changes
- Modified by feedback agent
- File size: 69 bytes (+228.6%)
- Lines: 8 (+7 lines)
- Key changes from improvement.md:
  * Added structured error handling so the agent recovers from tool failures gracefully.
  * Switched to a retry loop with exponential backoff for transient API errors.
  * Improved logging to capture each tool call and its result for later analysis.

### Execution Summary
- Execution status: ✓ SUCCESS
- Output format: Single

### Performance Metrics
- accuracy: 75.00
- correct: 148
- total: 198

### Changes vs Previous Generation
- accuracy: +25.00
- correct: +49.00
- total: +0.00

---

## Summary Statistics

**Total Generations**: 2
**Successful Executions**: 2
**Best Performance**: Generation 2 (75.00% accuracy)

**Evolution**:
- 50.00% → 75.00% (+25.00%)

**Code Growth**:
- Initial: 1 lines (21 bytes)
- Final: 8 lines (69 bytes)
- Growth: 7 lines (+48 bytes)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/feedback_context_failure_single.txt =====

===== EXECUTION STATUS =====
FAILED: Target agent failed with exit code 1

**EVALUATION RESULTS**: No results.json found (evaluation may not have run or may have failed)


**Last 10 lines of output**:
```
boot
running
crash

```

Full logs available at: <GEN>/target_agent_stdout.log

STDERR:
Traceback: boom

===== EXECUTION SECTION =====

Here is the target agent execution trajectory:
```json
[
  {
    "role": "user",
    "content": "attempt"
  }
]
```

NOTE: If you see an "error" field in the above JSON, it means the execution log was malformed or missing. Focus on making the agent more robust.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/feedback_context_success_multi.txt =====

===== EXECUTION STATUS =====
SUCCESS: Target agent completed execution successfully.


**EVALUATION RESULTS**:
```json
{
  "accuracy": 0.8
}
```


**Last 10 lines of output**:
```
processing q0
processing q1
done

```

Full logs available at: <GEN>/target_agent_stdout.log

===== EXECUTION SECTION =====

**MULTI-TRAJECTORY EXECUTION**:

The agent executed 2 separate trajectories (e.g., different questions/samples).

**Summary**:
- Total trajectories: 2
- Successful: 2
- Failed: 0
- Execution folder: <GEN>/agent_execution

**Sample Trajectories** (first 3 shown, you can read others from the folder):

### Trajectory 0
```json
[
  {
    "role": "user",
    "content": "q0"
  }
]
```

### Trajectory 1
```json
[
  {
    "role": "user",
    "content": "q1"
  }
]
```


**To analyze all trajectories**:
- Read files from: <GEN>/agent_execution
- Files named: execution_q0.json, execution_q1.json, ..., execution_q1.json

**Analysis guidance**:
- Look for common failure patterns across trajectories
- Check if trajectories are properly isolated
- Ensure consistent behavior across all samples


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/feedback_context_success_single.txt =====

===== EXECUTION STATUS =====
SUCCESS: Target agent completed execution successfully.


**EVALUATION RESULTS**:
```json
{
  "accuracy": 0.9,
  "correct": 9,
  "total": 10
}
```


**Last 10 lines of output**:
```
line1
line2
line3

```

Full logs available at: <GEN>/target_agent_stdout.log

===== EXECUTION SECTION =====

Here is the target agent execution trajectory:
```json
[
  {
    "role": "user",
    "content": "solve it"
  }
]
```

NOTE: If you see an "error" field in the above JSON, it means the execution log was malformed or missing. Focus on making the agent more robust.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/feedback_prompt.txt =====

You are an expert AI Engineer analyzing agent scaffolds for iterative improvement.

**GENERATION CONTEXT**:
- Current generation: 2
- Previous generations: 1
- Evolution history: /RUN/run_1/context.md

**BEFORE ANALYZING - READ THE FULL HISTORY**:
1. Read /RUN/run_1/context.md to understand:
   - What improvements were tried in each previous generation
   - Performance trends across generations
   - What worked and what didn't work
2. Review previous improvement.md files from earlier generations if helpful
3. Don't repeat failed approaches from earlier generations
4. Build upon successful patterns that improved performance

---

**SAMPLE TASK DESCRIPTIONS**:
```
SAMPLE DESCRIPTIONS BODY
```

**CURRENT TARGET AGENT** (Generation 2):
```python
print('current target agent gen 2')
```

**TASK WORKED ON**:
```
# Example Task
Solve the example problem precisely.
```

**EXECUTION STATUS**:
```
SUCCESS: example status block
```

**EXECUTION LOGS**:
EXECUTION SECTION BODY

---

**YOUR TASK**:

You must create exactly TWO files in /RUN/run_1/gen_3/:
1. improvement.md - Analysis and improvement plan
2. target_agent.py - The improved agent implementation

Follow these steps:

**STEP 1: Analyze the execution**:
   - For multi-trajectory: Look for patterns across all trajectories
   - For single-trajectory: Analyze the full execution flow
   - Identify what worked well and what failed
   - Check for consistency and robustness

**STEP 2: Review evolution history**:
   - Read context.md to see the full evolution
   - Understand what was tried in previous generations
   - Build upon successful patterns
   - Avoid repeating failed approaches

**STEP 3: Write improvement.md**:
   - MUST save to: /RUN/run_1/gen_3/improvement.md
   - Document your analysis and planned improvements
   - Focus on structural improvements to the agent scaffold
   - Make the agent more robust and generalizable
   - Don't optimize for this specific task
   - Reference insights from previous generations if applicable

**STEP 4: Create improved target_agent.py**:
   - MUST save to: /RUN/run_1/gen_3/target_agent.py
   - Implement the improvements documented in improvement.md
   - Apply all the planned improvements from step 3
   - Do not create or modify any other files besides these two

**RULES**:
- Focus on agent structure, not task-specific optimizations
- Make the agent work well across diverse task types (see sample task descriptions)
- If execution failed, fix the root cause
- If multi-trajectory: ensure each trajectory is properly isolated and logged
- Consider error handling, logging mechanisms, and robustness
- Build upon successful patterns from previous generations (check context.md)
- If execution log shows errors or is incomplete, suggest improvements to ensure proper logging

NOTE: The agent execution log may be incomplete or contain errors if the target agent crashed. If you see an "error" field, focus on making the agent more robust to prevent such failures.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/meta_prompt.txt =====

You are a meta-agent. Your task is to create a target agent which can execute a task. Go ahead and create a target_agent.py for the target agent, which in turn can solve the given task.

Here is the FULL TASK SPECIFICATION that your target_agent.py will need to solve:
# Example Task
Solve the example problem precisely.

Here are a couple of sample task descriptions which the target agent has to solve:
SAMPLE DESCRIPTIONS BODY

Here is a sample target_agent.py showing the complete implementation pattern (READ THE ENTIRE FILE):
print('reference target agent')

Here is a sample agent execution trajectory:
{
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ]
}

CRITICAL RULES - FOLLOW EXACTLY:

1. The current working directory is /WORK/run_1/gen_1. Create the target_agent.py in the current working directory itself.

2. The target_agent.py MUST accept two command-line arguments:
   - --dataset_dir: Absolute path to the dataset directory (READ-ONLY, provided at runtime)
   - --working_dir: Absolute path to the working directory (READ-WRITE, provided at runtime)

3. CRITICAL: The target_agent.py must INCLUDE these paths in the prompt it sends to claude-haiku-4-5-20251001. claude-haiku-4-5-20251001 MUST be explicitly told:
   - Where the dataset directory is located (the exact path from --dataset_dir)
   - Where the working directory is located (the exact path from --working_dir)
   - That it can ONLY READ from the dataset directory
   - That it can READ from and WRITE to the working directory

   DO NOT let claude-haiku-4-5-20251001 search for data in random locations. The prompt must say: "The dataset is at: <actual_dataset_dir_path>"

4. The target agent can ONLY read from the dataset directory provided via --dataset_dir, and can ONLY write to the working directory specified by --working_dir. It must NOT access any other directories on the filesystem.

5. EXECUTION LOGGING - CRITICAL:

   The target_agent.py must log its execution trajectory properly. The format depends on the task type:

   **FOR TASKS WITH MULTIPLE INDEPENDENT SAMPLES** (e.g., GPQA with 198 questions, multiple test cases):
   - Create a folder: agent_execution/ in the working directory
   - Save each sample separately: execution_q0.json, execution_q1.json, execution_q2.json, etc.
   - Each file contains the complete trajectory for that ONE sample only
   - Files must be named sequentially: execution_q0.json, execution_q1.json, ...

   **FOR TASKS WITH SINGLE EXECUTION** (e.g., building one ML model, analyzing one dataset):
   - Save to a single file: agent_execution.json in the working directory
   - File contains the complete execution trajectory

   **HOW TO DETERMINE WHICH FORMAT**:
   - Read the task description carefully
   - If it mentions "independent items", "dataset with multiple records to process separately"
     → Use multi-trajectory (folder with multiple files)
   - If it's about "build a model", "analyze the dataset", "create one solution", "optimize one system"
     → Use single-trajectory (one JSON file)

   **FORMAT REQUIREMENTS** (both formats):
   - Use the same format as the sample agent execution trajectory provided above
   - Include all messages, tool calls, and their results
   - Ensure valid JSON (properly close all arrays/objects)
   - Make sure to properly close the JSON file(s) to avoid corruption

6. Do NOT attempt to write to or modify files inside the dataset directory. It is READ-ONLY.
7. The target_agent.py should use only the "claude-haiku-4-5-20251001" model when invoking the language model (do not use any other model).
8. DO NOT hardcode any specific dataset paths in the target_agent.py code. The paths will be provided at runtime via command-line arguments and MUST be passed to claude-haiku-4-5-20251001 in the prompt.

Example invocation (paths will vary at runtime):
    python target_agent.py --dataset_dir /path/to/dataset --working_dir /path/to/working


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/hexo-ai-sia/tests/golden/meta_prompt_openai.txt =====

=== TARGET MODEL CLIENT SETUP (OpenAI-compatible provider: Nebius Token Factory) ===

The target model "moonshotai/Kimi-K2.6" is served by an OpenAI-compatible API. The reference
target_agent.py shown below may use a different SDK (e.g. the Gemini SDK) — you MUST
refactor your target_agent.py to use the `openai` SDK configured for this provider
(do NOT use the anthropic or google SDK):

    import os
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.tokenfactory.us-central1.nebius.com/v1/",
        api_key=os.environ["NEBIUS_API_KEY"],
    )

Call client.chat.completions.create(model="moonshotai/Kimi-K2.6", ...) using OpenAI-style
messages (and OpenAI function calling / response_format where the reference uses
structured output). Do NOT compute a dollar cost: per-provider pricing is unknown, so
set any cost field to 0 (token counts from the API response are still fine to record).

You are a meta-agent. Your task is to create a target agent which can execute a task. Go ahead and create a target_agent.py for the target agent, which in turn can solve the given task.

Here is the FULL TASK SPECIFICATION that your target_agent.py will need to solve:
# Example Task
Solve the example problem precisely.

Here are a couple of sample task descriptions which the target agent has to solve:
SAMPLE DESCRIPTIONS BODY

Here is a sample target_agent.py showing the complete implementation pattern (READ THE ENTIRE FILE):
print('reference target agent')

Here is a sample agent execution trajectory:
{
  "messages": [
    {
      "role": "user",
      "content": "hi"
    }
  ]
}

CRITICAL RULES - FOLLOW EXACTLY:

1. The current working directory is /WORK/run_1/gen_1. Create the target_agent.py in the current working directory itself.

2. The target_agent.py MUST accept two command-line arguments:
   - --dataset_dir: Absolute path to the dataset directory (READ-ONLY, provided at runtime)
   - --working_dir: Absolute path to the working directory (READ-WRITE, provided at runtime)

3. CRITICAL: The target_agent.py must INCLUDE these paths in the prompt it sends to moonshotai/Kimi-K2.6. moonshotai/Kimi-K2.6 MUST be explicitly told:
   - Where the dataset directory is located (the exact path from --dataset_dir)
   - Where the working directory is located (the exact path from --working_dir)
   - That it can ONLY READ from the dataset directory
   - That it can READ from and WRITE to the working directory

   DO NOT let moonshotai/Kimi-K2.6 search for data in random locations. The prompt must say: "The dataset is at: <actual_dataset_dir_path>"

4. The target agent can ONLY read from the dataset directory provided via --dataset_dir, and can ONLY write to the working directory specified by --working_dir. It must NOT access any other directories on the filesystem.

5. EXECUTION LOGGING - CRITICAL:

   The target_agent.py must log its execution trajectory properly. The format depends on the task type:

   **FOR TASKS WITH MULTIPLE INDEPENDENT SAMPLES** (e.g., GPQA with 198 questions, multiple test cases):
   - Create a folder: agent_execution/ in the working directory
   - Save each sample separately: execution_q0.json, execution_q1.json, execution_q2.json, etc.
   - Each file contains the complete trajectory for that ONE sample only
   - Files must be named sequentially: execution_q0.json, execution_q1.json, ...

   **FOR TASKS WITH SINGLE EXECUTION** (e.g., building one ML model, analyzing one dataset):
   - Save to a single file: agent_execution.json in the working directory
   - File contains the complete execution trajectory

   **HOW TO DETERMINE WHICH FORMAT**:
   - Read the task description carefully
   - If it mentions "independent items", "dataset with multiple records to process separately"
     → Use multi-trajectory (folder with multiple files)
   - If it's about "build a model", "analyze the dataset", "create one solution", "optimize one system"
     → Use single-trajectory (one JSON file)

   **FORMAT REQUIREMENTS** (both formats):
   - Use the same format as the sample agent execution trajectory provided above
   - Include all messages, tool calls, and their results
   - Ensure valid JSON (properly close all arrays/objects)
   - Make sure to properly close the JSON file(s) to avoid corruption

6. Do NOT attempt to write to or modify files inside the dataset directory. It is READ-ONLY.
7. The target_agent.py should use only the "moonshotai/Kimi-K2.6" model when invoking the language model (do not use any other model).
8. DO NOT hardcode any specific dataset paths in the target_agent.py code. The paths will be provided at runtime via command-line arguments and MUST be passed to moonshotai/Kimi-K2.6 in the prompt.

Example invocation (paths will vary at runtime):
    python target_agent.py --dataset_dir /path/to/dataset --working_dir /path/to/working
