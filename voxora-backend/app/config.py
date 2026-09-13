"""
Voxora Backend — Application Configuration

Uses pydantic-settings for type-safe environment variable loading.
"""

from functools import lru_cache
from typing import Any

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
    app_name: str = "voxora-backend"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://voxora:voxora_dev_2026@localhost:5432/voxora"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # LLM Settings & Multi-Provider
    llm_provider: str = "gemini"  # "gemini" | "groq" | "openai"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"

    # OpenAI (Optional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Google Cloud
    google_cloud_project: str = ""
    google_application_credentials: str = ""
    gcp_service_account_json: str = ""

    # BigQuery
    bigquery_project: str = ""
    bigquery_dataset: str = ""
    bigquery_max_bytes_billed: int = 100 * 1024 * 1024  # Cap at 100 MB per query to prevent runaway costs

    # CORS
    cors_origins: str | list[str] = ["http://localhost:3000"]

    @field_validator("database_url", mode="before")
    @classmethod
    def parse_database_url(cls, v: Any) -> str:
        if not isinstance(v, str):
            return v
        # Ensure asyncpg driver is specified
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]

        # asyncpg does not accept sslmode or channel_binding as query parameters in DSN
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(v)
        if parsed.query:
            query_params = parse_qs(parsed.query)
            query_params.pop("sslmode", None)
            query_params.pop("channel_binding", None)
            new_query = urlencode(query_params, doseq=True)
            v = urlunparse(parsed._replace(query=new_query))
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(origin).strip() for origin in parsed if str(origin).strip()]
                return [str(parsed).strip()]
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["*"]

    def model_post_init(self, __context: Any) -> None:
        import os
        import tempfile

        # If GCP service account JSON is passed as string, write to a temp file
        raw_json = self.gcp_service_account_json or (
            self.google_application_credentials
            if "{" in self.google_application_credentials
            else ""
        )
        if raw_json and "{" in raw_json:
            tmp_path = os.path.join(tempfile.gettempdir(), "gcp-service-account.json")
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write(raw_json.strip())
                self.google_application_credentials = tmp_path
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not write GCP service account temp file: %s", e)
        elif self.google_application_credentials and os.path.exists(self.google_application_credentials):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(self.google_application_credentials)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
