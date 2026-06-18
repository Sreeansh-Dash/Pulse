from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulse.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    DISCORD_WEBHOOK_URL: Optional[str] = None
    CHECK_INTERVAL_SECONDS: int = 120
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
