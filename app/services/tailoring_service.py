import logging
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from utils.cv_tailoring import CVTailoringEngine
from utils.cv_parser import CVParser
from utils.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

class TailoringService:
    """
    Service for tailoring CVs and generating cover letters.
    Coordinates between AI agents and local generation tools.
    """
    
    def __init__(self):
        self.pdf_generator = PDFGenerator()

    def _get_engine(self, master_cv: str, profile: Dict[str, Any], parsed_cv: Any = None) -> CVTailoringEngine:
        return CVTailoringEngine(master_cv, profile, parsed_cv)

    async def tailor_cv(
        self, 
        master_cv: str, 
        profile: Dict[str, Any], 
        job: Dict[str, Any], 
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a tailored CV content and analysis.
        """
        try:
            # Parse CV if needed for the engine
            parser = CVParser(raw_text=master_cv)
            # We don't necessarily need AI parsing here if we just want rule-based extraction for the engine
            # but if it was already parsed, we should pass it.
            
            engine = self._get_engine(master_cv, profile)
            cv_markdown, ats_analysis = engine.generate_tailored_cv(job, template_type)
            
            if not engine.cv_versions:
                raise ValueError("Engine failed to generate any CV versions")
                
            version_id = list(engine.cv_versions.keys())[-1]
            version_data = engine.get_cv_version(version_id)
            
            return {
                "markdown": cv_markdown,
                "ats_analysis": ats_analysis,
                "ats_score": version_data.get("ats_score"),
                "keywords": version_data.get("job_keywords"),
                "version_id": version_id,
                "template": version_data.get("template_type", "modern")
            }
        except Exception as e:
            logger.error(f"Tailoring CV failed: {e}")
            raise

    async def generate_cover_letter(
        self, 
        master_cv: str, 
        profile: Dict[str, Any], 
        job: Dict[str, Any], 
        tailored_cv: Optional[str] = None
    ) -> str:
        """
        Generate cover letter markdown.
        """
        try:
            engine = self._get_engine(master_cv, profile)
            # Use the internal markdown generation method directly to get content
            content = engine._generate_cover_letter_markdown(job, tailored_cv)
            return content
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            raise

    async def create_pdf(
        self, 
        markdown_content: str, 
        output_path: str, 
        template: str = 'modern', 
        header: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Generate a PDF from markdown content.
        """
        try:
            return self.pdf_generator.generate_pdf(
                markdown_content=markdown_content,
                output_path=output_path,
                template_name=template,
                header=header
            )
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return False
