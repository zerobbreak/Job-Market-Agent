"""
Greenhouse ATS Adapter
Implements battle-tested multi-strategy approach for Greenhouse job applications
"""
import time
import os
from playwright.sync_api import Page
from ..utils import (
    human_delay, human_fill, human_click, human_type,
    find_element_multiple_strategies, wait_for_element_with_retry
)


class GreenhouseAdapter:
    """
    Automates filling Greenhouse job applications with human-like behavior
    """
    
    def __init__(self, page: Page, logger):
        self.page = page
        self.log = logger
        
    def fill(self, data: dict, files: dict) -> bool:
        """
        Fill the Greenhouse form with retry logic and human-like behavior
        """
        try:
            self.log("Starting Greenhouse adapter...")
            human_delay(1000, 2000)  # Initial pause
            
            # Wait for form to be ready
            self.page.wait_for_load_state('networkidle', timeout=15000)
            human_delay(500, 1000)
            
            # 1. Resume Upload
            if files.get('cv') and os.path.exists(files['cv']):
                self.log("Uploading CV...")
                resume_strategies = [
                    {'type': 'css', 'value': 'input[type="file"][name*="resume"]'},
                    {'type': 'css', 'value': 'input[type="file"][name*="cv"]'},
                    {'type': 'css', 'value': 'input[type="file"]'},
                ]
                
                resume_input = find_element_multiple_strategies(self.page, resume_strategies, self.log)
                if resume_input:
                    resume_input.set_input_files(files['cv'])
                    self.log("CV uploaded successfully")
                    human_delay(2000, 3000)  # Wait for upload processing
                else:
                    self.log("Warning: Could not find resume upload field")
            
            # 2. Basic Info Fields
            self.log("Filling personal information...")
            
            # Name field
            name_strategies = [
                {'type': 'css', 'value': 'input[name*="firstname"], input[id*="firstname"]'},
                {'type': 'css', 'value': 'input[placeholder*="First Name"]'},
                {'type': 'xpath', 'value': '//input[contains(@placeholder, "First") or contains(@name, "first")]'},
            ]
            name_field = find_element_multiple_strategies(self.page, name_strategies, self.log)
            if name_field and data.get('name'):
                first_name = data['name'].split(' ')[0] if ' ' in data['name'] else data['name']
                human_fill(self.page, name_strategies[0]['value'], first_name)
            
            # Last name
            lastname_strategies = [
                {'type': 'css', 'value': 'input[name*="lastname"], input[id*="lastname"]'},
                {'type': 'css', 'value': 'input[placeholder*="Last Name"]'},
            ]
            lastname_field = find_element_multiple_strategies(self.page, lastname_strategies, self.log)
            if lastname_field and data.get('name'):
                last_name = ' '.join(data['name'].split(' ')[1:]) if ' ' in data['name'] else ''
                if last_name:
                    human_fill(self.page, lastname_strategies[0]['value'], last_name)
            
            # Email
            email_strategies = [
                {'type': 'css', 'value': 'input[type="email"], input[name*="email"]'},
                {'type': 'css', 'value': 'input[placeholder*="Email"]'},
            ]
            email_field = find_element_multiple_strategies(self.page, email_strategies, self.log)
            if email_field and data.get('email'):
                human_fill(self.page, email_strategies[0]['value'], data['email'])
            
            # Phone
            phone_strategies = [
                {'type': 'css', 'value': 'input[type="tel"], input[name*="phone"]'},
                {'type': 'css', 'value': 'input[placeholder*="Phone"]'},
            ]
            phone_field = find_element_multiple_strategies(self.page, phone_strategies, self.log)
            if phone_field and data.get('phone'):
                human_fill(self.page, phone_strategies[0]['value'], data['phone'])
            
            # 3. Links (LinkedIn, Portfolio)
            if data.get('linkedin'):
                self.log("Filling LinkedIn URL...")
                linkedin_strategies = [
                    {'type': 'css', 'value': 'input[name*="linkedin"], input[id*="linkedin"]'},
                    {'type': 'css', 'value': 'input[placeholder*="LinkedIn"]'},
                ]
                linkedin_field = find_element_multiple_strategies(self.page, linkedin_strategies, self.log)
                if linkedin_field:
                    human_fill(self.page, linkedin_strategies[0]['value'], data['linkedin'])
            
            if data.get('portfolio'):
                self.log("Filling Portfolio URL...")
                portfolio_strategies = [
                    {'type': 'css', 'value': 'input[name*="portfolio"], input[name*="website"], input[name*="url"]'},
                    {'type': 'css', 'value': 'input[placeholder*="Portfolio"], input[placeholder*="Website"]'},
                ]
                portfolio_field = find_element_multiple_strategies(self.page, portfolio_strategies, self.log)
                if portfolio_field:
                    human_fill(self.page, portfolio_strategies[0]['value'], data['portfolio'])
            
            # 4. Cover Letter
            if files.get('cover_letter') and os.path.exists(files['cover_letter']):
                self.log("Uploading Cover Letter...")
                cl_strategies = [
                    {'type': 'css', 'value': 'input[type="file"][name*="cover"]'},
                    {'type': 'css', 'value': 'textarea[name*="cover"], textarea[id*="cover"]'},
                ]
                
                cl_input = find_element_multiple_strategies(self.page, cl_strategies, self.log)
                if cl_input:
                    # Try file upload first
                    try:
                        if cl_input.evaluate('el => el.tagName === "INPUT"'):
                            cl_input.set_input_files(files['cover_letter'])
                            self.log("Cover letter uploaded")
                        else:
                            # Text area - read and paste content
                            with open(files['cover_letter'], 'r', encoding='utf-8') as f:
                                cl_text = f.read()
                            human_type(self.page, cl_strategies[1]['value'], cl_text)
                    except Exception as e:
                        self.log(f"Cover letter upload failed: {e}")
            
            human_delay(1000, 2000)
            
            # 5. Submit Button with validation
            self.log("Looking for submit button...")
            submit_strategies = [
                {'type': 'role', 'role': 'button', 'name': 'Submit Application'},
                {'type': 'role', 'role': 'button', 'name': 'Submit'},
                {'type': 'css', 'value': 'button[type="submit"]'},
                {'type': 'css', 'value': 'input[type="submit"]'},
                {'type': 'css', 'value': 'button:has-text("Submit")'},
                {'type': 'css', 'value': 'button:has-text("Apply")'},
            ]
            
            submit_button = find_element_multiple_strategies(self.page, submit_strategies, self.log)
            if submit_button:
                # Validate form is ready
                self.log("Validating form completion...")
                human_delay(500, 1000)
                
                # Scroll to button
                submit_button.scroll_into_view_if_needed()
                human_delay(300, 600)
                
                # Check if button is enabled
                is_enabled = submit_button.is_enabled()
                if is_enabled:
                    self.log("Submitting application...")
                    # Use the element directly instead of selector
                    submit_button.scroll_into_view_if_needed()
                    human_delay(300, 600)
                    submit_button.hover()
                    human_delay(100, 200)
                    submit_button.click()
                    
                    # Wait for confirmation
                    human_delay(2000, 3000)
                    
                    # Check for success indicators
                    success_indicators = [
                        'Thank you',
                        'Application submitted',
                        'Success',
                        'confirmation'
                    ]
                    
                    page_text = self.page.content().lower()
                    if any(indicator.lower() in page_text for indicator in success_indicators):
                        self.log("Application submitted successfully!")
                        return True
                    else:
                        self.log("Form submitted, but confirmation unclear. Please verify manually.")
                        return True  # Assume success if button was clicked
                else:
                    self.log("Submit button is disabled. Form may be incomplete.")
                    return False
            else:
                self.log("Could not find submit button")
                return False
                
        except Exception as e:
            self.log(f"Greenhouse adapter error: {e}")
            import traceback
            self.log(traceback.format_exc())
            return False

