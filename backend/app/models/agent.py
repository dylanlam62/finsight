import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AgentTool(Base):
    __tablename__ = "agent_tools"

    agent_id: Mapped[str] = mapped_column(String, ForeignKey("deep_agents.id", ondelete="CASCADE"), primary_key=True)
    tool_id: Mapped[str] = mapped_column(String, ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True)


class DeepAgent(Base):
    __tablename__ = "deep_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String, default="openai:gpt-4o")
    temperature: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    subagents: Mapped[list["SubAgent"]] = relationship(  # noqa: F821
        "SubAgent", back_populates="deep_agent", cascade="all, delete-orphan"
    )
    tools: Mapped[list["Tool"]] = relationship(  # noqa: F821
        "Tool", secondary="agent_tools", lazy="selectin"
    )
    runs: Mapped[list["AgentRun"]] = relationship(  # noqa: F821
        "AgentRun", back_populates="agent", cascade="all, delete-orphan"
    )
