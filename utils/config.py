"""
Centralized configuration management for Job Market AI Analyzer
Uses Pydantic for validation and type safety
"""
import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model_key: str = Field(default="deepseek-chat", env="OPENROUTER_MODEL_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    openrouter_only: bool = Field(default=True, env="OPENROUTER_ONLY")
    
    # Cache Configuration
    cache_max_size_agent: int = Field(default=500, env="CACHE_MAX_SIZE_AGENT", ge=1, le=10000)
    cache_agent_ttl: int = Field(default=1800, env="CACHE_AGENT_TTL", ge=60)
    cache_job_ttl: int = Field(default=86400, env="CACHE_JOB_TTL", ge=3600)
    cache_profile_ttl: int = Field(default=3600, env="CACHE_PROFILE_TTL", ge=60)
    cache_max_size_job: int = Field(default=200, env="CACHE_MAX_SIZE_JOB", ge=1, le=1000)
    cache_max_size_profile: int = Field(default=100, env="CACHE_MAX_SIZE_PROFILE", ge=1, le=500)
    
    # Scraping Configuration
    max_jobs_per_site: int = Field(default=50, env="MAX_JOBS_PER_SITE", ge=1, le=500)
    max_search_terms: int = Field(default=5, env="MAX_SEARCH_TERMS", ge=1, le=20)
    scraping_timeout: int = Field(default=60, env="SCRAPING_TIMEOUT", ge=10, le=300)
    
    # API Configuration
    api_max_retries: int = Field(default=3, env="API_MAX_RETRIES", ge=1, le=10)
    api_retry_delay: float = Field(default=2.0, env="API_RETRY_DELAY", ge=0.1, le=60.0)
    api_timeout: int = Field(default=30, env="API_TIMEOUT", ge=5, le=300)
    
    # Application Configuration
    default_location: str = Field(default="San Francisco, CA", env="DEFAULT_LOCATION")
    default_desired_role: str = Field(default="Software Engineer", env="DEFAULT_DESIRED_ROLE")
    default_industry: str = Field(default="Technology", env="DEFAULT_INDUSTRY")
    default_experience_level: str = Field(default="Entry Level", env="DEFAULT_EXPERIENCE_LEVEL")
    career_goals_default: str = Field(
        default="I want to become a skilled software engineer and contribute to innovative projects",
        env="CAREER_GOALS_DEFAULT"
    )
    cv_file_path: Optional[str] = Field(default=None, env="CV_FILE_PATH")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level is one of the standard levels"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @validator('openrouter_only', pre=True)
    def parse_openrouter_only(cls, v):
        """Parse openrouter_only from string or boolean"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @validator('debug', pre=True)
    def parse_debug(cls, v):
        """Parse debug flag from string or boolean"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    @validator('openrouter_model_key')
    def validate_model_key(cls, v):
        """Validate OpenRouter model key format"""
        # Basic validation - full validation happens in main.py
        if not v or not isinstance(v, str):
            return "deepseek-chat"
        return v
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'  # Ignore extra environment variables


# Singleton instance - will be initialized on first import
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as e:
            # For backward compatibility, allow missing OPENROUTER_API_KEY during import
            # but it will fail when actually used
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Settings initialization failed: {e}. Some features may not work.")
            # Create a minimal settings object for import-time compatibility
            _settings = Settings(_env_file=None)  # Will fail if required fields missing
    return _settings


# Convenience accessor
settings = get_settings()

