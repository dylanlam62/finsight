"""HITL tool — pauses the LangGraph graph and surfaces a question to the user.

In the web-form UX the SSE stream will emit an event of type
'on_tool_start' with tool_name='ask_human'; the frontend detects this,
shows an input form, and resumes the graph via POST /api/runs/{id}/resume
with {"answer": "..."} which calls graph.invoke(Command(resume=answer)).
"""
from __future__ import annotations

from langchain_core.tools import tool
from langgraph.types import interrupt


@tool
def ask_human(question: str, options: list[str] | None = None) -> str:
    """Pause execution and ask the human user a clarifying question.

    Use this whenever:
    - Critical inputs are missing or ambiguous (e.g. no revenue data)
    - Assumptions contradict each other
    - A red flag needs human sign-off before proceeding

    Args:
        question: The question to surface to the user (be specific and concise).
        options:  Optional list of suggested answers shown as buttons, e.g.
                  ["Less than HK$5M", "HK$5–10M", "More than HK$10M"].
                  The user may still type a free-form answer instead.

    Returns the user's answer as a string (provided when the graph is resumed).
    """
    payload: dict = {"question": question, "tool": "ask_human"}
    if options:
        payload["options"] = options
    return interrupt(payload)
