"""Seed Business Case tools

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-14
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO tools (id, name, tool_type, description) VALUES
        (gen_random_uuid()::text, 'financial_calculator', 'builtin',
            'Compute IRR, NPV (at 20% pre-tax), payback period, and CAGR from annual cashflows'),
        (gen_random_uuid()::text, 'sensitivity_analyzer', 'builtin',
            'Generate base case + 3 downside scenarios (Demand -30%, Price -50%, 80% CAPEX)'),
        (gen_random_uuid()::text, 'kpi_generator', 'builtin',
            'Generate KPI sets (3/1/0 sets based on capex threshold) with 8 quarterly targets each'),
        (gen_random_uuid()::text, 'validate_bcase', 'builtin',
            'Validate a business case output: check all 14 sections, IRR/margin red flags, KPI count'),
        (gen_random_uuid()::text, 'market_research', 'builtin',
            'Search Google via ScraperAPI and return structured market intelligence'),
        (gen_random_uuid()::text, 'document_parser', 'builtin',
            'Extract text from file attachments (TXT, MD, PDF, DOCX)'),
        (gen_random_uuid()::text, 'template_renderer', 'builtin',
            'Render a named business-case section (e.g. executive_summary, kpis) to formatted markdown'),
        (gen_random_uuid()::text, 'risk_register', 'builtin',
            'Generate a structured risk register based on project type and capex size'),
        (gen_random_uuid()::text, 'ask_human', 'builtin',
            'Pause execution and ask the user a clarifying question (HITL via web form)')
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM tools WHERE name IN (
            'financial_calculator', 'sensitivity_analyzer', 'kpi_generator',
            'validate_bcase', 'market_research', 'document_parser',
            'template_renderer', 'risk_register', 'ask_human'
        )
    """)
