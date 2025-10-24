"""
CV Tailoring Engine
Generate job-specific CV versions from master CV using AI optimization
"""

import os
from datetime import datetime
from .scraping import extract_job_keywords
from agents import ats_optimizer, cv_rewriter


class CVTailoringEngine:
    """
    Generate job-specific CV versions from master CV
    """
    def __init__(self, master_cv, student_profile):
        self.master_cv = master_cv
        self.profile = student_profile
        self.cv_versions = {}

    def generate_tailored_cv(self, job_posting):
        """
        Create customized CV for specific job application
        """
        try:
            # Extract job requirements
            job_keywords = extract_job_keywords(job_posting['description'])

            # Optimize for ATS
            ats_analysis = ats_optimizer.run(f"""
            Analyze CV ATS compatibility:
            CV: {self.master_cv}
            Job: {job_posting}
            """)

            # Rewrite content
            tailored_content = cv_rewriter.run(f"""
            Customize CV for this specific job:

            Master CV: {self.master_cv}
            Job Posting: {job_posting}
            Job Keywords: {job_keywords}
            Student Profile: {self.profile}

            Instructions:
            1. Reorder experiences by relevance to job
            2. Rewrite bullet points to include job keywords naturally
            3. Adjust professional summary to match job requirements
            4. Highlight most relevant skills
            5. Add relevant projects/coursework if needed

            Ensure ATS compatibility score improves to 85+
            """)

            # Generate version ID
            company_name = job_posting.get('company', 'Unknown').replace(' ', '_').replace('/', '_')
            role_name = job_posting.get('title', 'Position').replace(' ', '_').replace('/', '_')
            version_id = f"{company_name}_{role_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"

            self.cv_versions[version_id] = {
                'cv_content': tailored_content.content if hasattr(tailored_content, 'content') else str(tailored_content),
                'ats_analysis': ats_analysis.content if hasattr(ats_analysis, 'content') else str(ats_analysis),
                'job_match_score': job_posting.get('match_score', 0),
                'job_keywords': job_keywords,
                'created_at': datetime.now(),
                'job_url': job_posting.get('url', ''),
                'job_title': job_posting.get('title', ''),
                'company': job_posting.get('company', '')
            }

            return self.cv_versions[version_id]['cv_content'], self.cv_versions[version_id]['ats_analysis']

        except Exception as e:
            print(f"Error generating tailored CV: {e}")
            return None, f"Error: {e}"

    def get_cv_version(self, version_id):
        """
        Retrieve a specific CV version
        """
        return self.cv_versions.get(version_id)

    def list_cv_versions(self):
        """
        List all generated CV versions
        """
        return list(self.cv_versions.keys())

    def export_cv(self, version_id, format='pdf', output_dir='tailored_cvs'):
        """
        Export tailored CV in desired format
        """
        if version_id not in self.cv_versions:
            raise ValueError(f"CV version '{version_id}' not found")

        cv_data = self.cv_versions[version_id]

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        if format.lower() == 'pdf':
            # Generate professional PDF
            filename = self._create_pdf(cv_data, version_id, output_dir)
        elif format.lower() == 'docx':
            # Generate Word document
            filename = self._create_docx(cv_data, version_id, output_dir)
        elif format.lower() == 'txt':
            # Generate plain text file
            filename = self._create_txt(cv_data, version_id, output_dir)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'pdf', 'docx', or 'txt'")

        return filename

    def _create_pdf(self, cv_data, version_id, output_dir):
        """
        Create PDF version of the CV (placeholder implementation)
        """
        filename = f"{output_dir}/CV_{version_id}.pdf"

        # Placeholder for PDF generation
        # In a real implementation, you would use libraries like:
        # - reportlab
        # - fpdf
        # - weasyprint
        # - pdfkit

        try:
            # For now, create a simple text file with PDF extension
            # Replace this with actual PDF generation library
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"PDF Version - Tailored CV for {cv_data['company']} - {cv_data['job_title']}\n\n")
                f.write("=" * 80 + "\n\n")
                f.write(cv_data['cv_content'])
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Generated on: {cv_data['created_at']}\n")
                f.write(f"Job URL: {cv_data['job_url']}\n")
                f.write(f"Match Score: {cv_data['job_match_score']}\n")

            print(f"PDF placeholder created: {filename}")
            return filename

        except Exception as e:
            raise Exception(f"Failed to create PDF: {e}")

    def _create_docx(self, cv_data, version_id, output_dir):
        """
        Create DOCX version of the CV (placeholder implementation)
        """
        filename = f"{output_dir}/CV_{version_id}.docx"

        # Placeholder for DOCX generation
        # In a real implementation, you would use:
        # - python-docx
        # - docx

        try:
            # For now, create a text file with DOCX extension
            # Replace this with actual DOCX generation library
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"DOCX Version - Tailored CV for {cv_data['company']} - {cv_data['job_title']}\n\n")
                f.write("=" * 80 + "\n\n")
                f.write(cv_data['cv_content'])
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Generated on: {cv_data['created_at']}\n")
                f.write(f"Job URL: {cv_data['job_url']}\n")
                f.write(f"Match Score: {cv_data['job_match_score']}\n")

            print(f"DOCX placeholder created: {filename}")
            return filename

        except Exception as e:
            raise Exception(f"Failed to create DOCX: {e}")

    def _create_txt(self, cv_data, version_id, output_dir):
        """
        Create plain text version of the CV
        """
        filename = f"{output_dir}/CV_{version_id}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Tailored CV for {cv_data['company']} - {cv_data['job_title']}\n")
                f.write("=" * 80 + "\n\n")
                f.write(cv_data['cv_content'])
                f.write("\n\n" + "=" * 80 + "\n")
                f.write(f"Generated on: {cv_data['created_at']}\n")
                f.write(f"Job URL: {cv_data['job_url']}\n")
                f.write(f"Match Score: {cv_data['job_match_score']}\n")
                f.write(f"ATS Analysis: {cv_data['ats_analysis']}\n")

            print(f"Text file created: {filename}")
            return filename

        except Exception as e:
            raise Exception(f"Failed to create text file: {e}")

    def get_version_stats(self, version_id):
        """
        Get statistics for a specific CV version
        """
        if version_id not in self.cv_versions:
            return None

        cv_data = self.cv_versions[version_id]
        content = cv_data['cv_content']

        stats = {
            'word_count': len(content.split()),
            'character_count': len(content),
            'line_count': len(content.split('\n')),
            'created_at': cv_data['created_at'],
            'job_match_score': cv_data['job_match_score'],
            'company': cv_data['company'],
            'job_title': cv_data['job_title']
        }

        return stats

    def compare_versions(self, version_id1, version_id2):
        """
        Compare two CV versions
        """
        if version_id1 not in self.cv_versions or version_id2 not in self.cv_versions:
            return None

        cv1 = self.cv_versions[version_id1]
        cv2 = self.cv_versions[version_id2]

        comparison = {
            'version1': {
                'id': version_id1,
                'company': cv1['company'],
                'match_score': cv1['job_match_score'],
                'word_count': len(cv1['cv_content'].split())
            },
            'version2': {
                'id': version_id2,
                'company': cv2['company'],
                'match_score': cv2['job_match_score'],
                'word_count': len(cv2['cv_content'].split())
            },
            'differences': {
                'match_score_diff': cv2['job_match_score'] - cv1['job_match_score'],
                'word_count_diff': len(cv2['cv_content'].split()) - len(cv1['cv_content'].split())
            }
        }

        return comparison
