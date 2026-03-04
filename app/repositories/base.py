"""
Base repository for Appwrite data access.
Abstracts TablesDB/Databases logic into a clean interface.
"""

from __future__ import annotations

import json
import logging
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

    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        try:
            return self.db.get_row(self.database_id, self.collection_id, document_id)
        except Exception as e:
            if "404" not in str(e):
                logger.error("Error getting document %s: %s", document_id, e)
            return None

    def list(self, queries: List[str] = None) -> List[Dict[str, Any]]:
        """List documents matching queries."""
        try:
            result = self.db.list_rows(
                self.database_id, self.collection_id, queries=queries or []
            )
            return result.get("rows", result.get("documents", []))
        except Exception as e:
            logger.error("Error listing documents: %s", e)
            return []

    def create(self, data: Dict[str, Any], document_id: str = None) -> Optional[Dict[str, Any]]:
        """Create a new document."""
        try:
            return self.db.create_row(
                self.database_id,
                self.collection_id,
                document_id=document_id or ID.unique(),
                data=data,
            )
        except Exception as e:
            logger.error("Error creating document: %s", e)
            return None

    def update(self, document_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing document."""
        try:
            return self.db.update_row(
                self.database_id, self.collection_id, document_id, data=data
            )
        except Exception as e:
            logger.error("Error updating document %s: %s", document_id, e)
            return None

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
