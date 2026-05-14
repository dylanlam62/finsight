from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agents, runs, settings, subagents, tools

app = FastAPI(title="DeepAgents UI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router, prefix="/api")
app.include_router(subagents.router, prefix="/api")
app.include_router(tools.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
