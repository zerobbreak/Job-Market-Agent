"""
Common response/request schemas shared across all API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    """Reusable pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Pagination metadata included in list responses."""

    page: int
    limit: int
    total: int
    total_pages: int = 0

    def model_post_init(self, __context) -> None:
        if self.total_pages == 0 and self.limit > 0:
            self.total_pages = (self.total + self.limit - 1) // self.limit


# ── Standardised API Responses ────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    """Generic success response with optional message."""

    success: bool = True
    message: str = "OK"


class DataResponse(BaseModel):
    """Generic data-bearing response."""

    success: bool = True
    data: Any = None


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    success: bool = True
    data: Any = None
    meta: Optional[PaginationMeta] = None


# ── Error schemas (for documentation / OpenAPI spec) ──────────────────────────

class ErrorDetail(BaseModel):
    """Single field-level error detail."""

    field: str = ""
    message: str = ""
    type: str = ""


class ErrorResponse(BaseModel):
    """Standardised error envelope."""

    error: Dict[str, Any] = Field(
        ...,
        examples=[{
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": [{"field": "email", "message": "value is not a valid email", "type": "value_error"}],
        }],
    )
