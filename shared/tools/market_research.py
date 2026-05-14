"""Market research via ScraperAPI Google Search — no LLM inside."""
from __future__ import annotations

import os

import httpx
from langchain_core.tools import tool

from shared.guidelines import SCRAPER_API_BASE

_TIMEOUT = 30


def _scraper_key() -> str:
    key = os.environ.get("SCRAPER_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "SCRAPER_API_KEY environment variable is not set. "
            "Add it to backend/.env before running market research."
        )
    return key


def _format_results(data: dict, query: str) -> str:
    """Convert ScraperAPI JSON response to a compact markdown string."""
    lines = [f"## Market Research: {query}\n"]

    # Organic results
    organic = data.get("organic_results", [])
    if organic:
        lines.append("### Top Search Results\n")
        for i, r in enumerate(organic[:5], 1):
            title = r.get("title", "")
            link = r.get("link", "")
            snippet = r.get("snippet", "")
            lines.append(f"{i}. **{title}**")
            if snippet:
                lines.append(f"   {snippet}")
            if link:
                lines.append(f"   Source: {link}")
            lines.append("")

    # Knowledge graph / answer box
    answer = data.get("answer_box") or data.get("knowledge_graph")
    if answer and isinstance(answer, dict):
        lines.append("### Featured Answer\n")
        for k, v in answer.items():
            if isinstance(v, str) and v:
                lines.append(f"- **{k}**: {v}")
        lines.append("")

    # Related searches for follow-up
    related = data.get("related_searches", [])
    if related:
        terms = [r.get("query", "") for r in related[:5] if r.get("query")]
        if terms:
            lines.append(f"### Related topics: {', '.join(terms)}\n")

    if len(lines) == 1:
        lines.append("No results found.")

    return "\n".join(lines)


@tool
def market_research(query: str) -> str:
    """Search Google (via ScraperAPI) and return structured market intelligence.

    Args:
        query: Natural-language search query, e.g. 'Hong Kong logistics market size 2024'.

    Returns formatted markdown string with top results, answer box, and related topics.
    Raises EnvironmentError if SCRAPER_API_KEY is not set.
    """
    params = {"api_key": _scraper_key(), "query": query}
    response = httpx.get(SCRAPER_API_BASE, params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    return _format_results(data, query)
