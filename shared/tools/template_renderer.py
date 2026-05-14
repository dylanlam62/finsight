"""Render a named business-case section to formatted markdown."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Section templates
# ---------------------------------------------------------------------------

def _executive_summary(c: dict) -> str:
    return (
        f"## Executive Summary\n\n"
        f"{c.get('summary', '[Summary not provided]')}\n\n"
        f"**Recommendation:** {c.get('recommendation', 'Pending')}\n"
    )


def _market_overview(c: dict) -> str:
    size = c.get("market_size", "N/A")
    growth = c.get("market_growth_pct", "N/A")
    competitors = c.get("key_competitors", [])
    comp_str = "\n".join(f"- {k}" for k in competitors) if competitors else "- Not specified"
    return (
        f"## Market Overview\n\n"
        f"**Market Size:** {size}\n"
        f"**Growth Rate:** {growth}%\n\n"
        f"### Key Competitors\n{comp_str}\n\n"
        f"{c.get('market_context', '')}\n"
    )


def _value_proposition(c: dict) -> str:
    return (
        f"## Value Proposition\n\n"
        f"{c.get('statement', '[Value proposition not provided]')}\n\n"
        f"**Differentiators:**\n"
        + "\n".join(f"- {d}" for d in c.get("differentiators", []))
    )


def _project_description(c: dict) -> str:
    return (
        f"## Project Description\n\n"
        f"{c.get('description', '[Description not provided]')}\n\n"
        f"**Scope:** {c.get('scope', 'N/A')}\n"
        f"**Timeline:** {c.get('timeline', 'N/A')}\n"
        f"**Key Milestones:**\n"
        + "\n".join(f"- {m}" for m in c.get("milestones", []))
    )


def _investment_and_return(c: dict) -> str:
    irr = c.get("irr_pct", "N/A")
    npv = c.get("npv_hkd_millions", "N/A")
    payback = c.get("payback_years", "N/A")
    capex = c.get("capex_hkd_millions", "N/A")
    return (
        f"## Investment & Return\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Total CAPEX | HK${capex}M |\n"
        f"| IRR (Pre-tax) | {irr}% |\n"
        f"| NPV @ 20% | HK${npv}M |\n"
        f"| Payback Period | {payback} years |\n\n"
        f"{c.get('narrative', '')}\n"
    )


def _financials(c: dict) -> str:
    cashflows = c.get("cashflow_by_year", [])
    rows = "\n".join(
        f"| Year {i + 1} | HK${cf:.2f}M |" for i, cf in enumerate(cashflows)
    )
    return (
        f"## Financial Summary\n\n"
        f"| Year | Net Cashflow |\n"
        f"|------|-------------|\n"
        f"{rows}\n\n"
        f"**Discount Rate:** 20% (pre-tax, per company guidelines)\n"
    )


def _sensitivity(c: dict) -> str:
    scenarios = c.get("scenarios", [])
    if not scenarios:
        return "## Sensitivity Analysis\n\nNo scenarios provided.\n"
    header = "| Scenario | CAPEX (HK$M) | IRR (%) | NPV (HK$M) | Margin (%) | Payback (yrs) |"
    sep = "|----------|-------------|---------|-----------|-----------|-------------|"
    rows = []
    for s in scenarios:
        rows.append(
            f"| {s.get('name', '')} | {s.get('capex', '')} | "
            f"{s.get('irr', '')} | {s.get('npv', '')} | "
            f"{s.get('margin_pct', '')} | {s.get('payback', '')} |"
        )
    return f"## Sensitivity Analysis\n\n{header}\n{sep}\n" + "\n".join(rows) + "\n"


def _kpis(c: dict) -> str:
    kpi_list = c.get("kpis", [])
    if not kpi_list:
        return "## Key Performance Indicators\n\nNo KPIs defined.\n"
    sections = ["## Key Performance Indicators\n"]
    for kpi in kpi_list:
        name = kpi.get("name", "KPI")
        unit = kpi.get("unit", "")
        targets = kpi.get("quarterly_targets", [])
        q_str = " | ".join(str(t) for t in targets)
        sections.append(f"**{name}** ({unit})\n\n| Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 |")
        sections.append("|----|----|----|----|----|----|----|----|")
        sections.append(f"| {q_str} |\n")
    return "\n".join(sections)


def _capex_breakdown(c: dict) -> str:
    items = {k: v for k, v in c.items() if k != "total_hkd_millions"}
    total = c.get("total_hkd_millions", sum(items.values()) if items else 0)
    rows = "\n".join(f"| {k} | HK${v:.2f}M |" for k, v in items.items())
    return (
        f"## CAPEX Breakdown\n\n"
        f"| Item | Amount |\n"
        f"|------|--------|\n"
        f"{rows}\n"
        f"| **Total** | **HK${total:.2f}M** |\n"
    )


def _risks(c: dict) -> str:
    risk_list = c.get("risks", [])
    if not risk_list:
        return "## Risk Register\n\nNo risks documented.\n"
    header = "| # | Risk | Likelihood | Impact | Mitigation |"
    sep = "|---|------|-----------|--------|-----------|"
    rows = [
        f"| {i+1} | {r.get('name','')} | {r.get('likelihood','')} | "
        f"{r.get('impact','')} | {r.get('mitigation','')} |"
        for i, r in enumerate(risk_list)
    ]
    return f"## Risk Register\n\n{header}\n{sep}\n" + "\n".join(rows) + "\n"


def _implications(c: dict) -> str:
    parts = ["## Implications\n"]
    for area in ("financial", "legal", "tax", "co_sec"):
        label = area.replace("_", " ").title()
        parts.append(f"### {label}\n{c.get(area, 'Not assessed.')}\n")
    return "\n".join(parts)


def _key_success_factors(c: dict) -> str:
    factors = c.get("factors", [])
    items = "\n".join(f"- {f}" for f in factors)
    return f"## Key Success Factors\n\n{items}\n"


def _recommendations(c: dict) -> str:
    return f"## Recommendations\n\n{c.get('text', '[Recommendations not provided]')}\n"


def _appendices(c: dict) -> str:
    items = c.get("items", [])
    if not items:
        return "## Appendices\n\nNone.\n"
    return "## Appendices\n\n" + "\n".join(f"- {a}" for a in items) + "\n"


_RENDERERS = {
    "executive_summary": _executive_summary,
    "market_overview": _market_overview,
    "value_proposition": _value_proposition,
    "project_description": _project_description,
    "investment_and_return": _investment_and_return,
    "financials": _financials,
    "sensitivity": _sensitivity,
    "kpis": _kpis,
    "capex_breakdown": _capex_breakdown,
    "risks": _risks,
    "implications": _implications,
    "key_success_factors": _key_success_factors,
    "recommendations": _recommendations,
    "appendices": _appendices,
}


@tool
def template_renderer(section_name: str, content: dict) -> str:
    """Render a named business-case section to formatted markdown.

    Args:
        section_name: One of the 14 standard BC section names
                      (e.g. 'executive_summary', 'sensitivity', 'kpis').
        content: Dict of values to populate the section template.

    Returns formatted markdown string ready to include in the final document.
    """
    renderer = _RENDERERS.get(section_name)
    if renderer is None:
        available = ", ".join(_RENDERERS.keys())
        return (
            f"[template_renderer] Unknown section '{section_name}'. "
            f"Available: {available}"
        )
    return renderer(content)
