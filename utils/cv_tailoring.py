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

    def _extract_json_from_text(self, text):
        """
        Robustly extract JSON from text, handling code blocks and raw JSON
        """
        try:
            import json
            content = text.content if hasattr(text, 'content') else str(text)
            
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content: # Generic code block
                 parts = content.split("```")
                 if len(parts) >= 2:
                    content = parts[1].strip()

            # Attempt to find JSON object structure
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                candidate = content[start:end]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass # Continue to try raw content if this fails
            
            # Try to parse the cleaned content directly
            return json.loads(content)
        except Exception as e:
            # print(f"JSON extraction failed: {e}")
            return None

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
            
            Return the response in strict JSON format with the following structure:
            {
                "cv_content": "Full markdown of the CV",
                "ats_analysis": "Brief ATS analysis",
                "ats_score": 0,
                "summary": "1-2 paragraph professional summary",
                "experience": ["Bullet points for roles/projects"],
                "projects": ["Bullet points for projects"],
                "education": ["Bullet points for education"]
            }
            """)

            # Parse the response
            # Parse the response
            parsed_result = self._extract_json_from_text(tailored_result)
            
            try:
                if not parsed_result:
                     raise ValueError("Failed to extract JSON from response")

                cv_content = (
                    parsed_result.get('cv_content')
                    or parsed_result.get('optimized_cv')
                    or parsed_result.get('cv_markdown')
                    or parsed_result.get('cv')
                )
                
                # Fallback if cv_content is still None but we parsed something
                if not cv_content:
                     # Try to use the raw content if JSON didn't contain the key
                     # This happens if the model returns just the CV text in strict mode sometimes
                     content_str = tailored_result.content if hasattr(tailored_result, 'content') else str(tailored_result)
                     if "```" not in content_str and len(content_str) > 100:
                         cv_content = content_str
                     else:
                         cv_content = "CV generation failed to produce content."

                ats_analysis = parsed_result.get('ats_analysis', "Analysis not available")
                ats_score = parsed_result.get('ats_score')
                sections = {
                    'summary': parsed_result.get('summary') or '',
                    'experience': parsed_result.get('experience') or [],
                    'projects': parsed_result.get('projects') or [],
                    'education': parsed_result.get('education') or []
                }
            except Exception as e:
                print(f"Error parsing AI response: {e}")
                # Fallback: treat the whole response as CV content if parsing fails
                cv_content = tailored_result.content if hasattr(tailored_result, 'content') else str(tailored_result)
                ats_analysis = "Parsing failed"
                ats_score = None
                sections = {'summary': '', 'experience': [], 'projects': [], 'education': []}

            # Sanitize markdown to remove artifacts
            cv_content = self._sanitize_markdown(cv_content)

            # Generate version ID
            company_name = job_posting.get('company', 'Unknown').replace(' ', '_').replace('/', '_')
            role_name = job_posting.get('title', 'Position').replace(' ', '_').replace('/', '_')
            version_id = f"{company_name}_{role_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"

            self.cv_versions[version_id] = {
                'cv_content': cv_content,
                'ats_analysis': ats_analysis,
                'ats_score': ats_score,
                'job_match_score': job_posting.get('match_score', 0),
                'job_keywords': job_keywords,
                'created_at': datetime.now(),
                'job_url': job_posting.get('url', ''),
                'job_title': job_posting.get('title', ''),
                'company': job_posting.get('company', ''),
                'template_type': template_type.lower(),
                'sections': sections
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
        
        template_type = cv_data.get('template_type', 'professional')
            
        generator = PDFGenerator()
        header = self._extract_header_info()
        sections = self._build_sections(cv_data)
        success = generator.generate_pdf(
            markdown_content=cv_data['cv_content'],
            output_path=filename,
            template_name=template_type,
            header=header,
            sections=sections
        )
        
        if success:
            return filename
        else:
            raise Exception("PDF generation failed")

    def _extract_header_info(self):
        text = self.master_cv or ''
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        name = ''
        if lines:
            first = lines[0]
            if '@' not in first and len(first.split()) <= 5:
                name = first
        import re
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        email = email_match.group(0) if email_match else ''
        phone_match = re.search(r"(\+?\d[\d\s\-]{7,}\d)", text)
        phone = phone_match.group(0) if phone_match else ''
        loc_match = None
        for l in lines[:10]:
            if l.lower().startswith('location:'):
                loc_match = l.split(':', 1)[1].strip()
                break
        location = loc_match or ''
        title = ''
        if len(lines) > 1:
            second = lines[1]
            if '@' not in second and len(second.split()) <= 6:
                title = second
        return {
            'name': name,
            'title': title,
            'email': email,
            'phone': phone,
            'location': location
        }

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

    def generate_cover_letter(self, job_posting, tailored_cv=None, output_dir='tailored_cvs'):
        """
        Create job-specific cover letter
        """
        try:
            # Use the consolidated markdown generation method
            content = self._generate_cover_letter_markdown(job_posting, tailored_cv)
            
            # Save as PDF
            company_name = job_posting.get('company', 'Unknown').replace(' ', '_').replace('/', '_')
            role_name = job_posting.get('title', 'Position').replace(' ', '_').replace('/', '_')
            version_id = f"CL_{company_name}_{role_name}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            os.makedirs(output_dir, exist_ok=True)
            pdf_path = f"{output_dir}/{version_id}.pdf"
            
            generator = PDFGenerator()
            header = self._extract_header_info()
            try:
                from datetime import datetime
                header['date'] = datetime.now().strftime('%B %d, %Y')
            except Exception:
                pass
            success = generator.generate_pdf(
                markdown_content=content,
                output_path=pdf_path,
                template_name='cover_letter',
                header=header
            )
            if success:
                return pdf_path
            # Fallback: force a simple PDF even if markdown failed
            try:
                simple_text = content.replace('\n', '\n\n')
                success2 = generator.generate_pdf(
                    markdown_content=simple_text,
                    output_path=pdf_path,
                    template_name='cover_letter',
                    header=header
                )
                if success2:
                    return pdf_path
            except Exception:
                pass
        except Exception as e:
            print(f"Error generating cover letter: {e}")
            return self._generate_cover_letter_fallback(job_posting, tailored_cv)

    def _build_sections(self, cv_data):
        skills = []
        prof = self.profile
        try:
            import json
            if isinstance(prof, str):
                parsed = json.loads(prof)
                prof = parsed
        except Exception:
            pass
        if isinstance(prof, dict):
            s = prof.get('skills')
            if isinstance(s, list):
                skills = [str(x) for x in s if str(x).strip()]
        if not skills:
            kw = cv_data.get('job_keywords') or []
            skills = [str(x) for x in kw if str(x).strip()]
        summary = ''
        if isinstance(prof, dict):
            summary = str(prof.get('career_goals') or '').strip()
        experience_html = ''
        projects_html = ''
        education_html = ''
        sections_struct = cv_data.get('sections') or {}
        try:
            import markdown as md
            def bullets_to_html(items):
                if isinstance(items, list) and items:
                    md_text = '\n'.join([f"- {str(i)}" for i in items])
                    return md.markdown(md_text)
                return ''
            experience_html = bullets_to_html(sections_struct.get('experience')) or experience_html
            projects_html = bullets_to_html(sections_struct.get('projects')) or projects_html
            education_html = bullets_to_html(sections_struct.get('education')) or education_html
            if isinstance(sections_struct.get('summary'), str) and sections_struct.get('summary').strip():
                summary = sections_struct.get('summary').strip()
        except Exception:
            pass
        try:
            import re
            import markdown as md
            content = cv_data.get('cv_content') or ''
            def section_block(title):
                pattern = rf"^##\s*{title}[\s\S]*?(?=^##\s|\Z)"
                m = re.search(pattern, content, re.MULTILINE)
                return m.group(0) if m else ''
            exp_md = section_block('PROFESSIONAL EXPERIENCE') or section_block('EXPERIENCE')
            proj_md = section_block('TECHNICAL PROJECTS') or section_block('PROJECTS')
            edu_md = section_block('EDUCATION')
            experience_html = experience_html or (md.markdown(exp_md) if exp_md else '')
            projects_html = projects_html or (md.markdown(proj_md) if proj_md else '')
            education_html = education_html or (md.markdown(edu_md) if edu_md else '')
        except Exception:
            pass
        return {
            'skills': skills,
            'summary': summary,
            'experience_html': experience_html,
            'projects_html': projects_html,
            'education_html': education_html
        }

    def _generate_cover_letter_markdown(self, job_posting, tailored_cv=None):
        try:
            company_research = self._research_company(job_posting['company'])
            cv_content = tailored_cv if tailored_cv else self.master_cv
            prompt = self._build_cover_letter_prompt(job_posting, cv_content, company_research)
            cover_letter = application_writer.run(prompt)
            content = self._extract_content(cover_letter)
            content = self._extract_content(cover_letter)
            
            parsed = self._extract_json_from_text(content)
            if parsed and isinstance(parsed, dict):
                content = parsed.get('cover_letter', content)
                
            return self._sanitize_markdown(content)
            return self._sanitize_markdown(content)
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
        - Format as Markdown with bolding for emphasis
        """

    def _extract_content(self, response):
        """
        Extract content from agent response
        """
        return response.content if hasattr(response, 'content') else str(response)

    def _sanitize_markdown(self, text: str) -> str:
        """
        Clean up common artifacts (JSON wrappers, placeholders) and ensure readable markdown.
        """
        if not text:
            return ""
        # Strip surrounding backticks/code fences
        if text.strip().startswith("```"):
            try:
                inner = text.strip().split("```", 1)[1]
                # Remove potential language tag
                inner = inner.split("\n", 1)[1] if "\n" in inner else inner
                # Remove trailing fence
                if "```" in inner:
                    inner = inner.rsplit("```", 1)[0]
                text = inner
            except Exception:
                pass
        # Remove obvious placeholder markers
        import re
        text = re.sub(r"\(placeholder\)", "", text)
        text = re.sub(r"\[placeholder\]", "", text)
        # Collapse excessive escape sequences
        text = text.replace("\\n", "\n").replace("\\t", "\t")
        # Remove leading/trailing quotes if present
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        # Ensure paragraph breaks for readability
        try:
            import re
            # Insert double newlines after sentence endings when followed by a capital letter
            text = re.sub(r"([.!?])\s+(?=[A-Z])", r"\1\n\n", text)
            # Normalize multiple blank lines
            text = re.sub(r"\n{3,}", "\n\n", text)
        except Exception:
            pass
        return text.strip()

    def _research_company(self, company_name):
        """
        Research company for personalization using knowledge base
        """
        try:
            # Fallback to basic company information for now
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

