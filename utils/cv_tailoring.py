"""
CV Tailoring Engine
Generate job-specific CV versions from master CV using AI optimization
"""

import os
from datetime import datetime
from .scraping import extract_job_keywords
from agents import application_writer
from .cv_templates import CVTemplates
from .pdf_generator import PDFGenerator

class CVTailoringEngine:
    """
    Generate job-specific CV versions from master CV
    """
    def __init__(self, master_cv, student_profile):
        """
        Initialize the CV Tailoring Engine

        Args:
            master_cv (str): The original CV content
            student_profile (dict): Student profile information
        """
        self.master_cv = master_cv
        self.profile = student_profile
        self.cv_versions = {}

    def generate_tailored_cv(self, job_posting, template_type=None):
        """
        Create customized CV for specific job application
        """
        try:
            # Extract job requirements
            job_description = job_posting.get('description', '')
            if not job_description:
                print("⚠️ No job description available for CV tailoring")
                job_description = f"{job_posting.get('title', 'Position')} at {job_posting.get('company', 'Company')}"

            job_keywords = extract_job_keywords(job_description)
            
            # Determine template if not provided
            if not template_type:
                title = job_posting.get('title', '').lower()
                if any(x in title for x in ['developer', 'engineer', 'programmer', 'data', 'tech', 'software']):
                    template_type = 'MODERN'
                elif any(x in title for x in ['professor', 'researcher', 'lecturer', 'academic', 'scientist']):
                    template_type = 'ACADEMIC'
                else:
                    template_type = 'PROFESSIONAL'
            
            selected_template = CVTemplates.get_template(template_type)

            # Use consolidated application_writer for both ATS optimization and CV rewriting
            tailored_result = application_writer.run(f"""
            Create an optimized CV package for this job using the specified structure.
            
            Master CV: {self.master_cv}
            Job Posting: {job_posting}
            Job Keywords: {job_keywords}
            Student Profile: {self.profile}
            
            REQUIRED STRUCTURE (Follow this strictly):
            {selected_template}

            Instructions:
            1. Optimize for ATS compatibility (score 85+)
            2. Reorder experiences by relevance to job
            3. Rewrite bullet points to include job keywords naturally
            4. Adjust professional summary to match job requirements
            5. Highlight most relevant skills
            6. Add relevant projects/coursework if needed
            
            Return both the optimized CV and ATS analysis.
            """)

            # Generate version ID
            company_name = job_posting.get('company', 'Unknown').replace(' ', '_').replace('/', '_')
            role_name = job_posting.get('title', 'Position').replace(' ', '_').replace('/', '_')
            version_id = f"{company_name}_{role_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"

            self.cv_versions[version_id] = {
                'cv_content': tailored_result.content if hasattr(tailored_result, 'content') else str(tailored_result),
                'ats_analysis': tailored_result.content if hasattr(tailored_result, 'content') else str(tailored_result),
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

        format_methods = {
            'pdf': self._create_pdf,
            'docx': self._create_docx,
            'txt': self._create_txt
        }

        if format.lower() not in format_methods:
            raise ValueError(f"Unsupported format: {format}. Use 'pdf', 'docx', or 'txt'")

        filename = format_methods[format.lower()](cv_data, version_id, output_dir)
        return filename

    def _create_cv_content(self, cv_data, format_name):
        """
        Generate formatted CV content for export
        """
        header = f"{format_name.upper()} Version - Tailored CV for {cv_data['company']} - {cv_data['job_title']}\n\n"
        separator = "=" * 80 + "\n\n"

        content_parts = [
            header,
            separator,
            cv_data['cv_content'],
            "\n\n" + separator,
            f"Generated on: {cv_data['created_at']}\n",
            f"Job URL: {cv_data['job_url']}\n",
            f"Match Score: {cv_data['job_match_score']}\n"
        ]

        # Add ATS analysis for text format only
        if format_name.lower() == 'txt':
            content_parts.append(f"ATS Analysis: {cv_data['ats_analysis']}\n")

        return ''.join(content_parts)

    def _create_file(self, cv_data, version_id, output_dir, extension, format_name):
        """
        Create a CV file with the specified extension
        """
        filename = f"{output_dir}/CV_{version_id}.{extension}"

        try:
            content = self._create_cv_content(cv_data, format_name)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"{format_name.upper()} file created: {filename}")
            return filename

        except Exception as e:
            raise Exception(f"Failed to create {format_name.upper()}: {e}")

    def _create_pdf(self, cv_data, version_id, output_dir):
        """
        Create PDF version of the CV using PDFGenerator
        """
        filename = f"{output_dir}/CV_{version_id}.pdf"
        
        # Determine template based on what was used for generation
        # We stored 'job_title' which we can use to infer, or we can store the template type in cv_data
        # For now, let's re-infer or default to professional if unknown
        # Ideally, generate_tailored_cv should store the template_type used.
        
        # Let's try to infer from the content or just use a default mapping logic again
        # Or better, let's update generate_tailored_cv to store 'template_type' in cv_data
        # But for now, let's just use a heuristic or default.
        
        template_type = 'professional' # Default
        title = cv_data.get('job_title', '').lower()
        if any(x in title for x in ['developer', 'engineer', 'programmer', 'data', 'tech', 'software']):
            template_type = 'modern'
        elif any(x in title for x in ['professor', 'researcher', 'lecturer', 'academic', 'scientist']):
            template_type = 'academic'
            
        generator = PDFGenerator()
        success = generator.generate_pdf(
            markdown_content=cv_data['cv_content'],
            output_path=filename,
            template_name=template_type
        )
        
        if success:
            return filename
        else:
            raise Exception("PDF generation failed")

    def _create_docx(self, cv_data, version_id, output_dir):
        """
        Create DOCX version of the CV (placeholder implementation)
        """
        # Placeholder for DOCX generation
        # In a real implementation, you would use python-docx
        return self._create_file(cv_data, version_id, output_dir, 'docx', 'DOCX')

    def _create_txt(self, cv_data, version_id, output_dir):
        """
        Create plain text version of the CV
        """
        return self._create_file(cv_data, version_id, output_dir, 'txt', 'Text')

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

    def generate_cover_letter(self, job_posting, tailored_cv=None):
        """
        Create job-specific cover letter
        """
        try:
            company_research = self._research_company(job_posting['company'])
            cv_content = tailored_cv if tailored_cv else self.master_cv
            prompt = self._build_cover_letter_prompt(job_posting, cv_content, company_research)

            cover_letter = application_writer.run(prompt)
            return self._extract_content(cover_letter)

        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return self._generate_cover_letter_fallback(job_posting, tailored_cv)

    def _build_cover_letter_prompt(self, job_posting, cv_content, company_research):
        """
        Build the prompt for cover letter generation
        """
        return f"""
        Create cover letter for:

        Student Profile: {self.profile}
        CV Content: {cv_content}
        Job Posting: {job_posting}
        Company Research: {company_research}

        Ensure letter is:
        - Tailored to specific role and company
        - Highlights 2-3 strongest qualifications
        - Shows genuine interest and cultural fit
        - Professional yet authentic voice
        - 250-400 words
        - Uses STAR method for examples
        """

    def _extract_content(self, response):
        """
        Extract content from agent response
        """
        return response.content if hasattr(response, 'content') else str(response)

    def _research_company(self, company_name):
        """
        Research company for personalization using knowledge base
        """
        try:
            # Try to get company information from knowledge base first
            from . import knowledge_base

            # Search for company-specific information
            company_info = knowledge_base.retrieve_context(
                f"{company_name} company information mission values culture",
                sources=['sa_context', 'job_descriptions'],
                n_results=2
            )

            # Extract relevant company details
            company_details = []
            for source, results in company_info.items():
                # Handle both old and new knowledge base formats
                documents = []
                if 'results' in results:
                    # New simplified KB format
                    documents = [doc['text'] for doc in results['results']]
                elif 'documents' in results:
                    # Old ChromaDB format
                    documents = results['documents']

                for doc in documents:
                    if company_name.lower() in doc.lower():
                        company_details.append(doc[:300])  # First 300 chars

            if company_details:
                return f"""
                Company: {company_name}
                Research Findings: {' '.join(company_details[:2])}
                """
            else:
                # Fallback to basic information
                return f"""
                Company: {company_name}
                Mission: Technology innovation and customer success
                Values: Innovation, collaboration, excellence
                Recent Focus: Digital transformation and AI solutions
                Culture: Dynamic, fast-paced, employee-focused
                """

        except Exception as e:
            print(f"Error researching company: {e}")
            return f"Company: {company_name} - Technology company focused on innovation"

    def _generate_cover_letter_fallback(self, job_posting, tailored_cv=None):
        """
        Fallback cover letter generation when API is unavailable
        """
        cv_content = tailored_cv if tailored_cv else self.master_cv
        company = job_posting.get('company', 'Company')
        role = job_posting.get('title', 'Position')

        fallback_letter = f"""
Dear Hiring Manager,

I am writing to express my strong interest in the {role} position at {company}. As a dedicated technology professional with a passion for innovation, I am excited about the opportunity to contribute to your team's success.

With my background in software development and experience in modern web technologies, I am confident in my ability to make meaningful contributions to {company}'s projects. My technical skills in programming languages, database management, and agile development methodologies align well with the requirements of this role.

I am particularly drawn to {company} because of your commitment to technological excellence and innovative solutions. I would welcome the opportunity to discuss how my skills and enthusiasm can contribute to your continued success.

Thank you for considering my application. I look forward to the possibility of speaking with you about this exciting opportunity.

Best regards,
{self.profile.get('name', 'Applicant')}
"""

        return fallback_letter

