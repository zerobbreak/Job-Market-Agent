import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import Settings
from app.services.tailoring_service import TailoringService
from app.repositories.application_repo import ApplicationRepository
from app.repositories.storage_repo import StorageRepository

logger = logging.getLogger(__name__)

class ApplicationPackageService:
    """
    Service for orchestrating the generation of application packages (tailored CV, cover letter, metadata).
    Coordinates between tailoring logic, storage, and database repositories.
    """
    
    def __init__(
        self, 
        tailoring_service: TailoringService,
        app_repo: ApplicationRepository,
        storage_repo: StorageRepository,
        settings: Settings,
        output_dir: str = "applications/packages"
    ):
        self.tailoring_service = tailoring_service
        self.app_repo = app_repo
        self.storage_repo = storage_repo
        self.settings = settings
        self.output_dir = Path(output_dir)
        if not self.output_dir.is_absolute():
            base_dir = Path(os.getcwd())
            self.output_dir = base_dir / output_dir
            
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_package(
        self, 
        user_id: str,
        job: Dict[str, Any], 
        master_cv_text: str,
        profile: Dict[str, Any],
        template_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a complete application package.
        """
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        
        try:
            # 1. Tailor CV
            logger.info(f"Tailoring CV for {job_title} at {company}")
            cv_results = await self.tailoring_service.tailor_cv(
                master_cv=master_cv_text,
                profile=profile,
                job=job,
                template_type=template_type
            )
            
            # 2. Generate Cover Letter
            logger.info(f"Generating cover letter for {job_title} at {company}")
            cl_markdown = await self.tailoring_service.generate_cover_letter(
                master_cv=master_cv_text,
                profile=profile,
                job=job,
                tailored_cv=cv_results['markdown']
            )
            
            # 3. Create local package directory for processing
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_company = "".join(x for x in company if x.isalnum() or x in " -_").strip().replace(" ", "_")
            safe_title = "".join(x for x in job_title if x.isalnum() or x in " -_").strip().replace(" ", "_")
            
            pkg_dir = self.output_dir / user_id / f"{safe_company}_{safe_title}_{timestamp}"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            
            # 4. Generate PDFs
            cv_pdf_path = pkg_dir / "cv.pdf"
            cl_pdf_path = pkg_dir / "cover_letter.pdf"
            
            # Extract header info from master CV or profile for PDF generation
            header = self._prepare_pdf_header(profile, master_cv_text)
            
            cv_success = await self.tailoring_service.create_pdf(
                markdown_content=cv_results['markdown'],
                output_path=str(cv_pdf_path),
                template=cv_results['template'],
                header=header
            )
            
            cl_success = await self.tailoring_service.create_pdf(
                markdown_content=cl_markdown,
                output_path=str(cl_pdf_path),
                template='cover_letter',
                header=header
            )
            
            # 5. Upload to Storage
            cv_storage_id = None
            if cv_success:
                cv_storage_id = self.storage_repo.upload_file(
                    file_path=str(cv_pdf_path),
                    bucket_id=self.settings.bucket_id_cvs
                )
            
            cl_storage_id = None
            if cl_success:
                cl_storage_id = self.storage_repo.upload_file(
                    file_path=str(cl_pdf_path),
                    bucket_id=self.settings.bucket_id_cvs # Assuming CLs go to same bucket or a CL bucket
                ) or self.storage_repo.upload_file(
                    file_path=str(cl_pdf_path),
                    bucket_id=getattr(self.settings, 'bucket_id_covers', self.settings.bucket_id_cvs)
                )

            # 6. Save Metadata locally (optional but kept for heritage)
            metadata = {
                "job": job,
                "ats_score": cv_results['ats_score'],
                "ats_analysis": cv_results['ats_analysis'],
                "cv_storage_id": cv_storage_id,
                "cl_storage_id": cl_storage_id,
                "timestamp": timestamp
            }
            with open(pkg_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            # 7. Record in Database
            app_id = self.app_repo.save_application(
                user_id=user_id,
                company=company,
                role=job_title,
                job_url=job.get('url', ''),
                location=job.get('location', ''),
                cv_storage_id=cv_storage_id,
                cl_storage_id=cl_storage_id,
                description=job.get('description', ''),
                match_score=job.get('match_score', 0),
                ats_score=cv_results['ats_score']
            )

            return {
                "application_id": app_id,
                "cv_storage_id": cv_storage_id,
                "cover_letter_storage_id": cl_storage_id,
                "ats_score": cv_results['ats_score'],
                "ats_analysis": cv_results['ats_analysis'],
                "local_path": str(pkg_dir)
            }

        except Exception as e:
            logger.error(f"Failed to generate application package: {e}")
            return None

    def _prepare_pdf_header(self, profile: Dict[str, Any], raw_cv: str) -> Dict[str, Any]:
        """Prepare header information for PDF generation."""
        # Preference to profile data
        header = {
            'name': profile.get('name', ''),
            'email': profile.get('email', ''),
            'phone': profile.get('phone', ''),
            'location': profile.get('location', ''),
            'title': profile.get('degree', '') or profile.get('current_role', '')
        }
        
        # Merge links
        links = profile.get('links', {})
        if isinstance(links, dict):
            for k, v in links.items():
                if v: header[k] = v
        
        return header
