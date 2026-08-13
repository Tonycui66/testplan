import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "DevOps Platform"
    version: str = "0.1.0-alpha"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://devops:devops123@localhost:5432/devops_platform",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()
