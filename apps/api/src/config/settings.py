"""Application settings loaded from environment variables."""
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "/app/data/tenant_metadata.db")

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS origins
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://shell-ui:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
