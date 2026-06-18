import json
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database — accepts Railway's postgresql:// or our postgresql+asyncpg:// form
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

    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # File storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # CORS — accepts JSON array or comma-separated string
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v  # type: ignore[return-value]


settings = Settings()
