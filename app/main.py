"""
FastAPI application factory.

Creates and configures the FastAPI app instance with all middleware,
exception handlers, and routers.

Usage (production)::

    uvicorn app.main:app --host 0.0.0.0 --port 8000

Usage (development)::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    settings = get_settings()

    # ── Startup ──────────────────────────────────────────────────────
    setup_logging(settings)
    logger.info(
        "Starting Job Market Agent API [env=%s, port=%d]",
        settings.environment,
        settings.port,
    )

    # Ensure required directories exist
    os.makedirs(settings.upload_folder, exist_ok=True)
    os.makedirs(settings.scraper_cache_dir, exist_ok=True)
    os.makedirs("applications", exist_ok=True)

    # Start background task manager
    try:
        from services.task_manager import task_manager

        task_manager.start()
        logger.info("Task Manager started")
    except Exception as e:
        logger.warning("Failed to start Task Manager: %s", e)

    # Fix Windows Unicode
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    try:
        from services.task_manager import task_manager

        task_manager.stop()
        logger.info("Task Manager stopped")
    except Exception:
        pass

    logger.info("Job Market Agent API shut down")


def create_app() -> FastAPI:
    """Application factory — builds the FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title="Job Market Agent API",
        description="AI-powered job search, matching, and application platform",
        version="2.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Middleware
    setup_middleware(app, settings)

    # Exception handlers
    register_exception_handlers(app)

    # Rate limiting
    from app.core.limiter import limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Routers
    from app.api.v1 import v1_router

    app.include_router(v1_router)

    # Health check (root)
    @app.get("/", tags=["Health"])
    async def health_check():
        return {
            "status": "running",
            "version": "2.0.0",
            "message": "Job Market Agent API (FastAPI) is active.",
        }

    # Legacy compatibility: mount old /api/* routes that frontend might still use
    @app.get("/api/health", tags=["Health"])
    async def api_health():
        return {"status": "running"}

    return app


# Module-level app instance for Uvicorn
app = create_app()
