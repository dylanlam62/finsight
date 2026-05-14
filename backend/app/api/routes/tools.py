import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tool import Tool
from app.schemas.tool import ToolCreate, ToolDetail, ToolUpdate

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolDetail])
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tool).order_by(Tool.tool_type, Tool.name))
    return result.scalars().all()


@router.post("", response_model=ToolDetail, status_code=201)
async def create_tool(body: ToolCreate, db: AsyncSession = Depends(get_db)):
    tool = Tool(id=str(uuid.uuid4()), **body.model_dump())
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.get("/{tool_id}", response_model=ToolDetail)
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.put("/{tool_id}", response_model=ToolDetail)
async def update_tool(tool_id: str, body: ToolUpdate, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.tool_type == "builtin":
        raise HTTPException(status_code=400, detail="Built-in tools cannot be modified")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tool, field, value)
    await db.commit()
    await db.refresh(tool)
    return tool


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if tool.tool_type == "builtin":
        raise HTTPException(status_code=400, detail="Built-in tools cannot be deleted")
    await db.delete(tool)
    await db.commit()
