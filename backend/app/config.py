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
    log_json: bool = Field(default=False, alias="LOG_JSON")

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    database_url: str = Field(
        default="postgresql+asyncpg://user:pass@localhost/agrichain",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    redis_timeout_seconds: float = Field(default=2.5, alias="REDIS_TIMEOUT_SECONDS")
    redis_connect_retries: int = Field(default=2, alias="REDIS_CONNECT_RETRIES")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_minutes: int = 60 * 24 * 7

    web3_rpc_url: str = Field(default="http://localhost:8545", alias="WEB3_RPC_URL")
    batch_contract_address: str | None = Field(default=None, alias="BATCH_CONTRACT_ADDRESS")
    batch_contract_abi_path: str | None = Field(default=None, alias="BATCH_CONTRACT_ABI_PATH")
    blockchain_default_sender: str | None = Field(default=None, alias="BLOCKCHAIN_DEFAULT_SENDER")
    blockchain_request_timeout_seconds: float = Field(default=20.0, alias="BLOCKCHAIN_REQUEST_TIMEOUT_SECONDS")
    blockchain_failure_threshold: int = Field(default=3, alias="BLOCKCHAIN_FAILURE_THRESHOLD")
    blockchain_cooldown_seconds: int = Field(default=30, alias="BLOCKCHAIN_COOLDOWN_SECONDS")
    blockchain_health_cache_ttl_seconds: int = Field(default=10, alias="BLOCKCHAIN_HEALTH_CACHE_TTL_SECONDS")
    enable_blockchain_listener: bool = Field(default=False, alias="ENABLE_BLOCKCHAIN_LISTENER")
    blockchain_poll_interval: float = Field(default=3.0, alias="BLOCKCHAIN_POLL_INTERVAL")
    listener_heartbeat_cycles: int = Field(default=20, alias="LISTENER_HEARTBEAT_CYCLES")
    ipfs_api_url: str = Field(default="http://localhost:5001", alias="IPFS_API_URL")

    otp_provider: Literal["debug", "twilio", "fast2sms"] = Field(default="debug", alias="OTP_PROVIDER")
    otp_ttl_seconds: int = Field(default=300, alias="OTP_TTL_SECONDS")
    otp_max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")

    twilio_account_sid: str | None = Field(default=None, alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str | None = Field(default=None, alias="TWILIO_AUTH_TOKEN")
    twilio_from_number: str | None = Field(default=None, alias="TWILIO_FROM_NUMBER")

    fast2sms_api_key: str | None = Field(default=None, alias="FAST2SMS_API_KEY")
    fast2sms_sender_id: str = Field(default="FSTSMS", alias="FAST2SMS_SENDER_ID")
    fast2sms_route: str = Field(default="q", alias="FAST2SMS_ROUTE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()
