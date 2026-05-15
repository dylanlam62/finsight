"""HITL tool — pauses the LangGraph graph and surfaces a question to the user.

In the web-form UX the SSE stream will emit an event of type
'on_tool_start' with tool_name='ask_human'; the frontend detects this,
shows an input form, and resumes the graph via POST /api/runs/{id}/resume
with {"answer": "..."} which calls graph.invoke(Command(resume=answer)).
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt

@tool
def ask_human(question: str, options: list[str] | None = None, multi_fields: list[dict[str, Any]] | None = None) -> str:
    """Pause execution and ask the human user a clarifying question or multiple fields.

    Use this whenever:
    - Critical inputs are missing or ambiguous (e.g. no revenue data)
    - Assumptions contradict each other
    - A red flag needs human sign-off before proceeding

    Args:
        question: The main question to surface to the user.
        options:  Optional list of suggested answers for a single question.
        multi_fields: Optional list of specific fields you need from the user. Use this when asking for multiple distinct pieces of information at once.
                      Each dict should have: 
                      - "id": string identifier for the field (e.g., "project_name")
                      - "label": string label for the field
                      - "options": optional list of suggested answers for this specific field

    Returns the user's answer as a string (provided when the graph is resumed).
    """
    payload: dict = {"question": question, "tool": "ask_human"}
    if options:
        payload["options"] = options
    if multi_fields:
        payload["multi_fields"] = multi_fields
    return interrupt(payload)
