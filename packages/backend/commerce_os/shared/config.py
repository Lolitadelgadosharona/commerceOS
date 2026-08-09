from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COMMERCE_OS_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite+pysqlite:///./commerce_os.db"
    redis_url: str = "redis://localhost:6379/0"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
