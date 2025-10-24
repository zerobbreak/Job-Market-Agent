"""
CV Tailoring Engine
Generate job-specific CV versions from master CV using AI optimization
"""

import os
from datetime import datetime
from .scraping import extract_job_keywords
from agents import ats_optimizer, cv_rewriter, cover_letter_agent, interview_prep_agent


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

    def generate_cover_letter(self, job_posting, tailored_cv=None):
        """
        Create job-specific cover letter
        """
        try:
            # Research company for personalization
            company_research = self._research_company(job_posting['company'])

            # Use tailored CV if available, otherwise use master CV
            cv_content = tailored_cv if tailored_cv else self.master_cv

            # Generate cover letter
            cover_letter = cover_letter_agent.run(f"""
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
            """)

            return cover_letter.content if hasattr(cover_letter, 'content') else str(cover_letter)

        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return self._generate_cover_letter_fallback(job_posting, tailored_cv)

    def _research_company(self, company_name):
        """
        Research company for personalization
        """
        try:
            # In a real implementation, this would use web search APIs
            # For now, return basic company information
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

    def generate_interview_questions(self, job_posting, tailored_cv=None):
        """
        Predict likely interview questions for a specific job application
        """
        try:
            # Use tailored CV if available, otherwise use master CV
            cv_content = tailored_cv if tailored_cv else self.master_cv

            # Generate interview questions
            questions = interview_prep_agent.run(f"""
            Generate interview questions for:
            Student Profile: {self.profile}
            CV Content: {cv_content}
            Job Posting: {job_posting}

            Make questions realistic and role-specific across these categories:
            - 5 Technical/Skills-based questions
            - 5 Behavioral questions (using STAR method)
            - 3 Company/Role-specific questions
            - 2 Background/CV questions
            - 3-5 Curveball/stress questions

            Include South African context where relevant:
            - Work authorization in South Africa
            - Transportation/reliability concerns
            - Salary expectations
            - Location preferences
            """)

            return questions.content if hasattr(questions, 'content') else str(questions)

        except Exception as e:
            print(f"Error generating interview questions: {e}")
            return self._generate_interview_questions_fallback(job_posting)

    def _generate_interview_questions_fallback(self, job_posting):
        """
        Fallback interview questions generation when API is unavailable
        """
        company = job_posting.get('company', 'Company')
        role = job_posting.get('title', 'Position')

        fallback_questions = f"""
**Predicted Interview Questions for {role} at {company}**

**Technical/Skills-Based Questions:**
1. Can you walk me through your experience with web development technologies?
2. How do you approach debugging a complex software issue?
3. Tell me about a technical project you've worked on. What challenges did you face?
4. How do you stay current with technology trends and new tools?
5. Describe your experience with version control and collaborative development.

**Behavioral Questions (STAR Method):**
6. Tell me about a time when you had to learn a new technology quickly.
7. Describe a situation where you worked effectively in a team.
8. Tell me about a time when you received constructive feedback and how you responded.
9. Describe a challenging problem you solved and the steps you took.
10. Tell me about a time when you had to meet a tight deadline.

**Company/Role-Specific Questions:**
11. What interests you most about working at {company}?
12. How do you see yourself contributing to our team dynamic?
13. What do you know about {company}'s products/services?

**Background/CV Questions:**
14. I see you worked on an Instagram clone project. Can you tell me more about the technical challenges you faced?
15. How has your Computer Science degree prepared you for this role?

**South African Context Questions:**
16. Do you have the right to work in South Africa?
17. Can you reliably commute to our office location?
18. What are your salary expectations for this role?
19. How do you handle transportation challenges in the South African context?

**Curveball/Stress Questions:**
20. If you could change one thing about your previous work experience, what would it be?
21. Where do you see yourself in 5 years?
22. What would you do if a team member wasn't pulling their weight on a project?
"""

        return fallback_questions
