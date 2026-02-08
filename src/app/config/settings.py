"""Application settings using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "task-tracker"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/task_tracker"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Security
    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_private_key_path: str = "./keys/private_key.pem"
    jwt_public_key_path: str = "./keys/public_key.pem"

    # Password Hashing (Argon2)
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    login_rate_limit_requests: int = 5
    login_rate_limit_window: int = 60

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True

    # Security
    secret_key: str = "change-me-in-production"
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_list(cls, v):
        """Parse comma-separated string or JSON list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [item.strip() for item in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    def get_jwt_private_key(self) -> str:
        """Load JWT private key from file."""
        key_path = Path(self.jwt_private_key_path)
        if not key_path.exists():
            raise FileNotFoundError(
                f"JWT private key not found at {key_path}. "
                "Run 'python scripts/generate_keys.py' to generate keys."
            )
        return key_path.read_text()

    def get_jwt_public_key(self) -> str:
        """Load JWT public key from file."""
        key_path = Path(self.jwt_public_key_path)
        if not key_path.exists():
            raise FileNotFoundError(
                f"JWT public key not found at {key_path}. "
                "Run 'python scripts/generate_keys.py' to generate keys."
            )
        return key_path.read_text()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
