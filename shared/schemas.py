from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class BCaseInput(BaseModel):
    project_name: str
    project_type: Literal["CAPEX", "Investment", "CostSaving"]
    sponsor: str
    project_manager: str
    business_unit: str
    capex_hkd_millions: float
    description: str
    assumptions: dict
    attachments: list[str] = []
    known_market_data: dict = {}


class FinancialMetrics(BaseModel):
    irr_pct: float
    npv_hkd_millions: float
    payback_years: float
    cagr_pct: Optional[float] = None
    cashflow_by_year: list[float]


class SensitivityScenario(BaseModel):
    name: str
    capex: float
    irr: float
    npv: float
    margin_pct: float
    payback: float


class KPI(BaseModel):
    name: str
    quarterly_targets: list[float] = Field(..., min_length=8, max_length=8)
    unit: str


class BCaseOutput(BaseModel):
    executive_summary: str
    market_overview: str
    value_proposition: str
    project_description: str
    investment_and_return: str
    financials: FinancialMetrics
    sensitivity: list[SensitivityScenario] = Field(..., min_length=4)
    kpis: list[KPI]
    capex_breakdown: dict
    risks: list[dict]
    implications: dict  # financial, legal, tax, co_sec
    key_success_factors: list[str]
    recommendations: str
    appendices: list[str]

    clarifications_asked: list[str] = []
    validation_warnings: list[str] = []
