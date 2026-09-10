"""
Postgres-backed repository base class.

Replaces the old Appwrite ``AppwriteRepository``. Each collection (jobs,
applications, profiles, matches, analytics) is stored as rows in the shared
``documents`` table, keyed by ``(collection, id)``, with a JSON ``data``
column holding attributes — this preserves Appwrite's schemaless-document
behavior so services didn't need field-by-field migrations.

Returned dicts keep Appwrite's ``$id`` / ``$createdAt`` / ``$updatedAt`` keys
so existing service/router code (and the frontend contract) didn't need to
change.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.core.database import Document, get_session
from app.repositories.query import Filter

logger = logging.getLogger(__name__)

# Safety cap on how many rows a single `list()` pulls from Postgres before
# filtering/sorting/paginating in Python. Collections in this app are
# per-user and small in practice (one person's job-search history), so this
# is generous headroom rather than a real pagination limit.
_MAX_FETCH = 10_000


def _row_to_doc(row: Document) -> Dict[str, Any]:
    doc = dict(row.data or {})
    doc["$id"] = row.id
    doc["$createdAt"] = row.created_at.isoformat()
    doc["$updatedAt"] = row.updated_at.isoformat()
    doc["$permissions"] = []
    return doc


class PostgresRepository:
    """Base repository for a single named collection in the `documents` table."""

    def __init__(self, collection: str):
        self.collection = collection

    # -- (de)serialization, unchanged from the Appwrite-era contract --------

    def _serialize(self, data: Any) -> Any:
        """Serialize complex objects for storage."""
        if data is None:
            return None
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        return str(data)

    def _deserialize(self, data: Any) -> Any:
        """Deserialize JSON strings back into Python objects."""
        if not data:
            return None
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
        return data

    # -- CRUD -----------------------------------------------------------------

    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        with get_session() as session:
            row = session.get(Document, {"collection": self.collection, "id": document_id})
            return _row_to_doc(row) if row else None

    def list(self, queries: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """List documents matching queries."""
        filters = queries or []
        user_id_filter = next(
            (f for f in filters if f.op == "equal" and f.field == "user_id"), None
        )

        try:
            with get_session() as session:
                stmt = select(Document).where(Document.collection == self.collection)
                if user_id_filter is not None:
                    if isinstance(user_id_filter.value, (list, tuple, set)):
                        stmt = stmt.where(Document.user_id.in_(list(user_id_filter.value)))
                    else:
                        stmt = stmt.where(Document.user_id == user_id_filter.value)
                stmt = stmt.limit(_MAX_FETCH)
                rows = session.execute(stmt).scalars().all()
        except Exception as e:
            logger.error("Error listing documents in %s: %s", self.collection, e)
            raise

        docs = [_row_to_doc(r) for r in rows]

        for f in filters:
            if f.op == "equal" and f is not user_id_filter:
                values = f.value if isinstance(f.value, (list, tuple, set)) else [f.value]
                docs = [d for d in docs if d.get(f.field) in values]
            elif f.op == "gte":
                docs = [d for d in docs if (d.get(f.field) or "") >= f.value]

        order_filter = next((f for f in filters if f.op in ("order_desc", "order_asc")), None)
        if order_filter is not None:
            docs.sort(
                key=lambda d: (d.get(order_filter.field) is None, d.get(order_filter.field) or ""),
                reverse=(order_filter.op == "order_desc"),
            )

        offset_filter = next((f for f in filters if f.op == "offset"), None)
        if offset_filter is not None:
            docs = docs[offset_filter.value :]

        limit_filter = next((f for f in filters if f.op == "limit"), None)
        if limit_filter is not None:
            docs = docs[: limit_filter.value]

        return docs

    def create(self, data: Dict[str, Any], document_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new document."""
        try:
            doc_id = document_id or uuid.uuid4().hex
            user_id = data.get("user_id") or data.get("userId")
            now = datetime.now(timezone.utc)

            with get_session() as session:
                row = session.merge(
                    Document(
                        collection=self.collection,
                        id=doc_id,
                        user_id=user_id,
                        data=dict(data),
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.commit()
                return _row_to_doc(row)
        except Exception as e:
            logger.error("Error creating document in %s: %s", self.collection, e)
            raise

    def update(self, document_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing document."""
        try:
            with get_session() as session:
                row = session.get(Document, {"collection": self.collection, "id": document_id})
                if not row:
                    return None

                merged = dict(row.data or {})
                merged.update(data)
                row.data = merged

                new_user_id = data.get("user_id") or data.get("userId")
                if new_user_id:
                    row.user_id = new_user_id

                row.updated_at = datetime.now(timezone.utc)
                session.commit()
                return _row_to_doc(row)
        except Exception as e:
            logger.error("Error updating document %s in %s: %s", document_id, self.collection, e)
            raise

    def delete(self, document_id: str) -> bool:
        """Delete a document."""
        try:
            with get_session() as session:
                row = session.get(Document, {"collection": self.collection, "id": document_id})
                if not row:
                    return False
                session.delete(row)
                session.commit()
                return True
        except Exception as e:
            logger.error("Error deleting document %s: %s", document_id, e)
            return False

    def count(self, queries: Optional[List[Filter]] = None) -> int:
        """Count documents matching queries."""
        return len(self.list(queries))
