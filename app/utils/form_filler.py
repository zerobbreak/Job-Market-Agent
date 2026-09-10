
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FormAutoFiller:
    """
    Simulates the logic for mapping profile data to common job application form fields.
    Useful for "Easy Apply" simulations or preparing data for browser automation.
    """
    
    COMMON_FIELDS = {
        'first_name': ['first name', 'firstname', 'given name'],
        'last_name': ['last name', 'lastname', 'surname', 'family name'],
        'email': ['email', 'e-mail', 'email address'],
        'phone': ['phone', 'mobile', 'cell', 'contact number'],
        'linkedin': ['linkedin', 'linkedin profile', 'linkedin url'],
        'portfolio': ['portfolio', 'website', 'personal site'],
        'github': ['github', 'git'],
        'location': ['location', 'city', 'address', 'current location'],
        'authorized': ['authorized', 'eligible to work', 'visa'],
        'sponsorship': ['sponsorship', 'require visa'],
    }

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile

    def generate_form_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a filled form data dictionary for a specific job.
        """
        form_data = {}
        
        # 1. Basic Info
        full_name = self.profile.get('name', '').split()
        if len(full_name) >= 2:
            form_data['first_name'] = full_name[0]
            form_data['last_name'] = " ".join(full_name[1:])
        else:
            form_data['first_name'] = self.profile.get('name', '')
            form_data['last_name'] = ""
            
        form_data['email'] = self.profile.get('email', '')
        form_data['phone'] = self.profile.get('phone', '')
        form_data['location'] = self.profile.get('location', '')
        
        # 2. Links
        links = self.profile.get('links', {})
        form_data['linkedin'] = links.get('linkedin', '') or self.profile.get('linkedin', '')
        form_data['portfolio'] = links.get('portfolio', '') or self.profile.get('portfolio', '')
        form_data['github'] = links.get('github', '') or self.profile.get('github', '')

        # 3. Compliance / Legal (Defaults based on typical user)
        # In a real app, these should be stored in the user profile settings
        form_data['authorized_to_work'] = True 
        form_data['requires_sponsorship'] = False
        form_data['agree_terms'] = True
        form_data['agree_privacy'] = True

        # 4. Job Specific Questions (Heuristic)
        # If job description asks for "Years of experience with X", try to answer
        # This is a placeholder for more advanced NLP Question Answering
        form_data['custom_answers'] = self._infer_answers(job)

        return form_data

    def _infer_answers(self, job: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Infer answers to potential screening questions based on job description.
        """
        answers = []
        desc = job.get('description', '').lower()
        
        # Example: Experience Check
        if "years" in desc and "experience" in desc:
            # Simple heuristic: user has X years (derived from profile)
            # For now, just a placeholder
            answers.append({
                "question": "Years of experience",
                "answer": self.profile.get('experience_level', 'Entry Level') 
            })
            
        return answers
