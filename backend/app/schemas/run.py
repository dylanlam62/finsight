from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel


class RunCreate(BaseModel):
    input: str


class RunSummary(BaseModel):
    id: str
    agent_id: str
    input: str
    status: Literal["running", "completed", "failed"]
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class RunDetail(RunSummary):
    output: str
    steps: list[Any] | None = None

    model_config = {"from_attributes": True}
