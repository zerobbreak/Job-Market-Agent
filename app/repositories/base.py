"""
Base repository for Appwrite data access.
Abstracts TablesDB/Databases logic into a clean interface.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, TypeVar

from appwrite.client import Client
from appwrite.id import ID
from appwrite.query import Query
from appwrite.services.tables_db import TablesDB

logger = logging.getLogger(__name__)

T = TypeVar("T")


class AppwriteRepository:
    """Base repository for Appwrite TablesDB operations."""

    def __init__(self, client: Client, database_id: str, collection_id: str):
        self.client = client
        self.db = TablesDB(client)
        self.database_id = database_id
        self.collection_id = collection_id
        self._allowed_fields_cache: Optional[set[str]] = None

    def _serialize(self, data: Any) -> Any:
        """Serialize complex objects for Appwrite storage."""
        if data is None:
            return None
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)

    def _deserialize(self, data: Any) -> Any:
        """Deserialize JSON strings from Appwrite."""
        if not data:
            return None
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
        return data

    def _get_allowed_fields(self) -> Optional[set[str]]:
        """Return schema column keys for this collection, if available."""
        if self._allowed_fields_cache is not None:
            return self._allowed_fields_cache

        try:
            result = self.db.list_columns(self.database_id, self.collection_id)
            columns = result.get("columns", []) if isinstance(result, dict) else []
            keys = {
                c.get("key")
                for c in columns
                if isinstance(c, dict) and c.get("key")
            }
            keys.update({"$id", "$permissions"})
            self._allowed_fields_cache = keys
            return self._allowed_fields_cache
        except Exception as e:
            error_msg = str(e).lower()
            if "missing scopes" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
                logger.debug(
                    "Could not fetch schema for %s; using runtime write fallback: %s",
                    self.collection_id,
                    e,
                )
            else:
                logger.warning(
                    "Could not fetch schema for %s; using runtime write fallback: %s",
                    self.collection_id,
                    e,
                )
            self._allowed_fields_cache = set()
            return None

    def _sanitize_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Drop unknown attributes before sending data to Appwrite."""
        if not isinstance(data, dict):
            return data

        allowed = self._get_allowed_fields()
        if not allowed:
            return data

        clean = {k: v for k, v in data.items() if k in allowed}
        dropped = [k for k in data.keys() if k not in clean]
        if dropped:
            logger.warning(
                "Dropping unknown attributes for %s: %s",
                self.collection_id,
                ", ".join(sorted(dropped)),
            )
        return clean

    def _extract_unknown_attribute(self, error: Exception) -> Optional[str]:
        """Extract unknown attribute key from Appwrite validation errors."""
        message = str(error)
        match = re.search(r'Unknown attribute:\s*"([^"]+)"', message)
        if match:
            return match.group(1)
        return None

    def _safe_write_with_unknown_attr_retry(self, write_fn, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute write and progressively drop unknown attributes if Appwrite rejects them.

        This is a runtime fallback when the current auth context cannot list table columns.
        """
        payload = dict(data)
        max_attempts = len(payload) + 1
        last_error: Optional[Exception] = None

        for _ in range(max_attempts):
            try:
                return write_fn(payload)
            except Exception as e:
                unknown_key = self._extract_unknown_attribute(e)
                if not unknown_key or unknown_key not in payload:
                    raise

                payload.pop(unknown_key, None)
                logger.warning(
                    "Retrying %s write after removing unknown attribute: %s",
                    self.collection_id,
                    unknown_key,
                )
                last_error = e

        if last_error:
            raise last_error
        raise RuntimeError("Write failed unexpectedly")

    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        try:
            return self.db.get_row(self.database_id, self.collection_id, document_id)
        except Exception as e:
            if getattr(e, "code", None) == 404 or "404" in str(e) or "could not be found" in str(e).lower():
                return None
            logger.error("Error getting document %s: %s", document_id, e)
            raise

    def list(self, queries: List[str] = None) -> List[Dict[str, Any]]:
        """List documents matching queries."""
        try:
            result = self.db.list_rows(
                self.database_id, self.collection_id, queries=queries or []
            )
            return result.get("rows", result.get("documents", []))
        except Exception as e:
            logger.error("Error listing documents in %s: %s", self.collection_id, e)
            raise

    def create(self, data: Dict[str, Any], document_id: str = None) -> Optional[Dict[str, Any]]:
        """Create a new document."""
        try:
            clean_data = self._sanitize_payload(data)

            def _write(payload: Dict[str, Any]) -> Dict[str, Any]:
                return self.db.create_row(
                    self.database_id,
                    self.collection_id,
                    row_id=document_id or ID.unique(),
                    data=payload,
                )

            return self._safe_write_with_unknown_attr_retry(_write, clean_data)
        except Exception as e:
            logger.error("Error creating document in %s: %s", self.collection_id, e)
            raise

    def update(self, document_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing document."""
        try:
            clean_data = self._sanitize_payload(data)

            def _write(payload: Dict[str, Any]) -> Dict[str, Any]:
                return self.db.update_row(
                    self.database_id, self.collection_id, document_id, data=payload
                )

            return self._safe_write_with_unknown_attr_retry(_write, clean_data)
        except Exception as e:
            logger.error("Error updating document %s in %s: %s", document_id, self.collection_id, e)
            raise

    def delete(self, document_id: str) -> bool:
        """Delete a document."""
        try:
            self.db.delete_row(self.database_id, self.collection_id, document_id)
            return True
        except Exception as e:
            logger.error("Error deleting document %s: %s", document_id, e)
            return False

    def count(self, queries: List[str] = None) -> int:
        """Count documents matching queries."""
        try:
            result = self.db.list_rows(
                self.database_id, self.collection_id, queries=queries or [], limit=1
            )
            return result.get("total", 0)
        except Exception as e:
            logger.error("Error counting documents: %s", e)
            return 0
