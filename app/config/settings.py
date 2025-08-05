"""Application settings configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server configuration
    host: str
    port: int
    debug: bool
    
    # Database configuration
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_echo: bool
    
    @computed_field
    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Redis configuration
    redis_url: str
    
    # CORS configuration
    allowed_origins: List[str]
    
    # Agent configuration
    max_response_length: int
    
    # Security
    secret_key: str
    
    # External APIs
    openai_api_key: str
    anthropic_api_key: str


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 