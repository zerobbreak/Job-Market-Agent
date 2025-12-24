"""
CV Parser - Rule-based text extraction from PDF resumes
Extracts structured information using pattern matching and section identification
"""

import re
import pdfplumber
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
import json
import os

@dataclass
class ContactInfo:
    """Contact information structure"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    github: Optional[str] = None


@dataclass
class Education:
    """Education entry structure"""
    degree: str
    institution: str
    year: Optional[str] = None
    details: List[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


@dataclass
class WorkExperience:
    """Work experience entry structure"""
    title: str
    company: str
    duration: Optional[str] = None
    responsibilities: List[str] = None
    
    def __post_init__(self):
        if self.responsibilities is None:
            self.responsibilities = []


@dataclass
class Project:
    """Project entry structure"""
    name: str
    description: str
    technologies: List[str] = None
    details: List[str] = None
    
    def __post_init__(self):
        if self.technologies is None:
            self.technologies = []
        if self.details is None:
            self.details = []


@dataclass
class CVData:
    """Complete CV data structure"""
    contact_info: ContactInfo
    professional_profile: Optional[str] = None
    technical_skills: Dict[str, List[str]] = None
    education: List[Education] = None
    work_experience: List[WorkExperience] = None
    projects: List[Project] = None
    raw_text: str = ""
    
    def __post_init__(self):
        if self.technical_skills is None:
            self.technical_skills = {}
        if self.education is None:
            self.education = []
        if self.work_experience is None:
            self.work_experience = []
        if self.projects is None:
            self.projects = []


class CVParser:
    """Rule-based CV parser"""
    
    # Common section headers in CVs
    SECTION_PATTERNS = {
        'contact': r'(?i).*(contact|personal|details|information).*',
        'profile': r'(?i).*(professional\s+profile|profile|summary|objective|about\s+me).*',
        'skills': r'(?i).*(technical\s+skills|skills|core\s+competencies|expertise|tools|technologies).*',
        'education': r'(?i).*(education|academic|qualifications|studies).*',
        'experience': r'(?i).*(work\s+experience|experience|employment|professional\s+experience|history).*',
        'projects': r'(?i).*(projects|key\s+projects|portfolio).*',
    }
    
    CONTACT_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(?:\+?27|0)[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{4}|\d{10}|\+\d{1,3}[\s\-]?\d{2,4}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?',
        'github': r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?',
        'portfolio': r'(?:https?://)?[\w\-]+\.(?:vercel\.app|netlify\.app|herokuapp\.com|github\.io)[\w\-/]*',
        'url': r'https?://[^\s]+',
    }
    
    # Headers that should NOT be treated as names
    SKIP_AS_NAME = [
        'contact', 'personal', 'details', 'information', 'resume', 'cv', 
        'curriculum vitae', 'profile', 'summary', 'about', 'email', 'phone',
        'address', 'location', 'skills', 'experience', 'education', 'name'
    ]
    
    # Common technical skills for fallback extraction
    COMMON_SKILLS = [
        # Programming Languages
        'python', 'javascript', 'typescript', 'java', 'c#', 'c++', 'c', 'go', 'golang',
        'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl',
        # Frontend
        'react', 'react.js', 'reactjs', 'angular', 'vue', 'vue.js', 'vuejs', 'svelte',
        'next.js', 'nextjs', 'nuxt', 'gatsby', 'html', 'html5', 'css', 'css3', 
        'sass', 'scss', 'less', 'tailwind', 'tailwindcss', 'bootstrap', 'material-ui',
        # Backend
        'node.js', 'nodejs', 'express', 'express.js', 'fastapi', 'django', 'flask',
        'spring', 'spring boot', '.net', 'asp.net', 'laravel', 'rails', 'ruby on rails',
        # Databases
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
        'dynamodb', 'sqlite', 'oracle', 'ms sql', 'mssql', 'firebase', 'supabase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
        'terraform', 'jenkins', 'ci/cd', 'github actions', 'gitlab', 'linux',
        # Tools & Other
        'git', 'github', 'jira', 'agile', 'scrum', 'rest', 'restful', 'graphql',
        'api', 'microservices', 'machine learning', 'ml', 'ai', 'data science',
        'pandas', 'numpy', 'tensorflow', 'pytorch', 'selenium', 'cypress',
        'react native', 'flutter', 'ionic', 'electron', 'unity', 'unreal'
    ]
    
    def __init__(self, file_path: str = None, raw_text: str = None):
        """Initialize parser with PDF path or raw text"""
        self.file_path = file_path
        self.raw_text = raw_text or ""
        self.lines = []
        if self.raw_text:
             self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
    
    def _sanitize_pdf_text(self, text: str) -> str:
        """Clean up common PDF extraction artifacts"""
        if not text:
            return ""
        
        # Remove (cid:XXX) patterns (PDF ligatures/special chars) - replace with bullet or space
        text = re.sub(r'\(cid:\d+\)', ' • ', text)
        
        # Fix concatenated words: add space before capital letters that follow lowercase
        # e.g., "MongoDBCSS3React.js" -> "MongoDB CSS3 React.js"
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Fix concatenated words with dots: "Storage.MongoDB" -> "Storage, MongoDB"
        text = re.sub(r'\.([A-Z])', r', \1', text)
        
        # Fix concatenated words with closing paren: "Apps)Azure" -> "Apps, Azure"
        text = re.sub(r'\)([A-Z])', r'), \1', text)
        
        # Remove excessive dots and clean up
        text = re.sub(r'\.{2,}', '.', text)
        
        # Clean up multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up multiple bullets
        text = re.sub(r'(• ){2,}', '• ', text)
        
        return text.strip()
    
    def _split_concatenated_skills(self, skill_text: str) -> List[str]:
        """Split concatenated skill strings into individual skills"""
        # First sanitize
        skill_text = self._sanitize_pdf_text(skill_text)
        
        # Split by common delimiters
        skills = re.split(r'[,;•|/]|\s{2,}', skill_text)
        
        # Clean and filter
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip(' .-:()')
            # Skip empty, too short, or generic entries
            if skill and len(skill) > 1 and skill.lower() not in ['and', 'or', 'the', 'a', 'an']:
                cleaned_skills.append(skill)
        
        return cleaned_skills
        
    def extract_text(self) -> str:
        """Extract text from PDF preserving structure, or return provided raw text"""
        if self.raw_text and not self.file_path:
            # Sanitize provided raw text too
            self.raw_text = self._sanitize_pdf_text(self.raw_text)
            self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
            return self.raw_text

        if self.file_path and self.file_path.lower().endswith('.pdf'):
            text_parts = []
            try:
                with pdfplumber.open(self.file_path) as pdf:
                    for page in pdf.pages:
                        # Extract text with layout preservation
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                self.raw_text = "\n".join(text_parts)
            except Exception as e:
                print(f"pdfplumber extraction failed: {e}")
                # Fallback handled by caller or kept empty if raw_text was provided
        
        # Sanitize the extracted text
        self.raw_text = self._sanitize_pdf_text(self.raw_text)
        
        self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
        return self.raw_text
    
    
    def extract_contact_info(self) -> ContactInfo:
        """Extract contact information from the beginning of CV"""
        contact = ContactInfo()
        
        # Search first 30 lines for contact info
        search_text = "\n".join(self.lines[:30])
        
        # Extract email first (needed for name fallback)
        email_match = re.search(self.CONTACT_PATTERNS['email'], search_text)
        if email_match:
            contact.email = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(self.CONTACT_PATTERNS['phone'], search_text)
        if phone_match:
            contact.phone = phone_match.group(0)
        
        # Extract LinkedIn
        linkedin_match = re.search(self.CONTACT_PATTERNS['linkedin'], search_text)
        if linkedin_match:
            contact.linkedin = linkedin_match.group(0)
        
        # Extract GitHub
        github_match = re.search(self.CONTACT_PATTERNS['github'], search_text)
        if github_match:
            contact.github = github_match.group(0)
        
        # Extract portfolio
        portfolio_match = re.search(self.CONTACT_PATTERNS['portfolio'], search_text)
        if portfolio_match:
            contact.portfolio = portfolio_match.group(0)
        
        # Extract address (look for common patterns)
        for line in self.lines[:15]:
            if any(keyword in line.lower() for keyword in ['address:', 'location:']):
                contact.address = line.split(':', 1)[1].strip() if ':' in line else line
                break
            # Look for city/area names
            elif re.search(r'\b(?:johannesburg|pretoria|cape town|durban|midrand|sandton|london|new york|berlin|remote)\b', line, re.I):
                if not any(x in line.lower() for x in ['phone', 'email', 'http', '.com']):
                    contact.address = line
                    break
        
        # Name extraction - more sophisticated approach
        contact.name = self._extract_name()
        
        return contact
    
    def _extract_name(self) -> str:
        """Extract name using multiple strategies"""
        # Strategy 1: Look for the first line that looks like a name
        # (not a section header, not an email, not a phone, etc.)
        for i, line in enumerate(self.lines[:15]):
            line_lower = line.lower().strip()
            
            # Skip if it's a common section header
            if any(header in line_lower for header in self.SKIP_AS_NAME):
                continue
            
            # Skip if it contains email, phone, or URL patterns
            if re.search(self.CONTACT_PATTERNS['email'], line):
                continue
            if re.search(self.CONTACT_PATTERNS['phone'], line):
                continue
            if re.search(r'https?://', line):
                continue
            if re.search(r'linkedin|github|www\.', line, re.I):
                continue
            
            # Skip if it looks like an address (contains numbers with other chars)
            if re.search(r'\d+.*(?:street|road|avenue|drive|st\.|rd\.)|\b\d{4,}\b', line, re.I):
                continue
            
            # Skip if it looks like a location (contains city names)
            if re.search(r'\b(?:johannesburg|pretoria|cape town|durban|midrand|sandton|london|new york|berlin|remote|noordwyk|centurion|randburg|soweto|kempton)\b', line, re.I):
                continue
            
            # Check if it looks like a name (2-5 words, mostly letters)
            words = line.split()
            if 1 <= len(words) <= 5:
                # Name words should be mostly alphabetic
                alpha_words = sum(1 for w in words if re.match(r'^[A-Za-z\-\'\.]+$', w))
                if alpha_words >= len(words) * 0.5:
                    # Capitalize each word properly
                    name_parts = []
                    for w in words:
                        if w.isupper() or w.islower():
                            name_parts.append(w.title())
                        else:
                            name_parts.append(w)
                    return ' '.join(name_parts)
        
        # Strategy 2: Extract from email prefix
        search_text = "\n".join(self.lines[:30])
        email_match = re.search(self.CONTACT_PATTERNS['email'], search_text)
        if email_match:
            email = email_match.group(0)
            prefix = email.split('@')[0]
            # Clean the prefix
            prefix = re.sub(r'[\d_\-\.]+', ' ', prefix)
            words = prefix.split()
            if words:
                return ' '.join(w.title() for w in words)
        
        # Strategy 3: Fallback - just return first non-empty line
        if self.lines:
            return self.lines[0]
        
        return "Unknown"

    def find_section_boundaries(self) -> Dict[str, tuple]:
        """Identify section headers and their boundaries"""
        sections = {}
        current_section = None
        section_start = 0
        
        for i, line in enumerate(self.lines):
            # Check if line matches any section pattern
            # Heuristic: Section headers are usually short and distinct
            if len(line) < 50: 
                for section_name, pattern in self.SECTION_PATTERNS.items():
                    if re.match(pattern, line.strip()):
                        # Save previous section if exists
                        if current_section:
                            sections[current_section] = (section_start, i)
                        
                        current_section = section_name
                        section_start = i + 1
                        break
        
        # Add last section
        if current_section:
            sections[current_section] = (section_start, len(self.lines))
        
        return sections

    def extract_profile(self, sections: Dict[str, tuple]) -> Optional[str]:
        """Extract professional profile/summary"""
        if 'profile' not in sections:
            return None
        
        start, end = sections['profile']
        profile_lines = []
        
        for line in self.lines[start:end]:
            # Stop at next section or bullet points
            if re.match(r'^[A-Z\s]{3,}$', line) and len(line) < 40 and " " not in line.strip():  
                 pass

            profile_lines.append(line)
        
        return " ".join(profile_lines).strip()

    def extract_skills(self, sections: Dict[str, tuple]) -> Dict[str, List[str]]:
        """Extract technical skills organized by category"""
        skills = {}
        
        if 'skills' in sections:
            start, end = sections['skills']
            current_category = "General"
            
            for line in self.lines[start:end]:
                # Clean the line first
                line = self._sanitize_pdf_text(line)
                
                if ':' in line:
                    parts = line.split(':', 1)
                    category = parts[0].strip()
                    skill_list = parts[1].strip()
                    
                    # Use the helper to split concatenated skills
                    parsed_skills = self._split_concatenated_skills(skill_list)
                    if parsed_skills:
                        skills[category] = parsed_skills
                        current_category = category
                
                elif current_category and line and not re.match(r'^[A-Z\s]{3,}$', line):
                    # Split and clean additional skills
                    parsed_skills = self._split_concatenated_skills(line)
                    if parsed_skills:
                        if current_category not in skills:
                            skills[current_category] = []
                        skills[current_category].extend(parsed_skills)
        
        # Fallback: If no skills found or very few, scan entire document for known skills
        all_skills = []
        for cat_skills in skills.values():
            all_skills.extend(cat_skills)
        
        if len(all_skills) < 3:
            # Scan entire document for common tech skills
            fallback_skills = self._extract_skills_fallback()
            if fallback_skills:
                skills['Detected Skills'] = fallback_skills
        
        # Clean up any remaining corruption in skill names
        cleaned_skills = {}
        for category, skill_list in skills.items():
            cleaned = []
            for skill in skill_list:
                # Skip corrupted entries
                if not skill or len(skill) < 2:
                    continue
                if skill.startswith('•') or skill.startswith('('):
                    skill = skill.lstrip('•( ').strip()
                if skill and len(skill) >= 2:
                    cleaned.append(skill)
            if cleaned:
                cleaned_skills[category] = list(set(cleaned))  # Remove duplicates
        
        return cleaned_skills
    
    def _extract_skills_fallback(self) -> List[str]:
        """Scan entire document for common technical skills"""
        found_skills = []
        full_text = ' '.join(self.lines).lower()
        
        for skill in self.COMMON_SKILLS:
            # Use word boundaries for accurate matching
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, full_text):
                # Add with proper capitalization
                found_skills.append(skill.title() if skill.islower() else skill)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills

    def extract_education(self, sections: Dict[str, tuple]) -> List[Education]:
        """Extract education entries"""
        if 'education' not in sections:
            return []
        
        start, end = sections['education']
        education_list = []
        current_entry = None
        
        for line in self.lines[start:end]:
            # Look for degree indicators
            if any(keyword in line.upper() for keyword in ['BACHELOR', 'MASTER', 'DIPLOMA', 'CERTIFICATE', 'PHD', 'DOCTORATE', 'B.SC', 'M.SC', 'DEGREE', 'HONOURS', 'MATRIC']):
                # Save previous entry
                if current_entry:
                    education_list.append(current_entry)
                
                # Extract year if present
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                year = year_match.group(0) if year_match else None
                
                # Try smarter extraction of Degree vs Institution
                degree = line
                institution = ""
                
                # Common separators
                separators = [
                    r'\s{2,}', # Multiple spaces
                    r'\s*\|\s*', # Pipe
                    r'\s+at\s+', # " at "
                    r'\s+from\s+', # " from "
                    r'\s*-\s*', # Dash
                    r',\s*' # Comma (risky, but common)
                ]
                
                for sep in separators:
                    parts = re.split(sep, line)
                    if len(parts) > 1 and len(parts[0]) > 3: # Ensure split parts aren't tiny
                        degree = parts[0].strip()
                        institution = parts[1].strip()
                        # If the separator was a semantic one (at/from), we are confident.
                        # If it was comma/dash, we might simply be splitting properly.
                        break
                
                current_entry = Education(
                    degree=degree,
                    institution=institution,
                    year=year,
                    details=[]
                )
            
            # Bullet points or details for current entry
            elif current_entry and line.startswith('•'):
                current_entry.details.append(line[1:].strip())
            elif current_entry and line and not re.match(r'^[A-Z\s]{3,}$', line):
                 # Verify it's not a section match before appending
                 is_section = False
                 if len(line) < 40:
                     for p in self.SECTION_PATTERNS.values():
                         if re.match(p, line): is_section = True; break
                 if not is_section:
                     current_entry.details.append(line)
        
        # Add last entry
        if current_entry:
            education_list.append(current_entry)
        
        return education_list
    
    def extract_work_experience(self, sections: Dict[str, tuple]) -> List[WorkExperience]:
        """Extract work experience entries"""
        if 'experience' not in sections:
            return []
        
        start, end = sections['experience']
        experiences = []
        current_entry = None
        
        for line in self.lines[start:end]:
            # Look for job title pattern (ends with pipe or followed by company)
            # Heuristic: Contains common job words
            if '|' in line or re.search(r'\b(intern|developer|engineer|manager|analyst|consultant|specialist|lead|architect|designer)\b', line, re.I):
                # Check if this looks like a title line
                if not line.startswith('•'):
                    # Save previous entry
                    if current_entry:
                        experiences.append(current_entry)
                    
                    # Parse title | company format
                    if '|' in line:
                        parts = line.split('|')
                        title = parts[0].strip()
                        company = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        title = line
                        company = ""
                    
                    current_entry = WorkExperience(
                        title=title,
                        company=company,
                        responsibilities=[]
                    )
            
            # Look for date ranges
            elif current_entry and re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\b', line, re.I):
                 # Matches lines with dates
                 current_entry.duration = line
            
            # Bullet points for responsibilities
            elif current_entry and line.startswith('•'):
                current_entry.responsibilities.append(line[1:].strip())
            elif current_entry and line and not re.match(r'^[A-Z\s]{3,}$', line):
                # Additional details
                if len(line) > 20:  # Avoid capturing section headers
                    current_entry.responsibilities.append(line)
        
        # Add last entry
        if current_entry:
            experiences.append(current_entry)
        
        return experiences
    
    def extract_projects(self, sections: Dict[str, tuple]) -> List[Project]:
        """Extract project entries"""
        if 'projects' not in sections:
            return []
        
        start, end = sections['projects']
        projects = []
        current_project = None
        
        for line in self.lines[start:end]:
            # Look for project name (usually bold or first line)
            if '|' in line:
                # Save previous project
                if current_project:
                    projects.append(current_project)
                
                parts = line.split('|')
                name = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                current_project = Project(
                    name=name,
                    description=description,
                    technologies=[],
                    details=[]
                )
            
            # Look for technologies line
            elif current_project and any(keyword in line for keyword in ['Technologies:', 'Tech Stack:', 'Built with:']):
                tech_line = line.split(':', 1)[1] if ':' in line else line
                techs = re.split(r'[,;]', tech_line)
                current_project.technologies = [t.strip() for t in techs if t.strip()]
            
            # Bullet points for project details
            elif current_project and line.startswith('•'):
                current_project.details.append(line[1:].strip())
            elif current_project and line and not re.match(r'^[A-Z\s]{3,}$', line):
                if len(line) > 15:
                    current_project.details.append(line)
        
        # Add last project
        if current_project:
            projects.append(current_project)
        
        return projects
    
    def parse(self) -> CVData:
        """Main parsing method - extracts all CV information"""
        # Extract text if not already done
        if not self.lines:
            self.extract_text()
        
        # Extract contact information
        contact = self.extract_contact_info()
        
        # Find section boundaries
        sections = self.find_section_boundaries()
        
        # Extract each section
        profile = self.extract_profile(sections)
        skills = self.extract_skills(sections)
        education = self.extract_education(sections)
        experience = self.extract_work_experience(sections)
        projects = self.extract_projects(sections)
        
        # Create CV data object
        cv_data = CVData(
            contact_info=contact,
            professional_profile=profile,
            technical_skills=skills,
            education=education,
            work_experience=experience,
            projects=projects,
            raw_text=self.raw_text
        )
        
        return cv_data
    
    def to_dict(self, cv_data: CVData) -> dict:
        """Convert CV data to dictionary"""
        result = {
            'contact_info': asdict(cv_data.contact_info),
            'professional_profile': cv_data.professional_profile,
            'technical_skills': cv_data.technical_skills,
            'education': [asdict(edu) for edu in cv_data.education],
            'work_experience': [asdict(exp) for exp in cv_data.work_experience],
            'projects': [asdict(proj) for proj in cv_data.projects],
        }
        return result
    
    def to_json(self, cv_data: CVData, indent: int = 2) -> str:
        """Convert CV data to JSON string"""
        return json.dumps(self.to_dict(cv_data), indent=indent, ensure_ascii=False)
