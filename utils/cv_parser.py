"""
CV Parser - Hybrid AI & Rule-based text extraction from PDF resumes
Extracts structured information using Google Gemini AI with a rule-based fallback
"""

import re
import pdfplumber
from typing import Dict, List, Optional, Union
import json
import os
import google.genai as genai
from pydantic import BaseModel, Field

# --- Pydantic Models for Structured Output ---

class ContactInfo(BaseModel):
    """Contact information structure"""
    name: Optional[str] = Field(None, description="Full name of the candidate")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Physical address or location (City, Country)")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio: Optional[str] = Field(None, description="Portfolio website URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")

class Education(BaseModel):
    """Education entry structure"""
    degree: str = Field(..., description="Degree obtained (e.g. BSc Computer Science)")
    institution: str = Field(..., description="University or Institution name")
    year: Optional[str] = Field(None, description="Year of graduation or duration (e.g. 2020-2023)")
    details: List[str] = Field(default_factory=list, description="Additional details or achievements")

class WorkExperience(BaseModel):
    """Work experience entry structure"""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    duration: Optional[str] = Field(None, description="Employment duration (e.g. Jan 2020 - Present)")
    responsibilities: List[str] = Field(default_factory=list, description="List of responsibilities and achievements")

class Project(BaseModel):
    """Project entry structure"""
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Brief description of the project")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    details: List[str] = Field(default_factory=list, description="Additional details")

class CVData(BaseModel):
    """Complete CV data structure"""
    contact_info: ContactInfo
    professional_profile: Optional[str] = Field(None, description="Professional summary or objective")
    technical_skills: Dict[str, List[str]] = Field(default_factory=dict, description="Skills grouped by category (e.g. Languages, Frameworks)")
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    raw_text: str = Field("", description="Raw text content of the CV")

class CVParser:
    """Hybrid CV parser using AI with Rule-based fallback"""
    
    # Common section headers in CVs
    SECTION_PATTERNS = {
        'contact': r'(?i).*(contact|personal|details|information).*',
        'profile': r'(?i).*(professional\s+profile|profile|summary|objective|about\s+me).*',
        'skills': r'(?i).*(technical\s+skills|skills|core\s+competencies|expertise|tools|technologies).*',
        'education': r'(?i).*(education|academic|qualifications|studies).*',
        'experience': r'(?i).*(work\s+experience|experience|employment|professional\s+experience|history).*',
        'projects': r'(?i).*(projects|key\s+projects|portfolio).*',
    }
    
    # Contact information patterns
    CONTACT_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(?:\+?27|0)[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{4}|\d{10}',
        'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?',
        'github': r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?',
        'portfolio': r'(?:https?://)?[\w\-]+\.(?:vercel\.app|netlify\.app|herokuapp\.com|github\.io)[\w\-/]*',
        'url': r'https?://[^\s]+',
    }
    
    def __init__(self, file_path: str = None, raw_text: str = None):
        """Initialize parser with PDF path or raw text"""
        self.file_path = file_path
        self.raw_text = raw_text or ""
        self.lines = []
        if self.raw_text:
             self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
        
    def extract_text(self) -> str:
        """Extract text from PDF preserving structure, or return provided raw text"""
        if self.raw_text and not self.file_path:
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
        
        self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
        return self.raw_text
    
    def parse_with_ai(self) -> Optional[CVData]:
        """Parse CV using Google Gemini AI (Multimodal & Structured)"""
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return None

        try:
            client = genai.Client(api_key=api_key)
            
            prompt = """
            You are an expert CV parser. Extract information from the provided CV document into the specified structure.
            
            Guidelines:
            1. **Accuracy**: Copy names, dates, and titles exactly as they appear.
            2. **Skills**: 
               - Split concatenated skills (e.g. 'Java/Python' -> ['Java', 'Python']).
               - categorize them logically (Languages, Frameworks, Tools).
               - Ignore generic headers like "Technical Skills" as skill items.
            3. **Experience**: Focus on the most recent and relevant roles.
            4. **Inference**: If a section is missing (e.g. no explicit "Skills" section), infer skills from the project descriptions or work history.
            """

            # Prepare contents
            contents = []
            
            # 1. Add File Content (Multimodal) if available
            if self.file_path and os.path.exists(self.file_path) and self.file_path.lower().endswith('.pdf'):
                try:
                    with open(self.file_path, "rb") as f:
                        file_bytes = f.read()
                    contents.append({
                        "mime_type": "application/pdf",
                        "data": file_bytes
                    })
                except Exception as e:
                    print(f"Failed to read PDF file for AI: {e}")
                    # Fallback to text if file read fails
                    if self.raw_text:
                        contents.append(self.raw_text[:50000])
            elif self.raw_text:
                # Text-only fallback
                contents.append(self.raw_text[:50000])
            else:
                # Try extracting text if not yet done
                if not self.raw_text:
                    self.extract_text()
                if self.raw_text:
                    contents.append(self.raw_text[:50000])
                else:
                    return None # No data to parse

            # 2. Add Prompt
            contents.append(prompt)

            # 3. Call API with Structured Output
            # Use gemini-1.5-flash for speed/cost, or gemini-1.5-pro for complex layouts
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=contents,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': CVData
                }
            )
            
            # 4. Parse Response
            # The SDK should return a parsed object if response_schema is used, 
            # or we parse the text manually if it returns raw JSON string.
            # Newer SDKs might return a `parsed` attribute.
            
            if hasattr(response, 'parsed') and response.parsed:
                cv_data = response.parsed
                # Ensure raw_text is populated if it wasn't extracted before
                if not cv_data.raw_text and self.raw_text:
                    cv_data.raw_text = self.raw_text
                elif not cv_data.raw_text and not self.raw_text:
                     # If we used multimodal, we might not have raw text yet.
                     # We can leave it empty or try to extract it now.
                     self.extract_text()
                     cv_data.raw_text = self.raw_text
                return cv_data
                
            # Fallback: Parse text manually
            text_resp = response.text
            data = json.loads(text_resp.strip())
            
            # Clean skills logic (still useful if AI is messy)
            if 'technical_skills' in data:
                data['technical_skills'] = self._clean_skills(data['technical_skills'])

            # Convert dict to Pydantic model
            cv_data = CVData(**data)
            
            # Ensure raw_text is preserved
            if not cv_data.raw_text:
                cv_data.raw_text = self.raw_text or ""
                
            return cv_data
            
        except Exception as e:
            print(f"AI Parsing failed: {e}")
            return None

    def _clean_skills(self, skills_dict: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean up extracted skills by removing headers and splitting merged items"""
        cleaned_skills = {}
        
        # Common section headers to filter out
        headers_to_remove = {
            'programming languages', 'frameworks & tools', 'additional skills', 
            'technical skills', 'soft skills', 'tools & technologies',
            'languages', 'frameworks', 'tools', 'databases', 'cloud'
        }
        
        for category, skill_list in skills_dict.items():
            cleaned_list = []
            for skill in skill_list:
                s = skill.strip()
                if not s: continue
                
                # Skip if it's likely a header
                if s.lower() in headers_to_remove:
                    continue
                    
                # Skip if it looks like a concatenated header string (long and contains common header words)
                if len(s) > 30 and any(h in s.lower() for h in ['languages', 'frameworks', 'tools', 'skills']):
                    continue
                
                # Split by obvious delimiters that might have been missed
                if '   ' in s: # multiple spaces
                    parts = re.split(r'\s{3,}', s)
                    cleaned_list.extend([p.strip() for p in parts if p.strip()])
                    continue
                    
                cleaned_list.append(s)
            
            if cleaned_list:
                cleaned_skills[category] = cleaned_list
                
        return cleaned_skills

    def extract_contact_info(self) -> ContactInfo:
        """Extract contact information from the beginning of CV (Rule-based)"""
        contact = ContactInfo()
        
        # Name is typically the first significant line
        if self.lines:
            # First non-empty line is usually the name
            contact.name = self.lines[0]
        
        # Search first 30 lines for contact info
        search_text = "\n".join(self.lines[:30])
        
        # Extract email
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
            elif re.search(r'\b(?:johannesburg|pretoria|cape town|durban|midrand|sandton|london|new york|berlin)\b', line, re.I):
                if not any(x in line.lower() for x in ['phone', 'email', 'http', '.com']):
                    contact.address = line
                    break
        
        return contact

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
        if 'skills' not in sections:
            # Fallback: scan whole doc if section missing? For now just return empty or simple scan
            return {}
        
        start, end = sections['skills']
        skills = {}
        current_category = "General" 
        
        for line in self.lines[start:end]:
            if ':' in line:
                parts = line.split(':', 1)
                category = parts[0].strip()
                skill_list = parts[1].strip()
                skills_items = re.split(r'[,;]', skill_list)
                skills[category] = [s.strip() for s in skills_items if s.strip()]
                current_category = category
            
            elif current_category and line and not re.match(r'^[A-Z\s]{3,}$', line):
                additional_skills = re.split(r'[,;]', line)
                items = [s.strip() for s in additional_skills if s.strip()]
                if not items: continue
                
                if current_category not in skills:
                    skills[current_category] = []
                skills[current_category].extend(items)
        
        return skills

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
    
    def parse_with_rules(self) -> CVData:
        """Original rule-based parsing method"""
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

    def parse(self) -> CVData:
        """Main parsing method - tries AI first, falls back to rules"""
        # Always ensure text is extracted first (if we have no file path, or just to have raw_text available)
        if not self.lines and self.raw_text:
            self.lines = [line.strip() for line in self.raw_text.split('\n') if line.strip()]
            
        # Try AI Parsing first
        ai_result = self.parse_with_ai()
        if ai_result:
            print("Successfully parsed CV with Gemini AI")
            return ai_result
            
        print("AI parsing unavailable or failed, falling back to rule-based parser")
        return self.parse_with_rules()
    
    def to_dict(self, cv_data: CVData) -> dict:
        """Convert CV data to dictionary"""
        return cv_data.model_dump()
    
    def to_json(self, cv_data: CVData, indent: int = 2) -> str:
        """Convert CV data to JSON string"""
        return cv_data.model_dump_json(indent=indent)
