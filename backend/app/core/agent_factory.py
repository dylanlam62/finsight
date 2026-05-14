"""Translates a DeepAgent DB row into a live create_deep_agent() compiled graph."""

from __future__ import annotations

import os

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from app.core.tool_registry import build_extra_tools, get_excluded_builtin_names
from app.models.agent import DeepAgent

# One MemorySaver per agent — persists interrupt state across runs on the same thread.
_checkpointers: dict[str, object] = {}


def _resolve_model(model_str: str, temperature: float) -> BaseChatModel:
    """Return an initialised chat model.

    When OPENAI_BASE_URL is set we always use ChatOpenAI pointed at the custom
    endpoint, ignoring the 'provider:' prefix in model_str (Poe, Azure, Ollama,
    etc. are all OpenAI-compatible). Without a base URL we fall back to
    init_chat_model which honours the 'provider:model' format.
    """
    from app.config import settings as app_settings

    # Strip provider prefix — custom endpoints don't need it
    if ":" in model_str:
        _, model_name = model_str.split(":", 1)
    else:
        model_name = model_str

    if app_settings.openai_base_url:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=app_settings.openai_api_key or os.environ.get("OPENAI_API_KEY", ""),
            openai_api_base=app_settings.openai_base_url,
        )

    # Standard path — use init_chat_model with provider prefix
    from langchain.chat_models import init_chat_model
    full = model_str if ":" in model_str else f"openai:{model_str}"
    provider, name = full.split(":", 1)
    return init_chat_model(name, model_provider=provider, temperature=temperature)


def _default_model_str() -> str:
    """Return the configured default model string for this deployment."""
    from app.config import settings as app_settings
    return app_settings.deepagent_model or "gpt-4o"


def build_agent(agent: DeepAgent) -> CompiledStateGraph:
    """Build and compile a deep agent from its DB configuration."""
    from deepagents import SubAgent, create_deep_agent

    from app.config import settings as app_settings

    # Push env vars so deepagents internals can find them
    if app_settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", app_settings.openai_api_key)
    if app_settings.openai_base_url:
        os.environ.setdefault("OPENAI_BASE_URL", app_settings.openai_base_url)

    model_str = agent.model or _default_model_str()
    model = _resolve_model(model_str, agent.temperature or 0.0)

    # Sub-agents — each gets its own tool list from sub_agent_tools rows
    subagents: list[SubAgent] = []
    for sa in agent.subagents:
        spec: SubAgent = {
            "name": sa.name,
            "description": sa.description,
            "system_prompt": sa.system_prompt,
        }
        if sa.model:
            spec["model"] = sa.model
        sa_tools = build_extra_tools(sa.tools)
        if sa_tools:
            spec["tools"] = sa_tools
        subagents.append(spec)

    # Supervisor-level extra tools (e.g. ask_human selected for the top-level agent)
    extra_tools = build_extra_tools(agent.tools)

    if agent.id not in _checkpointers:
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointers[agent.id] = MemorySaver()

    compiled = create_deep_agent(
        model=model,
        tools=extra_tools or None,
        system_prompt=agent.system_prompt or None,
        subagents=subagents or None,
        checkpointer=_checkpointers[agent.id],
    )

    return compiled
