"""Seed Business Case Writer agent with 5 sub-agents and tool assignments

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-14
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SUPERVISOR_PROMPT = """\
You write comprehensive business cases for Hong Kong companies following strict internal guidelines.

## Core Rules
- Discount rate: 20% pre-tax (never change without explicit instruction)
- Default assessment period: 5 years
- KPI sets required: 3 if CAPEX > HK$10M | 1 if > HK$2M | 0 optional if ≤ HK$2M
- Failure threshold: 75% if CAPEX ≥ HK$20M | 50% otherwise
- Red flags requiring explicit extra justification: IRR > 100%, gross margin > 50%
- NEVER invent financial numbers — every figure must come from a tool call

## Workflow
1. Use write_todos to plan all sections before starting work
2. Review the input for missing or contradictory data — delegate clarification to hitl-agent before proceeding
3. Delegate market research and document parsing to research-agent
4. Delegate ALL financial calculations (IRR, NPV, payback, CAGR, sensitivity, KPIs) to finance-agent
5. Delegate section writing to writer-agent using the outputs from steps 3–4
6. Delegate final validation and risk register to compliance-agent
7. Fix any issues raised by compliance-agent, then compile the final document

## Required Sections (all 14 must be present and non-empty)
executive_summary, market_overview, value_proposition, project_description,
investment_and_return, financials, sensitivity, kpis, capex_breakdown, risks,
implications (financial / legal / tax / co_sec), key_success_factors,
recommendations, appendices
"""

RESEARCH_PROMPT = """\
You gather market intelligence to support business case development.

## Your tasks
- Use market_research to search for: market size, growth rates, key trends, competitor landscape, regulatory context
- Use document_parser to extract text from any file attachments provided in the input
- Return structured findings clearly labelled for use by the finance and writer agents

## Rules
- Always cite the search query you used so results can be traced
- If a search returns no useful results, try a more specific or alternative query
- Flag any regulatory risks or compliance requirements you find
- Do not compute financial figures — return raw market data only
"""

FINANCE_PROMPT = """\
You compute all financial metrics for business cases. NEVER invent or estimate numbers.

## Rules (non-negotiable)
- Call financial_calculator for IRR, NPV, payback, and CAGR — never compute these manually
- Call sensitivity_analyzer for the scenario table — always produces base case + 3 downside scenarios
- Call kpi_generator for KPI sets — pass the correct capex_hkd_millions and project_type
- Discount rate is 20% pre-tax; do not change unless explicitly overridden by the sponsor
- If Year-1 cashflow data is missing, return an error — do not assume or estimate

## Red flag checks
- IRR > 100%: flag it and request that writer-agent adds explicit justification to investment_and_return
- Gross margin > 50%: flag it and request explicit justification in value_proposition

## Output format
Return a structured dict with keys: financials (FinancialMetrics), sensitivity (list of scenarios), kpis (list of KPI sets).
"""

WRITER_PROMPT = """\
You write the narrative sections of a business case using markdown templates.

## Rules
- Always call template_renderer for each section — never write free-text sections without using the tool
- Write for a board-level audience: concise, evidence-based, no padding or filler
- Each section must be substantive and specific to this project — no generic boilerplate
- Use numbers from finance-agent outputs and market data from research-agent — do not invent figures
- If a red flag was raised (IRR > 100% or margin > 50%), include explicit justification in the relevant section

## Sections you are responsible for
executive_summary, market_overview, value_proposition, project_description,
investment_and_return, financials, sensitivity, kpis, capex_breakdown,
implications, key_success_factors, recommendations, appendices
"""

COMPLIANCE_PROMPT = """\
You validate business cases against company standards and generate the risk register.

## Tasks
1. Call validate_bcase on the complete BCaseOutput dict — report every warning returned
2. Call risk_register with the project_type and capex_hkd_millions to generate the structured risk list
3. Check that all 4 implication areas are covered: financial, legal, tax, co_sec
4. Verify red-flag sections contain explicit justification text (not just acknowledgement)
5. Confirm KPI count matches the threshold rule

## Output
Return:
- A list of issues that must be fixed before the business case is approved
- The completed risk register (list of risk dicts)
- A pass/fail compliance verdict

If any critical issues exist (missing required section, un-justified red flag), mark as FAIL.
"""

HITL_PROMPT = """\
You ask the human user focused clarifying questions when inputs are missing or contradictory.

## When to trigger
- Revenue or margin data is completely absent
- Growth rate in assumptions contradicts the description (e.g. 0% growth but "fastest-growing market")
- Margin in assumptions contradicts the description (e.g. 65% margin but "thin margins, highly competitive")
- Project scope is too vague to build a financial model
- A key assumption is internally inconsistent

## Rules
- Ask one focused question at a time using ask_human tool
- Reference the exact field or assumption that is unclear (quote it)
- Never guess or fill in missing values yourself
- After receiving an answer, summarise the clarification and hand back to the supervisor
"""

# ---------------------------------------------------------------------------
# Tool-to-subagent mapping
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    # BCase tools — all assigned at agent level so the graph can route them
    "financial_calculator", "sensitivity_analyzer", "kpi_generator",
    "validate_bcase", "market_research", "document_parser",
    "template_renderer", "risk_register", "ask_human",
    # Deepagents built-ins the supervisor needs
    "write_todos", "task",
]

SUBAGENT_TOOLS: dict[str, list[str]] = {
    "research-agent":    ["market_research", "document_parser"],
    "finance-agent":     ["financial_calculator", "sensitivity_analyzer", "kpi_generator"],
    "writer-agent":      ["template_renderer"],
    "compliance-agent":  ["validate_bcase", "risk_register"],
    "hitl-agent":        ["ask_human"],
}

SUBAGENTS = [
    {
        "name": "research-agent",
        "description": "Gathers market data, competitor intelligence, and regulatory context via web search and document parsing",
        "system_prompt": RESEARCH_PROMPT,
        "model": None,
    },
    {
        "name": "finance-agent",
        "description": "Computes all financial metrics (IRR, NPV, payback, CAGR, sensitivity table, KPIs) — never invents numbers",
        "system_prompt": FINANCE_PROMPT,
        "model": None,
    },
    {
        "name": "writer-agent",
        "description": "Writes all 14 business case sections using structured markdown templates",
        "system_prompt": WRITER_PROMPT,
        "model": None,
    },
    {
        "name": "compliance-agent",
        "description": "Validates the business case against company guidelines and generates the risk register",
        "system_prompt": COMPLIANCE_PROMPT,
        "model": None,
    },
    {
        "name": "hitl-agent",
        "description": "Asks the user clarifying questions when inputs are missing or contradictory",
        "system_prompt": HITL_PROMPT,
        "model": None,
    },
]


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def upgrade() -> None:
    conn = op.get_bind()

    # Idempotency check — skip if already seeded
    existing = conn.execute(
        sa.text("SELECT id FROM deep_agents WHERE name = 'Business Case Writer' LIMIT 1")
    ).fetchone()
    if existing:
        return

    agent_id = str(uuid.uuid4())

    # 1. Create the supervisor deep agent
    conn.execute(
        sa.text("""
            INSERT INTO deep_agents (id, name, description, system_prompt, model, temperature, created_at, updated_at)
            VALUES (:id, :name, :desc, :prompt, :model, :temp, now(), now())
        """),
        {
            "id": agent_id,
            "name": "Business Case Writer",
            "desc": "Writes comprehensive HK business cases per company guidelines — research, financials, narrative, compliance, and HITL in one agent",
            "prompt": SUPERVISOR_PROMPT,
            "model": "gpt-5.4-nano",
            "temp": 0.0,
        },
    )

    # 2. Assign tools to the agent (look up IDs by name)
    if AGENT_TOOLS:
        conn.execute(
            sa.text("""
                INSERT INTO agent_tools (agent_id, tool_id)
                SELECT :agent_id, id FROM tools WHERE name = ANY(:names)
                ON CONFLICT DO NOTHING
            """),
            {"agent_id": agent_id, "names": AGENT_TOOLS},
        )

    # 3. Create sub-agents and assign their tools
    for sa_def in SUBAGENTS:
        sa_id = str(uuid.uuid4())
        conn.execute(
            sa.text("""
                INSERT INTO sub_agents (id, deep_agent_id, name, description, system_prompt, model, created_at, updated_at)
                VALUES (:id, :deep_id, :name, :desc, :prompt, :model, now(), now())
            """),
            {
                "id": sa_id,
                "deep_id": agent_id,
                "name": sa_def["name"],
                "desc": sa_def["description"],
                "prompt": sa_def["system_prompt"],
                "model": sa_def["model"],
            },
        )

        tool_names = SUBAGENT_TOOLS.get(sa_def["name"], [])
        if tool_names:
            conn.execute(
                sa.text("""
                    INSERT INTO subagent_tools (subagent_id, tool_id)
                    SELECT :sa_id, id FROM tools WHERE name = ANY(:names)
                    ON CONFLICT DO NOTHING
                """),
                {"sa_id": sa_id, "names": tool_names},
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM deep_agents WHERE name = 'Business Case Writer'")
    )
