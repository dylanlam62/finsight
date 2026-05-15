import asyncio
from app.core.agent_factory import build_agent
from app.database import async_session_factory
from app.models.agent import DeepAgent
from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.subagent import SubAgent

async def main():
    async with async_session_factory() as db:
        result = await db.execute(
            select(DeepAgent)
            .options(selectinload(DeepAgent.subagents).selectinload(SubAgent.tools), selectinload(DeepAgent.tools))
            .where(DeepAgent.name == 'Business Case Writer')
        )
        agent_row = result.scalar_one_or_none()
    
    compiled = build_agent(agent_row)
    
    async for event in compiled.astream_events(
        {"messages": [HumanMessage("Just write a 1 sentence summary, no tools.")]},
        config={"configurable": {"thread_id": "test_123"}},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            print(event["metadata"].get("langgraph_path"))
            break

asyncio.run(main())
