from datetime import datetime

from pydantic import BaseModel

from app.schemas.subagent import SubAgentDetail
from app.schemas.tool import ToolDetail


class AgentBase(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""
    model: str = "openai:gpt-4o"
    temperature: float = 0.0


class AgentCreate(AgentBase):
    tool_ids: list[str] = []


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    temperature: float | None = None
    tool_ids: list[str] | None = None


class AgentSummary(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    subagent_count: int = 0

    model_config = {"from_attributes": True}


class AgentDetail(AgentBase):
    id: str
    created_at: datetime
    updated_at: datetime
    subagents: list[SubAgentDetail] = []
    tools: list[ToolDetail] = []

    model_config = {"from_attributes": True}
