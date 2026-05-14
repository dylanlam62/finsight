import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.agent import AgentTool, DeepAgent
from app.models.run import AgentRun
from app.models.subagent import SubAgent
from app.models.tool import Tool
from app.schemas.agent import AgentCreate, AgentDetail, AgentSummary, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


async def _load_agent(db: AsyncSession, agent_id: str) -> DeepAgent:
    result = await db.execute(
        select(DeepAgent)
        .options(selectinload(DeepAgent.subagents).selectinload(SubAgent.tools), selectinload(DeepAgent.tools))
        .where(DeepAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("", response_model=list[AgentSummary])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            DeepAgent,
            func.count(SubAgent.id).label("subagent_count"),
        )
        .outerjoin(SubAgent, SubAgent.deep_agent_id == DeepAgent.id)
        .group_by(DeepAgent.id)
        .order_by(DeepAgent.created_at.desc())
    )
    rows = result.all()
    summaries = []
    for agent, count in rows:
        d = AgentSummary.model_validate(agent)
        d.subagent_count = count
        summaries.append(d)
    return summaries


@router.post("", response_model=AgentDetail, status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    agent = DeepAgent(id=str(uuid.uuid4()), **body.model_dump(exclude={"tool_ids"}))
    db.add(agent)
    await db.flush()

    if body.tool_ids:
        tools = (await db.execute(select(Tool).where(Tool.id.in_(body.tool_ids)))).scalars().all()
        for t in tools:
            db.add(AgentTool(agent_id=agent.id, tool_id=t.id))

    await db.commit()
    return await _load_agent(db, agent.id)


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    return await _load_agent(db, agent_id)


@router.put("/{agent_id}", response_model=AgentDetail)
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await _load_agent(db, agent_id)

    for field, value in body.model_dump(exclude_none=True, exclude={"tool_ids"}).items():
        setattr(agent, field, value)

    if body.tool_ids is not None:
        await db.execute(
            AgentTool.__table__.delete().where(AgentTool.agent_id == agent_id)  # type: ignore[attr-defined]
        )
        tools = (await db.execute(select(Tool).where(Tool.id.in_(body.tool_ids)))).scalars().all()
        for t in tools:
            db.add(AgentTool(agent_id=agent_id, tool_id=t.id))

    await db.commit()
    return await _load_agent(db, agent_id)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(DeepAgent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()


@router.get("/{agent_id}/runs", response_model=list[dict])
async def list_runs(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun).where(AgentRun.agent_id == agent_id).order_by(AgentRun.created_at.desc()).limit(50)
    )
    return [
        {
            "id": r.id,
            "agent_id": r.agent_id,
            "input": r.input,
            "output": r.output,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in result.scalars().all()
    ]
