import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent import DeepAgent
from app.models.subagent import SubAgent, SubagentTool
from app.models.tool import Tool
from app.schemas.subagent import SubAgentCreate, SubAgentDetail, SubAgentUpdate

router = APIRouter(tags=["subagents"])


@router.get("/agents/{agent_id}/subagents", response_model=list[SubAgentDetail])
async def list_subagents(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(DeepAgent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = await db.execute(select(SubAgent).where(SubAgent.deep_agent_id == agent_id))
    return result.scalars().all()


@router.post("/agents/{agent_id}/subagents", response_model=SubAgentDetail, status_code=201)
async def create_subagent(agent_id: str, body: SubAgentCreate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(DeepAgent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    sa = SubAgent(id=str(uuid.uuid4()), deep_agent_id=agent_id, **body.model_dump(exclude={"tool_ids"}))
    db.add(sa)
    await db.flush()

    if body.tool_ids:
        tools = (await db.execute(select(Tool).where(Tool.id.in_(body.tool_ids)))).scalars().all()
        for t in tools:
            db.add(SubagentTool(subagent_id=sa.id, tool_id=t.id))

    await db.commit()
    await db.refresh(sa)
    return sa


@router.get("/subagents/{subagent_id}", response_model=SubAgentDetail)
async def get_subagent(subagent_id: str, db: AsyncSession = Depends(get_db)):
    sa = await db.get(SubAgent, subagent_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Sub-agent not found")
    return sa


@router.put("/subagents/{subagent_id}", response_model=SubAgentDetail)
async def update_subagent(subagent_id: str, body: SubAgentUpdate, db: AsyncSession = Depends(get_db)):
    sa = await db.get(SubAgent, subagent_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Sub-agent not found")

    for field, value in body.model_dump(exclude_none=True, exclude={"tool_ids"}).items():
        setattr(sa, field, value)

    if body.tool_ids is not None:
        await db.execute(
            SubagentTool.__table__.delete().where(SubagentTool.subagent_id == subagent_id)  # type: ignore[attr-defined]
        )
        tools = (await db.execute(select(Tool).where(Tool.id.in_(body.tool_ids)))).scalars().all()
        for t in tools:
            db.add(SubagentTool(subagent_id=subagent_id, tool_id=t.id))

    await db.commit()
    await db.refresh(sa)
    return sa


@router.delete("/subagents/{subagent_id}", status_code=204)
async def delete_subagent(subagent_id: str, db: AsyncSession = Depends(get_db)):
    sa = await db.get(SubAgent, subagent_id)
    if not sa:
        raise HTTPException(status_code=404, detail="Sub-agent not found")
    await db.delete(sa)
    await db.commit()
