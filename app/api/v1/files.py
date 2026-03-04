"""
Files router — signed URL generation and secure file downloads.

Ported from: routes/file_routes.py
"""

from __future__ import annotations

import logging
import os
import tempfile

import requests as _req
from appwrite.client import Client
from appwrite.services.storage import Storage
from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser
from app.core.exceptions import BadRequestError, ExternalServiceError, ForbiddenError, NotFoundError
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/files", tags=["Files"])
logger = logging.getLogger(__name__)


# ── Signed URL generation ─────────────────────────────────────────────────────

@router.post("/signed-url")
async def generate_signed_url(
    file_id: str,
    user: CurrentUser,
    bucket_id: str = "",
    file_type: str = "storage",
):
    """Generate a signed download URL for a file."""
    from utils.signed_urls import generate_signed_url as _generate

    url = _generate(file_id, bucket_id, file_type)
    return {"success": True, "url": url}


@router.get("/signed-url")
async def generate_signed_url_get(
    user: CurrentUser,
    file_id: str = Query(...),
    bucket_id: str = Query(default=""),
    file_type: str = Query(default="storage"),
):
    """Generate a signed download URL (GET variant)."""
    from utils.signed_urls import generate_signed_url as _generate

    url = _generate(file_id, bucket_id, file_type)
    return {"success": True, "url": url}


# ── Public signed download (no auth required) ────────────────────────────────

@router.get("/download-signed")
async def download_signed(
    file_id: str = Query(...),
    file_type: str = Query(...),
    expires: str = Query(...),
    signature: str = Query(...),
    bucket_id: str = Query(default=""),
    settings: Settings = Depends(get_settings),
):
    """Download a file using a signed URL (public, no auth required)."""
    from utils.signed_urls import validate_signed_url

    if not validate_signed_url(file_id, bucket_id, file_type, int(expires), signature):
        raise ForbiddenError("Invalid or expired signature")

    if file_type == "storage":
        return _download_storage_file(file_id, bucket_id, settings)
    elif file_type in ("preview_cv", "preview_cover_letter"):
        doc_type = "cv" if file_type == "preview_cv" else "cover_letter"
        return _download_preview_file(file_id, doc_type)
    else:
        raise BadRequestError("Invalid file_type")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _download_storage_file(file_id: str, bucket_id: str, settings: Settings):
    """Stream a file from Appwrite Storage."""
    try:
        client = Client()
        client.set_endpoint(settings.appwrite_api_endpoint)
        client.set_project(settings.appwrite_project_id)
        client.set_key(settings.appwrite_api_key)

        storage = Storage(client)
        file_info = storage.get_file(bucket_id, file_id)
        filename = file_info.get("name", "download")

        url = f"{settings.appwrite_api_endpoint}/storage/buckets/{bucket_id}/files/{file_id}/download"
        headers = {
            "X-Appwrite-Project": settings.appwrite_project_id,
            "X-Appwrite-Key": settings.appwrite_api_key,
        }

        r = _req.get(url, headers=headers, stream=True)
        if r.status_code != 200:
            raise ExternalServiceError("Appwrite Storage", f"HTTP {r.status_code}")

        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

        return StreamingResponse(
            generate(),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/octet-stream",
            },
        )
    except ExternalServiceError:
        raise
    except Exception as e:
        raise ExternalServiceError("Appwrite Storage", str(e))


def _download_preview_file(job_id: str, doc_type: str):
    """Generate and return a preview PDF from job state."""
    from services.job_store import load_job_state
    from utils.pdf_generator import PDFGenerator

    job_info = load_job_state(job_id)
    if not job_info:
        raise NotFoundError("Job preview")

    if job_info.get("status") != "done":
        raise BadRequestError("Preview not ready yet")

    result = job_info.get("result", {})
    template_type = job_info.get("template_type", "modern")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        output_path = tmp.name

    generator = PDFGenerator()
    markdown_content = result.get("cv_markdown" if doc_type == "cv" else "cl_markdown", "")
    header = result.get("header", {})
    sections = result.get("sections", {}) if doc_type == "cv" else {}

    template = template_type if doc_type == "cv" else "cover_letter"
    success = generator.generate_pdf(
        markdown_content, output_path, template_name=template, header=header, sections=sections
    )

    if success:
        return FileResponse(output_path, filename=f"{doc_type}.pdf", media_type="application/pdf")

    raise ExternalServiceError("PDF Generator", "PDF generation failed")


@router.get("/signed-url-test")
async def test_signed_url(user: CurrentUser):
    """Simple test endpoint for developers."""
    return {"message": "Signed URL system active"}
