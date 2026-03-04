"""
CV service for tailoring CVs and generating PDFs.
"""

from __future__ import annotations

import logging
import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import Settings
from app.repositories.job_repo import JobRepository
from app.repositories.storage_repo import StorageRepository

logger = logging.getLogger(__name__)


class CVService:
    """Service for CV tailoring and PDF generation logic."""

    def __init__(
        self,
        settings: Settings,
        job_repo: JobRepository,
        storage_repo: StorageRepository,
    ):
        self.settings = settings
        self.job_repo = job_repo
        self.storage_repo = storage_repo

    async def generate_preview(
        self, 
        job_id: str, 
        user_id: str, 
        job_data: Dict[str, Any], 
        template_type: str,
        profile_data: Dict[str, Any],
        cv_text: str
    ) -> None:
        """
        Asynchronously generate CV and cover letter preview.
        This is intended to be run in a background task.
        """
        try:
            # 1. Update progress: 10%
            self.job_repo.update_progress(job_id, 10, "processing", "Initializing tailoring...")

            # 2. Tailoring logic (using existing CVTailoringEngine for now)
            from utils.cv_tailoring import CVTailoringEngine
            from utils.pdf_generator import PDFGenerator

            engine = CVTailoringEngine(cv_text, profile_data)
            
            # 3. Generate tailored content: 50%
            self.job_repo.update_progress(job_id, 50, "processing", "Tailoring content with AI...")
            cv_markdown, ats_analysis = engine.generate_tailored_cv(job_data, template_type)
            cl_markdown = engine._generate_cover_letter_markdown(job_data, tailored_cv=cv_markdown)
            
            # 4. Render HTML/PDF preview: 90%
            self.job_repo.update_progress(job_id, 90, "processing", "Rendering preview...")
            generator = PDFGenerator()
            header = engine._extract_header_info()
            
            # We don't store the full HTML in the DB usually, just the status.
            # But the legacy code returned it in the 'result' field.
            result = {
                "cv_markdown": cv_markdown,
                "cl_markdown": cl_markdown,
                "header": header,
                "ats": {"analysis": ats_analysis},
                "generated_at": datetime.now().isoformat()
            }

            # 5. Complete: 100%
            self.job_repo.update_progress(job_id, 100, "done", "Preview ready!", result=result)

        except Exception as e:
            logger.error("Error in CV preview generation for %s: %s", job_id, e)
            logger.error(traceback.format_exc())
            self.job_repo.update_progress(job_id, 0, "error", f"Generation failed: {str(e)}")

    async def get_pdf_path(self, job_id: str, doc_type: str) -> Optional[str]:
        """Generate PDF and return local file path for download."""
        state = self.job_repo.get(job_id)
        if not state or state.get("status") != "done":
            return None

        result = state.get("result", {})
        template_type = state.get("template_type", "modern")
        
        from utils.pdf_generator import PDFGenerator
        generator = PDFGenerator()
        
        import tempfile
        suffix = ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            output_path = tmp.name

        success = False
        if doc_type == "cv":
            success = generator.generate_pdf(
                result.get("cv_markdown", ""), 
                output_path, 
                template_name=template_type,
                header=result.get("header", {})
            )
        elif doc_type == "cover_letter":
            success = generator.generate_pdf(
                result.get("cl_markdown", ""), 
                output_path, 
                template_name="cover_letter",
                header=result.get("header", {})
            )

        return output_path if success else None
