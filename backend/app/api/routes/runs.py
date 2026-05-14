"""Run endpoint with SSE streaming and HITL resume support."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.agent_factory import build_agent
from app.core.run_registry import evict, lookup, register
from app.database import async_session_factory, get_db
from app.models.agent import DeepAgent
from app.models.run import AgentRun
from app.models.subagent import SubAgent
from app.schemas.run import RunCreate, RunDetail

router = APIRouter(tags=["runs"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Access-Control-Allow-Origin": "*",
}


def _sse_default(obj: object) -> object:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return str(obj)


async def _load_agent_full(db: AsyncSession, agent_id: str) -> DeepAgent:
    result = await db.execute(
        select(DeepAgent)
        .options(selectinload(DeepAgent.subagents).selectinload(SubAgent.tools), selectinload(DeepAgent.tools))
        .where(DeepAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def _make_event_stream(compiled, run_id: str, graph_input):
    """Shared SSE generator for initial runs and resumes."""

    async def event_stream():
        output_parts: list[str] = []
        steps: list[dict] = []
        hitl: dict | None = None  # set when ask_human fires without matching tool_end

        try:
            async for event in compiled.astream_events(
                graph_input,
                config={"configurable": {"thread_id": run_id}},
                version="v2",
            ):
                kind = event.get("event", "")
                payload: dict = {"type": kind, "data": event}

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", {})
                    content = getattr(chunk, "content", "") or ""
                    if content:
                        output_parts.append(content)

                if kind == "on_tool_start":
                    safe_data = json.loads(json.dumps(event.get("data", {}), default=_sse_default))
                    steps.append({"event": kind, "name": event.get("name", ""), "data": safe_data})
                    if event.get("name") == "ask_human":
                        tool_input = event.get("data", {}).get("input", {})
                        hitl = {
                            "question": tool_input.get("question", ""),
                            "options": tool_input.get("options") or [],
                        }

                if kind == "on_tool_end":
                    safe_data = json.loads(json.dumps(event.get("data", {}), default=_sse_default))
                    steps.append({"event": kind, "name": event.get("name", ""), "data": safe_data})
                    if event.get("name") == "ask_human":
                        hitl = None  # tool completed without interrupt (shouldn't happen, but be safe)

                yield f"data: {json.dumps(payload, default=_sse_default)}\n\n"

            # Stream ended — decide final status
            async with async_session_factory() as db2:
                run_record = await db2.get(AgentRun, run_id)
                if run_record:
                    safe_steps = json.loads(json.dumps(steps, default=_sse_default))
                    run_record.steps = safe_steps
                    run_record.completed_at = datetime.utcnow()
                    run_record.output = "".join(output_parts)

                    if hitl:
                        run_record.status = "interrupted"
                        await db2.commit()
                        yield f"data: {json.dumps({'type': 'interrupt', 'run_id': run_id, **hitl})}\n\n"
                    else:
                        run_record.status = "completed"
                        await db2.commit()
                        evict(run_id)
                        yield f"data: {json.dumps({'type': 'done', 'run_id': run_id})}\n\n"

        except Exception as exc:
            async with async_session_factory() as db2:
                run_record = await db2.get(AgentRun, run_id)
                if run_record:
                    run_record.status = "failed"
                    run_record.completed_at = datetime.utcnow()
                await db2.commit()

            evict(run_id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return event_stream


@router.post("/agents/{agent_id}/run")
async def start_run(agent_id: str, body: RunCreate, db: AsyncSession = Depends(get_db)):
    """Start a run and stream events back as SSE."""
    agent_row = await _load_agent_full(db, agent_id)

    run_id = str(uuid.uuid4())
    run = AgentRun(
        id=run_id,
        agent_id=agent_id,
        input=body.input,
        status="running",
        steps=[],
    )
    db.add(run)
    await db.commit()

    compiled = build_agent(agent_row)
    register(run_id, compiled)

    event_stream = _make_event_stream(
        compiled, run_id, {"messages": [HumanMessage(body.input)]}
    )

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)


class ResumeBody(BaseModel):
    answer: str


@router.post("/runs/{run_id}/resume")
async def resume_run(run_id: str, body: ResumeBody, db: AsyncSession = Depends(get_db)):
    """Resume a run that is waiting for human input (ask_human interrupt)."""
    compiled = lookup(run_id)
    if not compiled:
        raise HTTPException(status_code=404, detail="Run not found or already completed")

    run_record = await db.get(AgentRun, run_id)
    if not run_record:
        raise HTTPException(status_code=404, detail="Run record not found")

    run_record.status = "running"
    await db.commit()

    event_stream = _make_event_stream(compiled, run_id, Command(resume=body.answer))

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
