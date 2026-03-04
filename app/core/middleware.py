"""
FastAPI middleware stack.

Configures CORS, request-ID injection, and access logging.
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings

logger = logging.getLogger(__name__)


# ── Request ID middleware ─────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique ``X-Request-ID`` header to every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ── Access log middleware ─────────────────────────────────────────────────────

class AccessLogMiddleware(BaseHTTPMiddleware):
    """Log method, path, status, and duration for every request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


# ── Setup helper ──────────────────────────────────────────────────────────────

def setup_middleware(app: FastAPI, settings: Settings) -> None:
    """Register all middleware on the FastAPI app instance."""

    # CORS — must be added first so preflight responses work
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Appwrite-Project",
            "X-Appwrite-JWT",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-Request-ID",
        ],
        expose_headers=["Content-Type", "Authorization", "X-Request-ID"],
        max_age=3600,
    )

    # Custom middleware (order matters — outermost runs first)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware)
