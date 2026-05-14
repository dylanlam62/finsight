from datetime import datetime

from pydantic import BaseModel

from app.schemas.tool import ToolDetail


class SubAgentBase(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""
    model: str | None = None


class SubAgentCreate(SubAgentBase):
    tool_ids: list[str] = []


class SubAgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    tool_ids: list[str] | None = None


class SubAgentDetail(SubAgentBase):
    id: str
    deep_agent_id: str
    tools: list[ToolDetail] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
