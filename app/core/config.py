"""
Centralized application settings using Pydantic BaseSettings.

All environment variables are validated at startup. Missing required vars
cause an immediate, clear error instead of runtime surprises.

Usage:
    from app.core.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Environment ──────────────────────────────────────────────────────
    environment: str = Field(default="development", description="development | staging | production")
    debug: bool = False
    port: int = 8000

    # ── Security ─────────────────────────────────────────────────────────
    secret_key: str = Field(default="change-me-in-production")
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:8000")
    signed_url_secret: Optional[str] = None
    signed_url_expiry_seconds: int = 3600
    otp_expiry_seconds: int = 300

    # ── Appwrite ─────────────────────────────────────────────────────────
    appwrite_api_endpoint: str = Field(default="https://cloud.appwrite.io/v1")
    appwrite_project_id: str = Field(default="")
    appwrite_api_key: str = Field(default="")
    appwrite_db_id: str = Field(default="job-market-db", alias="APPWRITE_DB_ID")
    appwrite_bucket_id: str = Field(default="cv-bucket", alias="APPWRITE_BUCKET_ID")

    # Collection IDs (kept as constants, overridable via env)
    collection_id_jobs: str = "jobs"
    collection_id_applications: str = "applications"
    collection_id_profiles: str = "profiles"
    collection_id_analytics: str = "analytics"
    collection_id_matches: str = "matches"

    # ── AI / LLM ─────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    google_api_key: str = Field(default="")

    # ── Files ────────────────────────────────────────────────────────────
    upload_folder: str = Field(default="uploads")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="10 MB")
    allowed_extensions: str = "pdf,doc,docx"

    # ── Job Search Defaults ──────────────────────────────────────────────
    cv_file_path: str = "cvs/CV.pdf"
    search_query: str = "Python Developer"
    location: str = "South Africa"
    max_jobs: int = 10

    # ── Scraping & Caching ───────────────────────────────────────────────
    scraper_cache_dir: str = "job_cache"
    cache_max_age_hours: int = 24
    cache_max_size_mb: int = 100
    default_results_wanted: int = 20
    max_workers: int = 5
    api_max_retries: int = 3
    api_retry_delay: float = 2.0
    api_timeout: int = 30

    # ── Computed Properties ──────────────────────────────────────────────

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extension_set(self) -> set:
        return {ext.strip() for ext in self.allowed_extensions.split(",")}

    @property
    def effective_api_key(self) -> str:
        """Return whichever AI key is available (Gemini takes priority)."""
        return self.gemini_api_key or self.google_api_key

    @property
    def effective_signed_url_secret(self) -> str:
        return self.signed_url_secret or self.secret_key

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    # ── Validation ───────────────────────────────────────────────────────

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    # Polyfill: sync GEMINI ↔ GOOGLE API keys
    def model_post_init(self, __context) -> None:
        if self.google_api_key and not self.gemini_api_key:
            self.gemini_api_key = self.google_api_key
        elif self.gemini_api_key and not self.google_api_key:
            self.google_api_key = self.gemini_api_key
        # Also set env vars for libraries that read them directly
        if self.gemini_api_key:
            os.environ.setdefault("GEMINI_API_KEY", self.gemini_api_key)
            os.environ.setdefault("GOOGLE_API_KEY", self.gemini_api_key)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — parsed once at startup."""
    return Settings()
