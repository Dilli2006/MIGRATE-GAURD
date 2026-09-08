"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://migrateguard:migrateguard@localhost:5432/migrateguard"
    DATABASE_URL_RAW: str = "postgresql://migrateguard:migrateguard@localhost:5432/"
    PRISMA_SCHEMA_PATH: str = "./prisma/schema.prisma"
    PRISMA_MIGRATIONS_DIR: str = "./prisma/migrations"
    WEBHOOK_SECRET: str = ""
    SLACK_WEBHOOK_URL: str = ""
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

