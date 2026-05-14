"""Maps tool names stored in the DB to actual LangChain tool objects.

Two categories of tools:

1. BCASE_TOOL_NAMES — business-case Python tools from shared/tools/.
   Stored as tool_type='builtin' in the DB; passed as extra_tools when selected.

2. Custom HTTP tools — user-defined tools stored with config in the DB.
   Resolved at runtime and passed as extra_tools.

Note: DEEPAGENTS_BUILTIN_NAMES (write_todos, ls, etc.) are always included by
deepagents automatically — they do not need to be resolved here.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import BaseTool, tool

logger = logging.getLogger(__name__)

# Tools provided by the deepagents library itself — excluded_tools controls these.
DEEPAGENTS_BUILTIN_NAMES: set[str] = {
    "write_todos",
    "ls",
    "read_file",
    "write_file",
    "edit_file",
    "glob",
    "grep",
    "execute",
    "task",
}

# Business-case Python tools — passed as extra_tools when selected.
BCASE_TOOL_NAMES: set[str] = {
    "financial_calculator",
    "sensitivity_analyzer",
    "kpi_generator",
    "validate_bcase",
    "market_research",
    "document_parser",
    "template_renderer",
    "risk_register",
    "ask_human",
}

# Combined set — every name that is stored as tool_type='builtin' in the DB.
BUILTIN_TOOL_NAMES: set[str] = DEEPAGENTS_BUILTIN_NAMES | BCASE_TOOL_NAMES


def _resolve_bcase_tool(name: str) -> BaseTool | None:
    """Import and return a BCase tool function by name."""
    try:
        from shared.tools.financial import financial_calculator
        from shared.tools.sensitivity import sensitivity_analyzer
        from shared.tools.kpi import kpi_generator
        from shared.tools.validator import validate_bcase
        from shared.tools.market_research import market_research
        from shared.tools.document_parser import document_parser
        from shared.tools.template_renderer import template_renderer
        from shared.tools.risk_register import risk_register
        from shared.tools.human import ask_human

        _mapping: dict[str, BaseTool] = {
            "financial_calculator": financial_calculator,
            "sensitivity_analyzer": sensitivity_analyzer,
            "kpi_generator": kpi_generator,
            "validate_bcase": validate_bcase,
            "market_research": market_research,
            "document_parser": document_parser,
            "template_renderer": template_renderer,
            "risk_register": risk_register,
            "ask_human": ask_human,
        }
        return _mapping.get(name)
    except ImportError as exc:
        logger.warning("Could not import bcase tool '%s': %s", name, exc)
        return None


def resolve_custom_tool(name: str, config: dict[str, Any] | None) -> BaseTool | None:
    """Build a LangChain tool from a custom tool config stored in the DB.

    Supported config shapes:
    - {"type": "http", "url": "https://...", "method": "POST"} — HTTP endpoint tool
    """
    if not config:
        return None

    tool_type = config.get("type")

    if tool_type == "http":
        import httpx

        url: str = config["url"]
        method: str = config.get("method", "POST").upper()
        headers: dict = config.get("headers", {})

        @tool(name)
        def http_tool(input: str) -> str:  # type: ignore[return-value]
            """Call a remote HTTP endpoint."""
            if method == "GET":
                resp = httpx.get(url, params={"input": input}, headers=headers, timeout=30)
            else:
                resp = httpx.post(url, json={"input": input}, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text

        return http_tool  # type: ignore[return-value]

    return None


def build_extra_tools(tool_rows: list) -> list[BaseTool]:
    """Return instantiated LangChain tools for selected tool rows.

    - builtin rows in BCASE_TOOL_NAMES → resolved from shared/tools/
    - custom rows with config → resolved as HTTP tools
    deepagents built-ins are NOT included here; they are controlled via
    excluded_tools in get_excluded_builtin_names().
    """
    result: list[BaseTool] = []
    for row in tool_rows:
        if row.tool_type == "builtin" and row.name in BCASE_TOOL_NAMES:
            t = _resolve_bcase_tool(row.name)
            if t:
                result.append(t)
        elif row.tool_type == "custom":
            t = resolve_custom_tool(row.name, row.config)
            if t:
                result.append(t)
    return result


def get_excluded_builtin_names(selected_tool_rows: list) -> list[str]:
    """Return deepagents built-in names the agent has NOT selected, to be excluded.

    BCase tools are intentionally excluded from this list — they are passed as
    extra_tools, not controlled via the excluded_tools mechanism.
    """
    selected_names = {
        r.name for r in selected_tool_rows
        if r.tool_type == "builtin" and r.name in DEEPAGENTS_BUILTIN_NAMES
    }
    return [name for name in DEEPAGENTS_BUILTIN_NAMES if name not in selected_names]
