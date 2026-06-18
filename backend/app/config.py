from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulse.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    DISCORD_WEBHOOK_URL: Optional[str] = None
    CHECK_INTERVAL_SECONDS: int = 120
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
