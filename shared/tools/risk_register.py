"""Risk register generator — returns structured risks based on project context."""
from __future__ import annotations

from langchain_core.tools import tool
from shared.guidelines import failure_threshold_pct

# Risk catalogue: (name, base_likelihood, base_impact, mitigation_template)
_COMMON_RISKS = [
    (
        "Market Demand Shortfall",
        "Medium",
        "High",
        "Conduct quarterly demand reviews; trigger contingency plan if revenue falls below {threshold}% of forecast.",
    ),
    (
        "CAPEX Cost Overrun",
        "Medium",
        "High",
        "Maintain a 10–15% contingency reserve; use fixed-price contracts where possible.",
    ),
    (
        "Project Schedule Delay",
        "Medium",
        "Medium",
        "Apply critical-path monitoring; identify and protect schedule float on key milestones.",
    ),
    (
        "Regulatory / Compliance Change",
        "Low",
        "High",
        "Engage regulatory counsel early; monitor government consultations quarterly.",
    ),
    (
        "Key Personnel Dependency",
        "Low",
        "Medium",
        "Cross-train at least two team members for each critical role; document key processes.",
    ),
]

_CAPEX_EXTRA = [
    (
        "Technology Obsolescence",
        "Low",
        "Medium",
        "Prefer modular, upgradeable technology; include refresh cycle in CAPEX plan.",
    ),
    (
        "Vendor / Supplier Concentration",
        "Medium",
        "Medium",
        "Dual-source critical components; negotiate SLAs with penalty clauses.",
    ),
]

_INVESTMENT_EXTRA = [
    (
        "Market Volatility / Valuation Risk",
        "High",
        "High",
        "Use portfolio diversification; set hard stop-loss triggers at 20% drawdown.",
    ),
    (
        "Liquidity Risk",
        "Medium",
        "High",
        "Maintain ≥ 6-month operating cash reserve; avoid illiquid position concentration.",
    ),
]

_COST_SAVING_EXTRA = [
    (
        "Change Management / Staff Resistance",
        "High",
        "Medium",
        "Implement structured change programme; communicate benefits early and often.",
    ),
    (
        "Process Dependency on Legacy Systems",
        "Medium",
        "Medium",
        "Map all system integrations before cutover; maintain parallel-run period.",
    ),
]

_EXTRA_BY_TYPE: dict[str, list] = {
    "CAPEX": _CAPEX_EXTRA,
    "Investment": _INVESTMENT_EXTRA,
    "CostSaving": _COST_SAVING_EXTRA,
}


@tool
def risk_register(
    project_type: str,
    capex_hkd_millions: float,
    description: str = "",
) -> list[dict]:
    """Generate a structured risk register for a business case.

    Args:
        project_type: One of 'CAPEX', 'Investment', 'CostSaving'.
        capex_hkd_millions: Capital expenditure (HKD millions) — used to set failure threshold.
        description: Optional project description for context (not parsed, reserved for future).

    Returns list of risk dicts with keys: name, likelihood, impact, mitigation.
    """
    threshold_pct = int(failure_threshold_pct(capex_hkd_millions) * 100)
    extra = _EXTRA_BY_TYPE.get(project_type, _CAPEX_EXTRA)

    risks = []
    for name, likelihood, impact, mitigation_tpl in _COMMON_RISKS + extra:
        risks.append(
            {
                "name": name,
                "likelihood": likelihood,
                "impact": impact,
                "mitigation": mitigation_tpl.format(threshold=threshold_pct),
            }
        )

    return risks
