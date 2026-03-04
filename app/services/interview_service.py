import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import settings
from agents import interview_prep_agent
from utils.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

class InterviewService:
    def __init__(self, output_dir: str = "applications/interviews"):
        # Ensure output directory is absolute or relative to a known base
        self.output_dir = Path(output_dir)
        if not self.output_dir.is_absolute():
            # Default to a subfolder in the backend directory
            base_dir = Path(os.getcwd())
            self.output_dir = base_dir / output_dir
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_generator = PDFGenerator()

    async def prepare_interview(self, job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate interview preparation materials for a job.
        
        Args:
            job: Dictionary containing job details (title, company, description)
            
        Returns:
            Dictionary with paths to generated files (pdf, txt) or None if failed.
        """
        job_title = job.get('title', 'Unknown Position')
        company = job.get('company', 'Unknown Company')
        job_description = job.get('description', 'Not provided')

        try:
            # The agent.run call is typically synchronous in the current setup.
            # Using a thread pool or just calling it directly if acceptable for now.
            # In a full async production app, we'd use run_in_executor.
            response = interview_prep_agent.run(f"""
            Prepare comprehensive interview materials for this position:
            Job: {job_title}
            Company: {company}
            Description: {job_description}
            """)

            if not response or not hasattr(response, 'content') or not response.content:
                logger.error("Interview Agent returned empty response")
                return None

            # Create safe names for folders
            safe_company = "".join(x for x in company if x.isalnum() or x in " -_").strip()
            safe_title = "".join(x for x in job_title if x.isalnum() or x in " -_").strip()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            job_folder_name = f"{safe_company}_{safe_title}_{timestamp}".replace(" ", "_")
            job_dir = self.output_dir / job_folder_name
            job_dir.mkdir(parents=True, exist_ok=True)

            results = {}

            # Save as text fallback first
            txt_path = job_dir / 'interview_prep.txt'
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(response.content)
            results['txt'] = str(txt_path)

            # Generate PDF
            pdf_path = job_dir / 'interview_prep.pdf'
            header = {
                'title': f"Interview Prep: {job_title}",
                'company': company,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
            try:
                success = self.pdf_generator.generate_pdf(
                    markdown_content=response.content,
                    output_path=str(pdf_path),
                    template_name='modern',
                    header=header
                )
                if success:
                    results['pdf'] = str(pdf_path)
            except Exception as pdf_error:
                logger.warning(f"PDF generation failed for interview prep: {pdf_error}")

            return results

        except Exception as e:
            logger.error(f"Error preparing interview materials: {e}")
            return None
