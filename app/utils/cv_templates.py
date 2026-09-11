"""
CV Templates Module
Defines the structural templates for different CV types and provides
data-driven CV building functionality.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


class CVTemplates:
    """
    Collection of CV templates with structural definitions.
    """
    
    MODERN = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn | Portfolio]
    
    ## SUMMARY
    [Concise, impactful summary highlighting key skills and career goals]
    
    ## SKILLS
    - **Languages:** [List]
    - **Frameworks:** [List]
    - **Tools:** [List]
    - **Soft Skills:** [List]
    
    ## TECHNICAL PROJECTS
    **[Project Name]** | [Role]
    [Link if available]
    - [Impact-driven bullet point]
    - [Tech stack used]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Dates]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    - [Relevant Coursework/Honors]
    """
    
    PROFESSIONAL = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn]
    
    ## PROFESSIONAL SUMMARY
    [Formal summary of experience, leadership, and value proposition]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Location] | [Dates]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    
    ## SKILLS & CERTIFICATIONS
    - [Skill Category]: [List]
    - [Certification Name] ([Year])
    """
    
    ACADEMIC = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn | Google Scholar]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    - Thesis: [Title]
    - Advisor: [Name]
    
    ## RESEARCH EXPERIENCE
    **[Role]** | [Institution] | [Dates]
    - [Research focus and outcomes]
    
    ## PUBLICATIONS
    - [Citation format]
    
    ## TEACHING EXPERIENCE
    **[Role]** | [Institution] | [Dates]
    - [Course Name]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Dates]
    - [Description]
    
    ## SKILLS
    - [List]
    """

    @staticmethod
    def get_template(template_name):
        """Returns the requested template structure."""
        template_name = template_name.upper()
        if hasattr(CVTemplates, template_name):
            return getattr(CVTemplates, template_name)
        return CVTemplates.PROFESSIONAL  # Default


class CVBuilder:
    """
    Data-driven CV builder that creates structured CVs from parsed CV data.
    Works without AI - guarantees output using actual user data.
    """
    
    # Action verbs for enhancing bullet points
    ACTION_VERBS = [
        'Developed', 'Implemented', 'Designed', 'Created', 'Built', 'Led',
        'Managed', 'Optimized', 'Improved', 'Delivered', 'Collaborated',
        'Architected', 'Integrated', 'Deployed', 'Automated', 'Streamlined'
    ]
    
    def __init__(self, cv_data: Any = None, profile: Dict = None, job_data: Dict = None):
        """
        Initialize the CV Builder.
        
        Args:
            cv_data: Parsed CVData object from cv_parser.py
            profile: Profile dictionary with user info
            job_data: Job posting dictionary for tailoring
        """
        self.cv_data = cv_data
        self.profile = profile or {}
        self.job_data = job_data or {}
        
    def build_modern_cv(self) -> str:
        """Build a modern-style CV with sidebar emphasis on skills."""
        return self._build_cv('modern')
    
    def build_professional_cv(self) -> str:
        """Build a professional/traditional CV."""
        return self._build_cv('professional')
    
    def build_academic_cv(self) -> str:
        """Build an academic CV with education emphasis."""
        return self._build_cv('academic')
    
    def _build_cv(self, template_type: str) -> str:
        """Build CV content based on template type."""
        # Extract data from cv_data or profile
        name = self._get_name()
        contact = self._get_contact_line()
        summary = self._get_summary()
        skills_section = self._build_skills_section()
        experience_section = self._build_experience_section()
        projects_section = self._build_projects_section()
        education_section = self._build_education_section()
        
        if template_type == 'modern':
            return self._format_modern(
                name, contact, summary, skills_section, 
                projects_section, experience_section, education_section
            )
        elif template_type == 'academic':
            return self._format_academic(
                name, contact, summary, education_section,
                experience_section, projects_section, skills_section
            )
        else:  # professional
            return self._format_professional(
                name, contact, summary, experience_section,
                education_section, skills_section
            )
    
    def _get_name(self) -> str:
        """Extract name from cv_data or profile."""
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            name = self.cv_data.contact_info.name
            if name and name.lower() not in ['unknown', 'contact']:
                return name
        if self.profile:
            name = self.profile.get('name', '')
            if name and name.lower() not in ['unknown', 'unknown candidate']:
                return name
        return 'Candidate'
    
    def _get_contact_line(self) -> str:
        """Build contact info line."""
        parts = []
        
        # Email
        email = None
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            email = self.cv_data.contact_info.email
        if not email and self.profile:
            email = self.profile.get('email', '')
        if email:
            parts.append(email)
        
        # Phone
        phone = None
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            phone = self.cv_data.contact_info.phone
        if not phone and self.profile:
            phone = self.profile.get('phone', '')
        if phone:
            parts.append(phone)
        
        # Location
        location = None
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            location = self.cv_data.contact_info.address
        if not location and self.profile:
            location = self.profile.get('location', '')
        if location:
            parts.append(location)
        
        # LinkedIn
        linkedin = None
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            linkedin = self.cv_data.contact_info.linkedin
        if linkedin:
            parts.append(linkedin)
        
        # GitHub
        github = None
        if self.cv_data and hasattr(self.cv_data, 'contact_info'):
            github = self.cv_data.contact_info.github
        if github:
            parts.append(github)
            
        return ' | '.join(parts) if parts else ''
    
    def _get_summary(self) -> str:
        """Build professional summary."""
        # Try cv_data professional_profile first
        if self.cv_data and self.cv_data.professional_profile:
            return self.cv_data.professional_profile
        
        # Try profile career_goals
        if self.profile and self.profile.get('career_goals'):
            goals = self.profile.get('career_goals', '')
            if goals and 'leverage my skills' not in goals.lower():
                return goals
        
        # Build a summary from available data
        name = self._get_name()
        skills = self._get_all_skills()[:5]
        job_title = self.job_data.get('title', 'a challenging role')
        company = self.job_data.get('company', '')
        
        exp_level = self.profile.get('experience_level', 'Entry Level') if self.profile else 'Entry Level'
        
        skills_text = ', '.join(skills[:3]) if skills else 'technical expertise'
        
        if company:
            return f"{exp_level} professional with expertise in {skills_text}. Seeking {job_title} at {company} to apply my skills and contribute to innovative solutions."
        else:
            return f"{exp_level} professional with expertise in {skills_text}. Seeking to apply my skills in a challenging {job_title} role."
    
    def _get_all_skills(self) -> List[str]:
        """Get all skills from cv_data or profile."""
        skills = []
        
        # From cv_data
        if self.cv_data and self.cv_data.technical_skills:
            for category, skill_list in self.cv_data.technical_skills.items():
                if isinstance(skill_list, list):
                    skills.extend(skill_list)
        
        # From profile
        if self.profile and self.profile.get('skills'):
            profile_skills = self.profile.get('skills', [])
            if isinstance(profile_skills, list):
                skills.extend(profile_skills)
        
        # Deduplicate while preserving order
        seen = set()
        unique_skills = []
        for s in skills:
            s_clean = str(s).strip()
            if s_clean and s_clean.lower() not in seen:
                seen.add(s_clean.lower())
                unique_skills.append(s_clean)
        
        return unique_skills
    
    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into Languages, Frameworks, Tools, etc."""
        categories = {
            'Languages': [],
            'Frameworks': [],
            'Tools': [],
            'Databases': [],
            'Cloud': [],
            'Other': []
        }
        
        # Keywords for categorization
        lang_keywords = ['python', 'javascript', 'typescript', 'java', 'c#', 'c++', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'sql', 'r']
        framework_keywords = ['react', 'angular', 'vue', 'next', 'node', 'express', 'django', 'flask', 'fastapi', 'spring', '.net', 'laravel', 'rails']
        db_keywords = ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'dynamodb', 'firebase']
        cloud_keywords = ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'github actions']
        tool_keywords = ['git', 'jira', 'linux', 'bash', 'vscode', 'postman', 'figma']
        
        for skill in skills:
            skill_lower = skill.lower()
            categorized = False
            
            for kw in lang_keywords:
                if kw in skill_lower:
                    categories['Languages'].append(skill)
                    categorized = True
                    break
            if categorized:
                continue
                
            for kw in framework_keywords:
                if kw in skill_lower:
                    categories['Frameworks'].append(skill)
                    categorized = True
                    break
            if categorized:
                continue
                
            for kw in db_keywords:
                if kw in skill_lower:
                    categories['Databases'].append(skill)
                    categorized = True
                    break
            if categorized:
                continue
                
            for kw in cloud_keywords:
                if kw in skill_lower:
                    categories['Cloud'].append(skill)
                    categorized = True
                    break
            if categorized:
                continue
                
            for kw in tool_keywords:
                if kw in skill_lower:
                    categories['Tools'].append(skill)
                    categorized = True
                    break
            if categorized:
                continue
            
            categories['Other'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _build_skills_section(self) -> str:
        """Build the skills section."""
        skills = self._get_all_skills()
        if not skills:
            return ''
        
        # First try to use cv_data categorization
        if self.cv_data and self.cv_data.technical_skills:
            lines = []
            for category, skill_list in self.cv_data.technical_skills.items():
                if skill_list:
                    # Clean category name
                    cat_clean = category.strip('• ').strip()
                    if cat_clean:
                        lines.append(f"- **{cat_clean}:** {', '.join(skill_list[:10])}")
            if lines:
                return '\n'.join(lines)
        
        # Fall back to auto-categorization
        categorized = self._categorize_skills(skills)
        lines = []
        for category, skill_list in categorized.items():
            if skill_list:
                lines.append(f"- **{category}:** {', '.join(skill_list[:10])}")
        
        return '\n'.join(lines) if lines else '\n'.join([f"- {s}" for s in skills[:15]])
    
    def _build_experience_section(self) -> str:
        """Build the work experience section."""
        lines = []
        
        if self.cv_data and self.cv_data.work_experience:
            for exp in self.cv_data.work_experience[:5]:
                # Title and company
                title = exp.title if hasattr(exp, 'title') else 'Position'
                company = exp.company if hasattr(exp, 'company') else ''
                duration = exp.duration if hasattr(exp, 'duration') else ''
                
                header = f"**{title}**"
                if company:
                    header += f" | {company}"
                if duration:
                    header += f" | {duration}"
                lines.append(header)
                
                # Responsibilities
                if hasattr(exp, 'responsibilities') and exp.responsibilities:
                    for resp in exp.responsibilities[:4]:
                        if resp:
                            lines.append(f"- {resp}")
                
                lines.append('')  # Empty line between entries
        
        if not lines:
            lines.append("- Experience details available in full CV")
        
        return '\n'.join(lines)
    
    def _build_projects_section(self) -> str:
        """Build the projects section."""
        lines = []
        
        if self.cv_data and self.cv_data.projects:
            for proj in self.cv_data.projects[:4]:
                name = proj.name if hasattr(proj, 'name') else 'Project'
                desc = proj.description if hasattr(proj, 'description') else ''
                
                header = f"**{name}**"
                if desc:
                    header += f" | {desc}"
                lines.append(header)
                
                # Technologies
                if hasattr(proj, 'technologies') and proj.technologies:
                    lines.append(f"- Technologies: {', '.join(proj.technologies[:6])}")
                
                # Details
                if hasattr(proj, 'details') and proj.details:
                    for detail in proj.details[:3]:
                        if detail:
                            lines.append(f"- {detail}")
                
                lines.append('')
        
        if not lines:
            lines.append("- Project portfolio available upon request")
        
        return '\n'.join(lines)
    
    def _build_education_section(self) -> str:
        """Build the education section."""
        lines = []
        
        if self.cv_data and self.cv_data.education:
            for edu in self.cv_data.education[:3]:
                degree = edu.degree if hasattr(edu, 'degree') else ''
                institution = edu.institution if hasattr(edu, 'institution') else ''
                year = edu.year if hasattr(edu, 'year') else ''
                
                header = f"**{degree}**" if degree else "**Education**"
                if institution:
                    header += f" | {institution}"
                if year:
                    header += f" | {year}"
                lines.append(header)
                
                # Details
                if hasattr(edu, 'details') and edu.details:
                    for detail in edu.details[:2]:
                        if detail:
                            lines.append(f"- {detail}")
                
                lines.append('')
        
        # Fallback to profile
        if not lines and self.profile and self.profile.get('education'):
            edu = self.profile.get('education', '')
            if edu and edu != 'Not specified':
                lines.append(f"**{edu}**")
        
        if not lines:
            lines.append("- Education details available upon request")
        
        return '\n'.join(lines)
    
    def _format_modern(self, name, contact, summary, skills, projects, experience, education) -> str:
        """Format as modern CV."""
        return f"""# {name}
{contact}

## SUMMARY
{summary}

## SKILLS
{skills}

## TECHNICAL PROJECTS
{projects}

## PROFESSIONAL EXPERIENCE
{experience}

## EDUCATION
{education}
"""

    def _format_professional(self, name, contact, summary, experience, education, skills) -> str:
        """Format as professional CV."""
        return f"""# {name}
{contact}

## PROFESSIONAL SUMMARY
{summary}

## PROFESSIONAL EXPERIENCE
{experience}

## EDUCATION
{education}

## SKILLS & COMPETENCIES
{skills}
"""

    def _format_academic(self, name, contact, summary, education, experience, projects, skills) -> str:
        """Format as academic CV."""
        return f"""# {name}
{contact}

## ABOUT
{summary}

## EDUCATION
{education}

## RESEARCH & PROJECTS
{projects}

## PROFESSIONAL EXPERIENCE
{experience}

## SKILLS
{skills}
"""

    def build_cover_letter(self) -> str:
        """Build a cover letter using actual user data."""
        name = self._get_name()
        skills = self._get_all_skills()[:5]
        job_title = self.job_data.get('title', 'the position')
        company = self.job_data.get('company', 'your company')
        
        # Get experience highlights
        experience_highlights = []
        if self.cv_data and self.cv_data.work_experience:
            for exp in self.cv_data.work_experience[:2]:
                if hasattr(exp, 'title') and exp.title:
                    experience_highlights.append(exp.title)
        
        # Build the letter
        skills_text = ', '.join(skills[:3]) if skills else 'my technical expertise'
        exp_text = f" with experience as {' and '.join(experience_highlights)}" if experience_highlights else ""
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the **{job_title}** position at **{company}**. As a professional{exp_text}, I am excited about the opportunity to contribute to your team.

My technical background includes {skills_text}, which I have applied to deliver impactful solutions. I am particularly drawn to this role because it aligns with my career goals and allows me to leverage my strengths in a meaningful way.

Throughout my career, I have focused on delivering high-quality work while collaborating effectively with teams. I am confident that my skills and experience make me a strong candidate for this position.

I would welcome the opportunity to discuss how my background and skills would benefit {company}. Thank you for considering my application.

Sincerely,
{name}
"""

