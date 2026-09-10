"""
Storage repository — local filesystem storage (e.g. a mounted Railway Volume).

Files are copied into ``settings.storage_volume_path``, namespaced by an
optional ``bucket_id`` (kept as a subfolder for interface parity with the
old bucket-based API) and keyed by a generated file id. Metadata (original
filename, content type, size) is tracked in Postgres via ``FileAsset`` so
downloads can restore the original filename.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import shutil
import uuid
from typing import Any, Dict, Optional

from app.core.config import Settings
from app.core.database import FileAsset, get_session

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for local-volume file storage."""

    def __init__(self, settings: Settings):
        self.settings = settings
        os.makedirs(settings.storage_volume_path, exist_ok=True)

    def _abs_path(self, relative_path: str) -> str:
        return os.path.join(self.settings.storage_volume_path, relative_path)

    def upload_file(self, file_path: str, bucket_id: str = None) -> Optional[str]:
        """Copy a local file into the storage volume and return its file id."""
        if not file_path or not os.path.exists(file_path):
            logger.warning("Upload failed: File does not exist: %s", file_path)
            return None

        namespace = bucket_id or "files"
        file_id = uuid.uuid4().hex
        filename = os.path.basename(file_path)
        relative_path = os.path.join(namespace, f"{file_id}_{filename}")
        dest_path = self._abs_path(relative_path)

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copyfile(file_path, dest_path)
            content_type, _ = mimetypes.guess_type(filename)

            with get_session() as session:
                session.add(
                    FileAsset(
                        id=file_id,
                        namespace=namespace,
                        filename=filename,
                        relative_path=relative_path,
                        content_type=content_type,
                        size_bytes=os.path.getsize(dest_path),
                    )
                )
                session.commit()

            return file_id
        except Exception as e:
            logger.error("Failed to store file %s in namespace %s: %s", file_path, namespace, e)
            return None

    def delete_file(self, file_id: str, bucket_id: str = None) -> bool:
        """Delete a file from storage."""
        try:
            with get_session() as session:
                asset = session.get(FileAsset, file_id)
                if not asset:
                    return False
                abs_path = self._abs_path(asset.relative_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                session.delete(asset)
                session.commit()
                return True
        except Exception as e:
            logger.error("Failed to delete file %s: %s", file_id, e)
            return False

    def get_file_path(self, file_id: str) -> Optional[str]:
        """Resolve a stored file id to its absolute path on the volume, if present."""
        with get_session() as session:
            asset = session.get(FileAsset, file_id)
            if not asset:
                return None
            abs_path = self._abs_path(asset.relative_path)
            return abs_path if os.path.exists(abs_path) else None

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Return stored metadata (filename, content type, size) for a file id."""
        with get_session() as session:
            asset = session.get(FileAsset, file_id)
            if not asset:
                return None
            return {
                "filename": asset.filename,
                "content_type": asset.content_type,
                "size": asset.size_bytes,
            }

    def get_file_download_url(self, file_id: str, bucket_id: str = None) -> str:
        """Build the app's signed-URL download path for a stored file."""
        return f"{self.settings.api_base_url}/api/v1/files/signed-url?file_id={file_id}&bucket_id={bucket_id or ''}"
