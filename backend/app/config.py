from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/deepagents"
    openai_api_key: str = ""
    openai_base_url: str = ""          # Custom OpenAI-compatible endpoint (e.g. Poe, Azure, Ollama)
    deepagent_model: str = "gpt-4o"   # Default model name (no provider prefix)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""


settings = Settings()
