"""KPI generator — returns the correct number of KPI sets per threshold rules."""
from __future__ import annotations

import math
from typing import Optional

from langchain_core.tools import tool

from shared.guidelines import required_kpi_sets


# ---------------------------------------------------------------------------
# KPI templates per project type
# ---------------------------------------------------------------------------

def _capex_kpis(revenue_year1: float, revenue_final: float, n_quarters: int = 8) -> list[dict]:
    """Standard KPI set for CAPEX projects."""
    rev_growth = (revenue_final / revenue_year1) ** (1 / (n_quarters / 4)) - 1 if revenue_year1 > 0 else 0.05
    return [
        {
            "name": "Cumulative Revenue (HKD M)",
            "unit": "HKD M",
            "quarterly_targets": [
                round(revenue_year1 * (1 + rev_growth) ** (q / 4), 3)
                for q in range(n_quarters)
            ],
        },
        {
            "name": "Gross Margin (%)",
            "unit": "%",
            "quarterly_targets": [
                round(30 + q * 1.5, 1) for q in range(n_quarters)
            ],
        },
        {
            "name": "Customer Acquisition Count",
            "unit": "customers",
            "quarterly_targets": [
                int(50 * (1.15 ** q)) for q in range(n_quarters)
            ],
        },
    ]


def _investment_kpis(revenue_year1: float, revenue_final: float, n_quarters: int = 8) -> list[dict]:
    """Standard KPI set for Investment projects."""
    rev_growth = (revenue_final / revenue_year1) ** (1 / (n_quarters / 4)) - 1 if revenue_year1 > 0 else 0.05
    return [
        {
            "name": "Portfolio Return (%)",
            "unit": "%",
            "quarterly_targets": [round(5 + q * 0.8, 1) for q in range(n_quarters)],
        },
        {
            "name": "Assets Under Management (HKD M)",
            "unit": "HKD M",
            "quarterly_targets": [
                round(revenue_year1 * (1 + rev_growth) ** (q / 4), 3)
                for q in range(n_quarters)
            ],
        },
        {
            "name": "Risk-Adjusted Return (Sharpe Ratio)",
            "unit": "ratio",
            "quarterly_targets": [round(0.8 + q * 0.05, 2) for q in range(n_quarters)],
        },
    ]


def _cost_saving_kpis(capex: float, n_quarters: int = 8) -> list[dict]:
    """Standard KPI set for CostSaving projects."""
    quarterly_saving = capex * 0.05  # target 5% of capex per quarter saved
    return [
        {
            "name": "Cumulative Cost Savings (HKD M)",
            "unit": "HKD M",
            "quarterly_targets": [
                round(quarterly_saving * (q + 1), 3) for q in range(n_quarters)
            ],
        },
        {
            "name": "Process Efficiency (%)",
            "unit": "%",
            "quarterly_targets": [round(60 + q * 4, 1) for q in range(n_quarters)],
        },
        {
            "name": "Headcount Equivalent Saved",
            "unit": "FTE",
            "quarterly_targets": [int(2 * (q + 1)) for q in range(n_quarters)],
        },
    ]


_KPI_FACTORIES = {
    "CAPEX": _capex_kpis,
    "Investment": _investment_kpis,
    "CostSaving": _cost_saving_kpis,
}


@tool
def kpi_generator(
    capex_hkd_millions: float,
    project_type: str,
    revenue_year1: float = 0.0,
    revenue_final_year: float = 0.0,
) -> list[dict]:
    """Generate KPI sets scaled to project size and type.

    Args:
        capex_hkd_millions: Initial capital expenditure (HKD millions).
        project_type: One of 'CAPEX', 'Investment', or 'CostSaving'.
        revenue_year1: Projected Year-1 revenue/benefit (HKD millions).
        revenue_final_year: Projected final-year revenue/benefit (HKD millions).

    Returns list of KPI dicts (each with name, unit, quarterly_targets[8]).
    The number of sets follows the company threshold rule:
      >HK$10M → 3 sets,  >HK$2M → 1 set,  ≤HK$2M → 0 (optional).
    """
    n_sets = required_kpi_sets(capex_hkd_millions)
    if n_sets == 0:
        return []

    factory = _KPI_FACTORIES.get(project_type, _capex_kpis)

    if project_type == "CostSaving":
        all_kpis = factory(capex_hkd_millions)
    else:
        yr1 = revenue_year1 if revenue_year1 > 0 else capex_hkd_millions * 0.3
        yrf = revenue_final_year if revenue_final_year > 0 else yr1 * 1.5
        all_kpis = factory(yr1, yrf)

    return all_kpis[:n_sets]
