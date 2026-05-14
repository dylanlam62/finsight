from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class ToolBase(BaseModel):
    name: str
    tool_type: Literal["builtin", "custom"]
    description: str = ""
    config: dict[str, Any] | None = None


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict[str, Any] | None = None


class ToolDetail(ToolBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
