"""
Storage repository — S3-compatible bucket storage (e.g. a Railway Bucket),
falling back to the local filesystem (e.g. a mounted Railway Volume) when
no bucket is configured, so local dev works without cloud credentials.

Files are keyed by a generated file id and namespaced by an optional
``bucket_id`` (kept as a subfolder/prefix for interface parity with the old
Appwrite bucket-based API). Metadata (original filename, content type,
size) is tracked in Postgres via ``FileAsset`` so downloads can restore the
original filename regardless of which backend holds the bytes.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import shutil
import tempfile
import uuid
from typing import Any, Dict, Optional

from app.core.config import Settings
from app.core.database import FileAsset, get_session

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for file storage — bucket-backed when configured, else local-volume."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._use_bucket = bool(settings.bucket_name)

        if self._use_bucket:
            import boto3
            from botocore.config import Config

            self._bucket = settings.bucket_name
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.bucket_endpoint,
                aws_access_key_id=settings.bucket_access_key_id,
                aws_secret_access_key=settings.bucket_secret_access_key,
                region_name=settings.bucket_region,
                config=Config(s3={"addressing_style": "virtual"}, signature_version="s3v4"),
            )
        else:
            os.makedirs(settings.storage_volume_path, exist_ok=True)

    def _abs_path(self, relative_path: str) -> str:
        return os.path.join(self.settings.storage_volume_path, relative_path)

    def upload_file(self, file_path: str, bucket_id: str = None) -> Optional[str]:
        """Store a local file (bucket or local volume) and return its file id."""
        if not file_path or not os.path.exists(file_path):
            logger.warning("Upload failed: File does not exist: %s", file_path)
            return None

        namespace = bucket_id or "files"
        file_id = uuid.uuid4().hex
        filename = os.path.basename(file_path)
        relative_path = f"{namespace}/{file_id}_{filename}"
        content_type, _ = mimetypes.guess_type(filename)

        try:
            if self._use_bucket:
                extra_args = {"ContentType": content_type} if content_type else None
                self._client.upload_file(file_path, self._bucket, relative_path, ExtraArgs=extra_args)
                size_bytes = os.path.getsize(file_path)
            else:
                dest_path = self._abs_path(relative_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copyfile(file_path, dest_path)
                size_bytes = os.path.getsize(dest_path)

            with get_session() as session:
                session.add(
                    FileAsset(
                        id=file_id,
                        namespace=namespace,
                        filename=filename,
                        relative_path=relative_path,
                        content_type=content_type,
                        size_bytes=size_bytes,
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

                if self._use_bucket:
                    self._client.delete_object(Bucket=self._bucket, Key=asset.relative_path)
                else:
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
        """Resolve a stored file id to a local filesystem path, if present.

        For bucket-backed storage this downloads the object to a temp file —
        callers only ever read this path, so an ephemeral local copy is fine.
        """
        with get_session() as session:
            asset = session.get(FileAsset, file_id)
            if not asset:
                return None

            if self._use_bucket:
                try:
                    suffix = os.path.splitext(asset.filename)[1]
                    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
                    os.close(fd)
                    self._client.download_file(self._bucket, asset.relative_path, tmp_path)
                    return tmp_path
                except Exception as e:
                    logger.error("Failed to download file %s from bucket: %s", file_id, e)
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
