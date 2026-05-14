from shared.tools.financial import financial_calculator
from shared.tools.sensitivity import sensitivity_analyzer
from shared.tools.kpi import kpi_generator
from shared.tools.validator import validate_bcase
from shared.tools.market_research import market_research
from shared.tools.document_parser import document_parser
from shared.tools.template_renderer import template_renderer
from shared.tools.risk_register import risk_register
from shared.tools.human import ask_human

ALL_TOOLS = [
    financial_calculator,
    sensitivity_analyzer,
    kpi_generator,
    validate_bcase,
    market_research,
    document_parser,
    template_renderer,
    risk_register,
    ask_human,
]
