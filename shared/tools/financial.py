"""Pure-Python financial calculations — no LLM, fully unit-testable."""
from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from shared.guidelines import DISCOUNT_RATE_PRETAX


# ---------------------------------------------------------------------------
# Internal helpers (pure Python, importable by sensitivity.py without the
# LangChain wrapper)
# ---------------------------------------------------------------------------

def _npv(rate: float, cashflows: list[float]) -> float:
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(cashflows))


def _dnpv(rate: float, cashflows: list[float]) -> float:
    return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cashflows))


def calc_irr(cashflows: list[float], max_iter: int = 300, tol: float = 1e-9) -> Optional[float]:
    """Newton-Raphson IRR with bisection fallback. Returns None if no real IRR exists."""
    # Must have at least one sign change
    signs = [1 if cf >= 0 else -1 for cf in cashflows]
    if len(set(signs)) < 2:
        return None

    # Newton-Raphson from initial guess
    r = 0.1
    for _ in range(max_iter):
        f = _npv(r, cashflows)
        df = _dnpv(r, cashflows)
        if abs(df) < 1e-14:
            break
        r_new = r - f / df
        if abs(r_new - r) < tol:
            return r_new
        r = max(r_new, -0.9999)  # clamp away from -1 to avoid division by zero

    # Bisection fallback between -99.99% and +1000%
    lo, hi = -0.9999, 10.0
    if _npv(lo, cashflows) * _npv(hi, cashflows) > 0:
        return None  # No root in range
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if _npv(mid, cashflows) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def calc_npv(rate: float, cashflows: list[float]) -> float:
    return _npv(rate, cashflows)


def calc_payback(capex: float, annual_cashflows: list[float]) -> float:
    """Returns payback in years using linear interpolation. inf if never recovered."""
    cumulative = 0.0
    for i, cf in enumerate(annual_cashflows):
        prev = cumulative
        cumulative += cf
        if cumulative >= capex:
            fraction = (capex - prev) / cf if cf != 0 else 0
            return i + fraction
    return float("inf")


def calc_cagr(cashflows: list[float]) -> Optional[float]:
    """CAGR from first to last cashflow value. None if undefined."""
    if len(cashflows) < 2 or cashflows[0] <= 0 or cashflows[-1] <= 0:
        return None
    n = len(cashflows) - 1
    return (cashflows[-1] / cashflows[0]) ** (1 / n) - 1


# ---------------------------------------------------------------------------
# LangChain tool
# ---------------------------------------------------------------------------

@tool
def financial_calculator(
    cashflows: list[float],
    capex_hkd_millions: float,
    discount_rate: float = DISCOUNT_RATE_PRETAX,
) -> dict:
    """Compute IRR, NPV (at 20% pre-tax), payback period, and CAGR.

    Args:
        cashflows: Annual net cash inflows in HKD millions, Year 1 onward.
        capex_hkd_millions: Initial capital expenditure (positive number = outflow).
        discount_rate: Pre-tax discount rate; defaults to 20% per company guidelines.

    Returns dict matching FinancialMetrics schema.
    """
    all_flows = [-capex_hkd_millions] + list(cashflows)
    irr = calc_irr(all_flows)
    npv = calc_npv(discount_rate, all_flows)
    payback = calc_payback(capex_hkd_millions, list(cashflows))
    cagr = calc_cagr(list(cashflows))

    return {
        "irr_pct": round(irr * 100, 2) if irr is not None else None,
        "npv_hkd_millions": round(npv, 4),
        "payback_years": round(payback, 2) if payback != float("inf") else None,
        "cagr_pct": round(cagr * 100, 2) if cagr is not None else None,
        "cashflow_by_year": cashflows,
    }
