import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — accepts Render's postgresql:// or our postgresql+asyncpg:// form
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/essassess"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # Auth
    jwt_secret_key: str = "dev-secret-key"
    jwt_refresh_secret_key: str = "dev-refresh-secret-key"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # AI — set ANTHROPIC_API_KEY for Claude (paid) or GOOGLE_API_KEY for Gemini (free)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # File storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # CORS — typed Any so pydantic-settings passes the raw string to our validator
    # (list[str] causes pydantic-settings to JSON-parse the env var, breaking "*" or CSV values)
    cors_origins: Any = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return v
        return [str(v)]


settings = Settings()
