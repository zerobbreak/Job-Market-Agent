"""
Postgres-backed repository base classes.

Replaces the old Appwrite ``AppwriteRepository``. Two shapes exist:

- ``PostgresRepository``: the original generic store. A collection (today
  just ``analytics``, plus any future ad-hoc collection) lives as rows in
  the shared ``documents`` table, keyed by ``(collection, id)``, with a
  JSON ``data`` column holding attributes.
- ``TypedRepository``: backs a dedicated table (profiles/jobs/matches/
  applications — see ``app.core.database``). Columns declared on the
  model are read/written directly (real, indexed, queryable in SQL);
  anything else is kept in that row's ``attrs`` JSONB column.

Both return the same flat, Appwrite-shaped dict (``$id`` / ``$createdAt`` /
``$updatedAt``) so existing service/router code (and the frontend contract)
didn't need to change when a collection moved from one shape to the other.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Type

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


class _SerializationMixin:
    """(De)serialization helpers, unchanged from the Appwrite-era contract."""

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


class PostgresRepository(_SerializationMixin):
    """Base repository for a single named collection in the `documents` table."""

    def __init__(self, collection: str):
        self.collection = collection

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


# Legacy/alternate key names the app still writes here and there (mostly
# from the Appwrite era) mapped onto the real typed column name.
_FIELD_ALIASES = {
    "userId": "user_id",
    "isActive": "is_active",
    "$createdAt": "created_at",
    "$updatedAt": "updated_at",
}

# Columns every model shares that are never treated as plain data fields.
_RESERVED_COLUMNS = {"id", "created_at", "updated_at", "attrs"}


class TypedRepository(_SerializationMixin):
    """Base repository for a dedicated typed table.

    Subclasses set ``model`` to a SQLAlchemy model with an ``id`` primary
    key, ``created_at``/``updated_at`` timestamps, and an ``attrs`` JSONB
    catch-all column. Any field written that matches a real column on the
    model goes there (so `list()` can filter/sort/paginate it in SQL);
    everything else is kept in ``attrs``. Returned dicts flatten both back
    together, Appwrite-shaped (`$id`/`$createdAt`/`$updatedAt`), so this is
    a drop-in swap for ``PostgresRepository`` at the call site.
    """

    model: Type[Any] = None

    def __init__(self) -> None:
        self._columns = set(self.model.__table__.columns.keys())

    def _alias(self, field: Optional[str]) -> Optional[str]:
        return _FIELD_ALIASES.get(field, field) if field else field

    def _row_to_doc(self, row: Any) -> Dict[str, Any]:
        doc = dict(row.attrs or {})
        for col in self._columns - _RESERVED_COLUMNS:
            doc[col] = getattr(row, col)
        doc["$id"] = row.id
        doc["$createdAt"] = row.created_at.isoformat() if row.created_at else None
        doc["$updatedAt"] = row.updated_at.isoformat() if row.updated_at else None
        doc["$permissions"] = []
        return doc

    def _split(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Split a write payload into (typed column kwargs, attrs extras)."""
        typed: Dict[str, Any] = {}
        extra: Dict[str, Any] = {}
        for key, value in data.items():
            field = self._alias(key)
            if field in _RESERVED_COLUMNS:
                continue
            if field in self._columns:
                if field == "user_id" and not value:
                    value = None
                typed[field] = value
            else:
                extra[key] = value
        return typed, extra

    # -- CRUD -----------------------------------------------------------------

    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single row by ID."""
        with get_session() as session:
            row = session.get(self.model, document_id)
            return self._row_to_doc(row) if row else None

    def list(self, queries: Optional[List[Filter]] = None) -> List[Dict[str, Any]]:
        """List rows matching queries, pushing filters/sort/paging to SQL
        wherever the field is a real column (attrs-only fields fall back to
        filtering the already-fetched page in Python, as before)."""
        filters = queries or []
        stmt = select(self.model)
        has_limit = False
        python_filters: List[Filter] = []

        for f in filters:
            if f.op == "limit":
                stmt = stmt.limit(f.value)
                has_limit = True
                continue
            if f.op == "offset":
                stmt = stmt.offset(f.value)
                continue

            field = self._alias(f.field)
            column = getattr(self.model, field, None) if field in self._columns else None
            if column is None:
                python_filters.append(f)
                continue

            if f.op == "equal":
                if isinstance(f.value, (list, tuple, set)):
                    stmt = stmt.where(column.in_(list(f.value)))
                else:
                    stmt = stmt.where(column == f.value)
            elif f.op == "gte":
                stmt = stmt.where(column >= f.value)
            elif f.op == "order_desc":
                stmt = stmt.order_by(column.desc())
            elif f.op == "order_asc":
                stmt = stmt.order_by(column.asc())

        if not has_limit:
            stmt = stmt.limit(_MAX_FETCH)

        try:
            with get_session() as session:
                rows = session.execute(stmt).scalars().all()
        except Exception as e:
            logger.error("Error listing rows in %s: %s", self.model.__tablename__, e)
            raise

        docs = [self._row_to_doc(r) for r in rows]

        for f in python_filters:
            if f.op == "equal":
                values = f.value if isinstance(f.value, (list, tuple, set)) else [f.value]
                docs = [d for d in docs if d.get(f.field) in values]
            elif f.op == "gte":
                docs = [d for d in docs if (d.get(f.field) or "") >= f.value]

        return docs

    def create(self, data: Dict[str, Any], document_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new row."""
        try:
            typed, extra = self._split(data)
            doc_id = document_id or uuid.uuid4().hex
            now = datetime.now(timezone.utc)
            with get_session() as session:
                row = self.model(id=doc_id, attrs=extra, created_at=now, updated_at=now, **typed)
                session.add(row)
                session.commit()
                session.refresh(row)
                return self._row_to_doc(row)
        except Exception as e:
            logger.error("Error creating row in %s: %s", self.model.__tablename__, e)
            raise

    def update(self, document_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing row, merging unknown fields into `attrs`."""
        try:
            typed, extra = self._split(data)
            with get_session() as session:
                row = session.get(self.model, document_id)
                if not row:
                    return None

                for key, value in typed.items():
                    setattr(row, key, value)
                if extra:
                    merged = dict(row.attrs or {})
                    merged.update(extra)
                    row.attrs = merged

                row.updated_at = datetime.now(timezone.utc)
                session.commit()
                session.refresh(row)
                return self._row_to_doc(row)
        except Exception as e:
            logger.error("Error updating row %s in %s: %s", document_id, self.model.__tablename__, e)
            raise

    def delete(self, document_id: str) -> bool:
        """Delete a row."""
        try:
            with get_session() as session:
                row = session.get(self.model, document_id)
                if not row:
                    return False
                session.delete(row)
                session.commit()
                return True
        except Exception as e:
            logger.error("Error deleting row %s: %s", document_id, e)
            return False

    def count(self, queries: Optional[List[Filter]] = None) -> int:
        """Count rows matching queries."""
        return len(self.list(queries))
