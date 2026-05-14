"""Sensitivity analysis: base case + 3 standard downside scenarios."""
from __future__ import annotations

from langchain_core.tools import tool

from shared.guidelines import DISCOUNT_RATE_PRETAX, SENSITIVITY_SCENARIOS
from shared.tools.financial import calc_irr, calc_npv, calc_payback


def _run_scenario(
    name: str,
    base_cashflows: list[float],
    capex_hkd_millions: float,
    base_revenue: float,
    base_costs: float,
    demand_mult: float,
    price_mult: float,
    capex_mult: float,
) -> dict:
    adj_capex = capex_hkd_millions * capex_mult
    # Scale each cashflow proportionally to demand and price changes
    scale = demand_mult * price_mult
    adj_cashflows = [cf * scale for cf in base_cashflows]

    all_flows = [-adj_capex] + adj_cashflows
    irr = calc_irr(all_flows)
    npv = calc_npv(DISCOUNT_RATE_PRETAX, all_flows)
    payback = calc_payback(adj_capex, adj_cashflows)

    adj_revenue = base_revenue * demand_mult * price_mult
    adj_margin = (adj_revenue - base_costs) / adj_revenue if adj_revenue > 0 else 0.0

    return {
        "name": name,
        "capex": round(adj_capex, 4),
        "irr": round(irr * 100, 2) if irr is not None else None,
        "npv": round(npv, 4),
        "margin_pct": round(adj_margin * 100, 2),
        "payback": round(payback, 2) if payback != float("inf") else None,
    }


@tool
def sensitivity_analyzer(
    base_cashflows: list[float],
    capex_hkd_millions: float,
    base_annual_revenue: float,
    base_annual_costs: float,
) -> list[dict]:
    """Generate base case + 3 standard downside scenarios per company guidelines.

    Args:
        base_cashflows: Annual net cash inflows in HKD millions (Year 1 onward).
        capex_hkd_millions: Initial capital expenditure (HKD millions).
        base_annual_revenue: Year-1 gross revenue (HKD millions) — used for margin calc.
        base_annual_costs: Year-1 total costs excluding capex (HKD millions).

    Returns list of SensitivityScenario dicts: index 0 is the base case, 1-3 are downside.
    """
    # Base case (no adjustments)
    base_all_flows = [-capex_hkd_millions] + list(base_cashflows)
    base_irr = calc_irr(base_all_flows)
    base_npv = calc_npv(DISCOUNT_RATE_PRETAX, base_all_flows)
    base_payback = calc_payback(capex_hkd_millions, list(base_cashflows))
    base_margin = (
        (base_annual_revenue - base_annual_costs) / base_annual_revenue
        if base_annual_revenue > 0
        else 0.0
    )

    results = [
        {
            "name": "Base Case",
            "capex": round(capex_hkd_millions, 4),
            "irr": round(base_irr * 100, 2) if base_irr is not None else None,
            "npv": round(base_npv, 4),
            "margin_pct": round(base_margin * 100, 2),
            "payback": round(base_payback, 2) if base_payback != float("inf") else None,
        }
    ]

    for scenario in SENSITIVITY_SCENARIOS:
        results.append(
            _run_scenario(
                name=scenario["name"],
                base_cashflows=list(base_cashflows),
                capex_hkd_millions=capex_hkd_millions,
                base_revenue=base_annual_revenue,
                base_costs=base_annual_costs,
                demand_mult=scenario["demand_mult"],
                price_mult=scenario["price_mult"],
                capex_mult=scenario["capex_mult"],
            )
        )

    return results
