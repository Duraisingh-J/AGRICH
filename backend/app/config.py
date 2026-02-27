"""Application configuration for AGRICHAIN backend."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AGRICHAIN Backend"
    app_env: Literal["development", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/agrichain",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7

    web3_rpc_url: str = Field(default="http://localhost:8545", alias="WEB3_RPC_URL")
    batch_contract_address: str | None = Field(default=None, alias="BATCH_CONTRACT_ADDRESS")
    batch_contract_abi_path: str | None = Field(default=None, alias="BATCH_CONTRACT_ABI_PATH")
    blockchain_default_sender: str | None = Field(default=None, alias="BLOCKCHAIN_DEFAULT_SENDER")
    ipfs_api_url: str = Field(default="http://localhost:5001", alias="IPFS_API_URL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
