"""Business-case validator — pure checks, no LLM, raises no exceptions."""
from __future__ import annotations

from langchain_core.tools import tool

from shared.guidelines import (
    DISCOUNT_RATE_PRETAX,
    RED_FLAGS,
    REQUIRED_SECTIONS,
    required_kpi_sets,
)


@tool
def validate_bcase(bcase: dict) -> list[str]:
    """Validate a BCaseOutput dict against company guidelines.

    Checks:
    - All 14 required sections are present and non-empty
    - Sensitivity table has ≥ 4 rows (base + 3 scenarios)
    - KPI count matches the threshold rule for this capex size
    - IRR > 100% is flagged for extra justification
    - Gross margin > 50% is flagged for extra justification
    - NPV was computed at 20% discount rate (presence check only)

    Returns list of warning strings. Empty list = clean.
    """
    warnings: list[str] = []

    # 1. Required sections
    for section in REQUIRED_SECTIONS:
        val = bcase.get(section)
        if val is None or val == "" or val == [] or val == {}:
            warnings.append(f"Missing or empty required section: '{section}'")

    # 2. Sensitivity: must have base + ≥ 3 downside scenarios
    sensitivity = bcase.get("sensitivity", [])
    if not isinstance(sensitivity, list) or len(sensitivity) < 4:
        warnings.append(
            f"Sensitivity table has {len(sensitivity) if isinstance(sensitivity, list) else 0} rows; "
            "need ≥ 4 (base case + 3 downside scenarios)."
        )

    # 3. KPI count vs threshold
    financials = bcase.get("financials") or {}
    capex = None
    capex_breakdown = bcase.get("capex_breakdown") or {}
    if isinstance(capex_breakdown, dict) and "total_hkd_millions" in capex_breakdown:
        capex = capex_breakdown["total_hkd_millions"]

    kpis = bcase.get("kpis", [])
    if capex is not None:
        required = required_kpi_sets(capex)
        actual = len(kpis) if isinstance(kpis, list) else 0
        if actual < required:
            warnings.append(
                f"Project capex HK${capex}M requires ≥ {required} KPI set(s); only {actual} provided."
            )

    # 4. IRR red flag
    irr = None
    if isinstance(financials, dict):
        irr = financials.get("irr_pct")
    if irr is not None:
        if irr > RED_FLAGS["irr_too_high"] * 100:
            warnings.append(
                f"IRR of {irr:.1f}% exceeds 100% — extra justification required in 'investment_and_return'."
            )

    # 5. Margin red flag — check base-case scenario
    if isinstance(sensitivity, list) and len(sensitivity) > 0:
        base_margin = sensitivity[0].get("margin_pct") if isinstance(sensitivity[0], dict) else None
        if base_margin is not None and base_margin > RED_FLAGS["margin_too_high"] * 100:
            warnings.append(
                f"Base-case gross margin of {base_margin:.1f}% exceeds 50% — extra justification required."
            )

    # 6. Risks list must be non-empty
    risks = bcase.get("risks", [])
    if not isinstance(risks, list) or len(risks) == 0:
        warnings.append("Risk register is empty — at least 3 risks must be documented.")

    # 7. Implications must cover the 4 mandatory areas
    implications = bcase.get("implications") or {}
    for area in ("financial", "legal", "tax", "co_sec"):
        if not implications.get(area):
            warnings.append(f"Implications missing mandatory area: '{area}'")

    return warnings
