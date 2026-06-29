from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = Field(default="tcc-backend", alias="APP_NAME")
    app_env: Literal["development", "production"] = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database
    database_url: str = Field(
        default="postgresql://tcc:tcc@localhost:5432/tcc",
        alias="DATABASE_URL",
    )

    # LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # LangSmith
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="tcc-backend", alias="LANGCHAIN_PROJECT")

    # Security
    api_key: str = Field(default="", alias="API_KEY")
    supabase_jwt_secret: str = Field(default="", alias="SUPABASE_JWT_SECRET")
    supabase_url: str = Field(default="", alias="SUPABASE_URL")

    @property
    def supabase_jwks_url(self) -> str | None:
        if not self.supabase_url:
            return None
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"

    @property
    def supabase_jwt_issuer(self) -> str | None:
        if not self.supabase_url:
            return None
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def sqlalchemy_database_url(self) -> str:
        """SQLAlchemy URL using psycopg v3 (project default driver)."""
        url = self.database_url
        if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def langsmith_enabled(self) -> bool:
        return self.langchain_tracing_v2 and bool(self.langchain_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
