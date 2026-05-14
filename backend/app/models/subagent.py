import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubagentTool(Base):
    __tablename__ = "subagent_tools"

    subagent_id: Mapped[str] = mapped_column(String, ForeignKey("sub_agents.id", ondelete="CASCADE"), primary_key=True)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)


class SubAgent(Base):
    __tablename__ = "sub_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    deep_agent_id: Mapped[str] = mapped_column(String, ForeignKey("deep_agents.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    deep_agent: Mapped["DeepAgent"] = relationship("DeepAgent", back_populates="subagents")  # noqa: F821
    tools: Mapped[list["Tool"]] = relationship(  # noqa: F821
        "Tool", secondary="subagent_tools", lazy="selectin"
    )
