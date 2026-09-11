"""
Minimal query-filter builder.

API-compatible with the subset of Appwrite's ``Query`` helper this codebase
used (``equal`` / ``order_desc`` / ``order_asc`` / ``limit`` / ``offset`` /
``greater_than_equal``), so repository and service call sites didn't need to
change when the storage layer moved from Appwrite to Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Filter:
    op: str
    field: Optional[str] = None
    value: Any = None


class Query:
    @staticmethod
    def equal(field: str, value: Any) -> Filter:
        return Filter("equal", field, value)

    @staticmethod
    def order_desc(field: str) -> Filter:
        return Filter("order_desc", field)

    @staticmethod
    def order_asc(field: str) -> Filter:
        return Filter("order_asc", field)

    @staticmethod
    def limit(value: int) -> Filter:
        return Filter("limit", value=value)

    @staticmethod
    def offset(value: int) -> Filter:
        return Filter("offset", value=value)

    @staticmethod
    def greater_than_equal(field: str, value: Any) -> Filter:
        return Filter("gte", field, value)
