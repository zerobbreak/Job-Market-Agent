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
            
            CRITICAL: The CV text may be extracted from PDF/DOCX and may have formatting issues. Look for section markers like [SECTION:PROFILE], [SECTION:EXPERIENCE], etc. that indicate document structure.
            
            Guidelines:
            1. **Professional Profile/Summary (HIGHEST PRIORITY)**:
               - Look for sections marked [SECTION:PROFILE] or headers like "PROFESSIONAL PROFILE", "SUMMARY", "OBJECTIVE", "ABOUT ME"
               - Extract the FIRST substantial paragraph or 2-3 sentences after the profile header
               - This is usually located at the beginning of the CV, after contact information
               - Extract the ACTUAL text from the CV - DO NOT use generic phrases like "To leverage my skills" or "Seeking opportunities"
               - If no explicit profile section exists, extract the first meaningful paragraph (50+ characters) that describes the candidate
               - The professional_profile field is CRITICAL for job matching - extract it accurately
            
            2. **Accuracy**: Copy names, dates, and titles exactly as they appear.
            
            3. **Skills**: 
               - Look for [SECTION:SKILLS] or "SKILLS", "TECHNICAL SKILLS" sections
               - Split concatenated skills (e.g. 'Java/Python' -> ['Java', 'Python']).
               - Categorize them logically (Languages, Frameworks, Tools).
               - Ignore generic headers like "Technical Skills" as skill items.
               - If no skills section, infer from work experience and projects
            
            4. **Experience**: 
               - Look for [SECTION:EXPERIENCE] or "EXPERIENCE", "WORK EXPERIENCE" sections
               - Focus on the most recent and relevant roles.
               - Extract job titles, companies, durations, and responsibilities accurately
            
            5. **Education**:
               - Look for [SECTION:EDUCATION] or "EDUCATION", "QUALIFICATIONS" sections
               - Extract degrees, institutions, and years
            
            6. **Handling Messy Text**:
               - Text may have line breaks in wrong places - reconstruct sentences when needed
               - Ignore PDF artifacts like "(cid:XXX)" patterns
               - Section markers [SECTION:XXX] indicate document structure - use them
               - If text seems garbled, try to extract meaningful information from what's available
            
            7. **Inference**: If a section is missing (e.g. no explicit "Skills" section), infer from project descriptions or work history.
            
            IMPORTANT: The professional_profile field MUST contain actual text from the CV, not generic placeholder text. If you cannot find a profile/summary section, extract the first meaningful paragraph that describes the candidate's background or career goals.
            """

            # Prepare contents - Use text extraction (more reliable than PDF bytes)
            contents = []
            
            # Extract text first (more reliable than passing PDF directly)
            if not self.raw_text:
                self.extract_text()
            
            # Use extracted text for AI parsing
            if self.raw_text:
                # Truncate to avoid token limits (Gemini has context limits)
                text_content = self.raw_text[:50000] if len(self.raw_text) > 50000 else self.raw_text
                # Combine prompt and text in a single message
                full_prompt = f"{prompt}\n\nCV Content:\n{text_content}"
                contents.append(full_prompt)
            else:
                # If text extraction failed, we can't parse
                print("No text extracted from CV, cannot parse with AI")
                return None

            # 3. Call API with Structured Output
            # Use gemini-1.5-flash for speed/cost, or gemini-1.5-pro for complex layouts
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config={
                        'response_mime_type': 'application/json',
                        'response_schema': CVData
                    }
                )
            except Exception as api_error:
                # Log the error for debugging
                print(f"Gemini API call failed: {api_error}")
                # If structured output fails, try without schema
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents
                    )
                    # Parse JSON from text response
                    text_resp = response.text
                    data = json.loads(text_resp.strip())
                    cv_data = CVData(**data)
                    if not cv_data.raw_text:
                        cv_data.raw_text = self.raw_text or ""
                    return cv_data
                except Exception as fallback_error:
                    print(f"Fallback parsing also failed: {fallback_error}")
                    raise api_error  # Re-raise original error
            
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
                
                # If professional_profile is empty or generic, try rule-based extraction
                if not cv_data.professional_profile or len(cv_data.professional_profile.strip()) < 20:
                    print("AI parsing returned empty/generic professional_profile, trying rule-based extraction")
                    fallback_profile = self._extract_professional_profile_fallback(self.raw_text or "")
                    if fallback_profile:
                        cv_data.professional_profile = fallback_profile
                        print(f"Rule-based extraction found profile: {fallback_profile[:100]}...")
                
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
            
            # If professional_profile is empty or generic, try rule-based extraction
            if not cv_data.professional_profile or len(cv_data.professional_profile.strip()) < 20:
                print("AI parsing returned empty/generic professional_profile, trying rule-based extraction")
                fallback_profile = self._extract_professional_profile_fallback(self.raw_text or "")
                if fallback_profile:
                    cv_data.professional_profile = fallback_profile
                    print(f"Rule-based extraction found profile: {fallback_profile[:100]}...")
                
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
        
        # Strategy 2: Extract from email prefix (improved)
        search_text = "\n".join(self.lines[:30])
        email_match = re.search(self.CONTACT_PATTERNS['email'], search_text)
        if email_match:
            email = email_match.group(0)
            prefix = email.split('@')[0]
            # Clean the prefix more intelligently - handle dots, underscores, numbers
            # Replace common separators with spaces
            prefix = re.sub(r'[._-]', ' ', prefix)
            # Remove standalone numbers and numbers at start/end
            prefix = re.sub(r'\b\d+\b', ' ', prefix)
            prefix = re.sub(r'^\d+|\d+$', '', prefix)
            # Remove multiple spaces
            prefix = re.sub(r'\s+', ' ', prefix).strip()
            words = [w for w in prefix.split() if len(w) > 1 and w.isalpha()]
            if words and len(words) <= 5:  # Reasonable name length
                return ' '.join(w.title() for w in words)
        
        # Strategy 3: Extract from LinkedIn URL
        linkedin_match = re.search(self.CONTACT_PATTERNS['linkedin'], search_text)
        if linkedin_match:
            linkedin_url = linkedin_match.group(0)
            # Extract username from LinkedIn URL (e.g., linkedin.com/in/john-doe -> john-doe)
            username_match = re.search(r'/in/([^/?]+)', linkedin_url)
            if username_match:
                username = username_match.group(1)
                # Convert username to name (e.g., john-doe -> John Doe)
                name_parts = username.replace('-', ' ').replace('_', ' ').split()
                # Filter out non-name parts
                name_parts = [p for p in name_parts if p.isalpha() and len(p) > 1]
                if name_parts and len(name_parts) <= 5:
                    return ' '.join(p.title() for p in name_parts)
        
        # Strategy 4: Extract from GitHub URL
        github_match = re.search(self.CONTACT_PATTERNS['github'], search_text)
        if github_match:
            github_url = github_match.group(0)
            # Extract username from GitHub URL (e.g., github.com/johndoe -> johndoe)
            username_match = re.search(r'github\.com/([^/?]+)', github_url)
            if username_match:
                username = username_match.group(1)
                # Try to split camelCase or convert to name
                # If it's already separated by dashes/underscores, use that
                if '-' in username or '_' in username:
                    name_parts = re.split(r'[-_]', username)
                else:
                    # Try to split camelCase
                    name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', username)
                name_parts = [p for p in name_parts if p.isalpha() and len(p) > 1]
                if name_parts and len(name_parts) <= 5:
                    return ' '.join(p.title() for p in name_parts)
        
        # Strategy 5: Fallback - just return first non-empty line (if it looks reasonable)
        if self.lines:
            first_line = self.lines[0].strip()
            # Only use if it looks like it could be a name (not too long, mostly letters)
            if len(first_line) < 50 and re.match(r'^[A-Za-z\s\-\'\.]+$', first_line):
                words = first_line.split()
                if 1 <= len(words) <= 5:
                    return ' '.join(w.title() if w.islower() or w.isupper() else w for w in words)
        
        return ""

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
    
    def _is_generic_phrase(self, text: str) -> bool:
        """Check if text contains only generic career phrases"""
        if not text or len(text.strip()) < 20:
            return False
        
        text_lower = text.lower().strip()
        generic_phrases = [
            "to leverage my skills",
            "seeking opportunities",
            "looking for",
            "to utilize my",
            "seeking a position",
            "looking to apply",
            "to contribute",
            "seeking employment",
            "to apply my",
            "seeking a role",
            "to leverage my skills in a challenging role",
            "seeking a challenging position",
            "looking for opportunities"
        ]
        
        # Check if text is primarily generic phrases
        generic_count = sum(1 for phrase in generic_phrases if phrase in text_lower)
        # If text is short and contains generic phrases, it's likely generic
        if len(text) < 50 and generic_count > 0:
            return True
        # If text is longer but mostly generic phrases
        if generic_count >= 2:
            return True
        # If text is very short and matches a generic phrase exactly
        if len(text) < 40:
            for phrase in generic_phrases:
                if phrase in text_lower and len(text_lower) - len(phrase) < 10:
                    return True
        
        return False
    
    def _extract_professional_profile_fallback(self, text: str) -> Optional[str]:
        """Rule-based extraction of professional profile/summary from CV text"""
        if not text:
            return None
        
        lines = text.split('\n')
        profile_text = None
        
        # Method 1: Look for explicit section markers
        section_markers = [
            r'\[SECTION:PROFILE\]',
            r'(?i)^\s*(PROFESSIONAL\s+PROFILE|PROFILE|SUMMARY|OBJECTIVE|ABOUT\s+ME|CAREER\s+OBJECTIVE|PROFESSIONAL\s+SUMMARY)\s*:?\s*$'
        ]
        
        profile_start = None
        for i, line in enumerate(lines):
            for marker_pattern in section_markers:
                if re.search(marker_pattern, line):
                    profile_start = i + 1
                    break
            if profile_start is not None:
                break
        
        if profile_start is not None:
            # Extract text until next section or significant break
            profile_lines = []
            for i in range(profile_start, min(profile_start + 10, len(lines))):  # Max 10 lines
                line = lines[i].strip()
                # Stop at next section marker
                if re.search(r'\[SECTION:', line):
                    break
                # Stop at next major section header (all caps, short)
                if re.match(r'^[A-Z\s]{2,30}$', line) and len(line) < 40 and i > profile_start + 2:
                    break
                # Stop at empty line followed by section-like text
                if not line and i < len(lines) - 1:
                    next_line = lines[i + 1].strip()
                    if re.match(r'^[A-Z\s]{2,30}$', next_line) and len(next_line) < 40:
                        break
                if line:
                    profile_lines.append(line)
            
            if profile_lines:
                profile_text = ' '.join(profile_lines).strip()
                # Clean up: remove excessive spaces, normalize
                profile_text = re.sub(r'\s+', ' ', profile_text)
                if len(profile_text) > 20:  # Minimum meaningful length
                    # Check if it's a generic phrase - if so, return None
                    if self._is_generic_phrase(profile_text):
                        return None
                    return profile_text
        
        # Method 2: Extract first 2-3 meaningful paragraphs (after contact info, before experience)
        if not profile_text:
            # Find where contact info likely ends (look for email/phone patterns)
            contact_end = 0
            for i, line in enumerate(lines[:20]):  # Check first 20 lines
                if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line):
                    contact_end = i + 1
                    break
                if re.search(r'(?:\+?27|0)[\s\-]?\d{2,3}[\s\-]?\d{3}[\s\-]?\d{4}', line):
                    contact_end = i + 1
                    break
            
            # Find where experience section starts
            experience_start = len(lines)
            for i, line in enumerate(lines):
                if re.search(r'(?i)(EXPERIENCE|WORK\s+EXPERIENCE|EMPLOYMENT)', line):
                    experience_start = i
                    break
            
            # Extract paragraphs between contact and experience
            if experience_start > contact_end + 2:
                candidate_lines = lines[contact_end:experience_start]
                paragraphs = []
                current_para = []
                
                for line in candidate_lines:
                    line = line.strip()
                    if not line:
                        if current_para:
                            paragraphs.append(' '.join(current_para))
                            current_para = []
                    else:
                        # Skip section headers
                        if not re.match(r'^[A-Z\s]{2,30}$', line) or len(line) > 40:
                            current_para.append(line)
                
                if current_para:
                    paragraphs.append(' '.join(current_para))
                
                # Take first 2-3 meaningful paragraphs
                meaningful_paras = [p for p in paragraphs if len(p) > 20][:3]
                if meaningful_paras:
                    profile_text = ' '.join(meaningful_paras).strip()
                    if len(profile_text) > 20:
                        # Check if it's a generic phrase - if so, return None
                        if self._is_generic_phrase(profile_text):
                            return None
                        return profile_text
        
        # Method 3: Extract first substantial paragraph (fallback)
        if not profile_text:
            for line in lines[:30]:  # Check first 30 lines
                line = line.strip()
                # Skip contact info, headers, short lines
                if (len(line) > 50 and 
                    not re.search(r'@|phone|email|linkedin|github', line.lower()) and
                    not re.match(r'^[A-Z\s]{2,30}$', line)):
                    profile_text = line
                    break
        
        # Final check: if we found text, verify it's not generic
        if profile_text and len(profile_text) > 20:
            if self._is_generic_phrase(profile_text):
                return None
            return profile_text
        
        return None

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
