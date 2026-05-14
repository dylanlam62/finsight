"""Lightweight settings endpoint — reads/writes .env at runtime."""

import os

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["settings"])

_ENV_FILE = ".env"


def _read_env() -> dict[str, str]:
    env: dict[str, str] = {}
    try:
        with open(_ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env


def _write_env(env: dict[str, str]) -> None:
    with open(_ENV_FILE, "w") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


class SettingsPayload(BaseModel):
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    deepagent_model: str | None = None
    langchain_api_key: str | None = None
    langchain_tracing_v2: bool | None = None


class SettingsResponse(BaseModel):
    openai_api_key_set: bool
    openai_base_url: str
    deepagent_model: str
    langchain_api_key_set: bool
    langchain_tracing_v2: bool


@router.get("", response_model=SettingsResponse)
async def get_settings():
    env = _read_env()
    return SettingsResponse(
        openai_api_key_set=bool(env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")),
        openai_base_url=env.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL", ""),
        deepagent_model=env.get("DEEPAGENT_MODEL") or os.environ.get("DEEPAGENT_MODEL", "gpt-4o"),
        langchain_api_key_set=bool(env.get("LANGCHAIN_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")),
        langchain_tracing_v2=(env.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"),
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsPayload):
    env = _read_env()

    if body.openai_api_key is not None:
        env["OPENAI_API_KEY"] = body.openai_api_key
        os.environ["OPENAI_API_KEY"] = body.openai_api_key

    if body.openai_base_url is not None:
        env["OPENAI_BASE_URL"] = body.openai_base_url
        os.environ["OPENAI_BASE_URL"] = body.openai_base_url

    if body.deepagent_model is not None:
        env["DEEPAGENT_MODEL"] = body.deepagent_model
        os.environ["DEEPAGENT_MODEL"] = body.deepagent_model

    if body.langchain_api_key is not None:
        env["LANGCHAIN_API_KEY"] = body.langchain_api_key
        os.environ["LANGCHAIN_API_KEY"] = body.langchain_api_key

    if body.langchain_tracing_v2 is not None:
        env["LANGCHAIN_TRACING_V2"] = str(body.langchain_tracing_v2).lower()
        os.environ["LANGCHAIN_TRACING_V2"] = str(body.langchain_tracing_v2).lower()

    _write_env(env)
    return await get_settings()
