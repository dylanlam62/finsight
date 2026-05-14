from __future__ import annotations

DISCOUNT_RATE_PRETAX: float = 0.20
DEFAULT_ASSESSMENT_YEARS: int = 5

# ScraperAPI is used by the research tool; key loaded from env SCRAPER_API_KEY.
SCRAPER_API_BASE = "https://api.scraperapi.com/structured/google/search"


def required_kpi_sets(capex_hkd_m: float) -> int:
    if capex_hkd_m > 10:
        return 3
    if capex_hkd_m > 2:
        return 1
    return 0  # optional below HK$2M


def failure_threshold_pct(capex_hkd_m: float) -> float:
    """Minimum revenue/demand retention before a scenario is flagged as critical failure."""
    return 0.75 if capex_hkd_m >= 20 else 0.50


RED_FLAGS: dict[str, float] = {
    "irr_too_high": 1.00,    # >100% IRR requires explicit extra justification
    "margin_too_high": 0.50,  # >50% gross margin requires explicit extra justification
}

# Three mandatory downside scenarios (base case is scenario index 0).
SENSITIVITY_SCENARIOS: list[dict] = [
    {"name": "Demand -30%",           "demand_mult": 0.70, "price_mult": 1.00, "capex_mult": 1.00},
    {"name": "Price -50%",            "demand_mult": 1.00, "price_mult": 0.50, "capex_mult": 1.00},
    {"name": "80% of CAPEX applying", "demand_mult": 1.00, "price_mult": 1.00, "capex_mult": 0.80},
]

REQUIRED_SECTIONS: list[str] = [
    "executive_summary",
    "market_overview",
    "value_proposition",
    "project_description",
    "investment_and_return",
    "financials",
    "sensitivity",
    "kpis",
    "capex_breakdown",
    "risks",
    "implications",
    "key_success_factors",
    "recommendations",
    "appendices",
]
