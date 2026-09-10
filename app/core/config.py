"""
Centralized application settings using Pydantic BaseSettings.

All environment variables are validated at startup. Missing required vars
cause an immediate, clear error instead of runtime surprises.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # -- Environment -----------------------------------------------------
    environment: str = Field(default="development", description="development | staging | production")
    debug: bool = False
    port: int = 8000

    # -- Security ----------------------------------------------------------
    # Also used to sign auth JWTs and password-reset/verification tokens
    # (see app/core/security.py) — set a real random value in production.
    secret_key: str = Field(default="change-me-in-production")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:8000")
    signed_url_secret: Optional[str] = None
    signed_url_expiry_seconds: int = 3600

    # -- Database (Postgres) ----------------------------------------------
    database_url: str = Field(default="", alias="DATABASE_URL")

    # Collection names within the shared `documents` table (kept as constants,
    # overridable via env) — carried over from the Appwrite collection IDs.
    collection_id_jobs: str = "jobs"
    collection_id_applications: str = "applications"
    collection_id_profiles: str = "profiles"
    collection_id_analytics: str = "analytics"
    collection_id_matches: str = "matches"

    # -- AI / LLM --------------------------------------------------------
    gemini_api_key: str = Field(default="")

    # -- Files -------------------------------------------------------------
    upload_folder: str = Field(default="uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="10 MB")
    allowed_extensions: str = "pdf,doc,docx"

    # -- Storage (local volume, e.g. a mounted Railway Volume) -------------
    storage_volume_path: str = Field(default="storage", alias="STORAGE_VOLUME_PATH")

    # Public base URL this API is reachable at — used to build signed file URLs.
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")

    # -- Job Search Defaults --------------------------------------------
    cv_file_path: str = "cvs/CV.pdf"
    search_query: str = "Python Developer"
    location: str = "South Africa"
    max_jobs: int = 10

    # -- Scraping & Caching ---------------------------------------------
    scraper_cache_dir: str = "job_cache"
    cache_max_age_hours: int = 24
    cache_max_size_mb: int = 100
    default_results_wanted: int = 20
    max_workers: int = 5
    api_max_retries: int = 3
    api_retry_delay: float = 2.0
    api_timeout: int = 30

    # -- Computed Properties --------------------------------------------

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set:
        return {ext.strip() for ext in self.allowed_extensions.split(",")}

    @property
    def effective_api_key(self) -> str:
        """Canonical API key for Gemini integrations."""
        return self.gemini_api_key

    @property
    def effective_signed_url_secret(self) -> str:
        return self.signed_url_secret or self.secret_key

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    # -- Validation ------------------------------------------------------

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    def model_post_init(self, __context) -> None:
        """Startup key validation and environment normalization."""
        legacy_google_key = os.getenv("GOOGLE_API_KEY", "").strip()

        if legacy_google_key and self.gemini_api_key:
            logger.warning(
                "Both GEMINI_API_KEY and GOOGLE_API_KEY are set; GOOGLE_API_KEY is ignored."
            )
        elif legacy_google_key:
            logger.warning(
                "GOOGLE_API_KEY is deprecated and ignored. Configure GEMINI_API_KEY instead."
            )

        if self.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = self.gemini_api_key

        # Remove legacy key from process env so SDKs do not prefer it.
        if "GOOGLE_API_KEY" in os.environ:
            os.environ.pop("GOOGLE_API_KEY", None)

        if self.is_production and not self.database_url:
            raise ValueError("DATABASE_URL must be set in production.")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton - parsed once at startup."""
    return Settings()
