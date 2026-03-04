"""
Storage repository for managing file uploads and downloads via Appwrite Storage.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from appwrite.client import Client
from appwrite.id import ID
from appwrite.input_file import InputFile
from appwrite.services.storage import Storage

from app.core.config import Settings

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for Appwrite Storage operations."""

    def __init__(self, client: Client, settings: Settings):
        self.client = client
        self.storage = Storage(client)
        self.settings = settings

    def upload_file(self, file_path: str, bucket_id: str = None) -> Optional[str]:
        """Upload a file and return its ID."""
        if not file_path or not os.path.exists(file_path):
            logger.warning("Upload failed: File does not exist: %s", file_path)
            return None

        actual_bucket = bucket_id or self.settings.storage_bucket_cvs
        try:
            result = self.storage.create_file(
                bucket_id=actual_bucket,
                file_id=ID.unique(),
                file=InputFile.from_path(file_path),
            )
            return result["$id"]
        except Exception as e:
            logger.error("Failed to upload file %s to bucket %s: %s", file_path, actual_bucket, e)
            return None

    def delete_file(self, file_id: str, bucket_id: str = None) -> bool:
        """Delete a file from storage."""
        actual_bucket = bucket_id or self.settings.storage_bucket_cvs
        try:
            self.storage.delete_file(bucket_id=actual_bucket, file_id=file_id)
            return True
        except Exception as e:
            logger.error("Failed to delete file %s from bucket %s: %s", file_id, actual_bucket, e)
            return False

    def get_file_download_url(self, file_id: str, bucket_id: str = None) -> str:
        """Get the Appwrite download URL for a file."""
        actual_bucket = bucket_id or self.settings.storage_bucket_cvs
        return f"{self.settings.appwrite_api_endpoint}/storage/buckets/{actual_bucket}/files/{file_id}/download"
