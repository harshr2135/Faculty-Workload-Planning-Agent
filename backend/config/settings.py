"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fwp_env: str = "development"
    fwp_debug: bool = True
    fwp_api_prefix: str = "/api/v1"
    fwp_app_name: str = "Faculty Workload Planning Agent"

    fwp_database_url: str = (
        "postgresql+asyncpg://fwp_user:fwp_password@127.0.0.1:15432/fwp_db"
    )
    fwp_database_pool_size: int = 10
    fwp_database_echo: bool = False

    fwp_cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.fwp_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
