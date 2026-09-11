from playwright.sync_api import Page
import time
import os
from ..utils import (
    human_delay, human_fill, human_click, human_type,
    find_element_multiple_strategies, wait_for_element_with_retry
)


class LeverAdapter:
    """
    Automates filling Lever.co job applications with battle-tested retry logic
    """
    
    def __init__(self, page: Page, logger):
        self.page = page
        self.log = logger
        
    def fill(self, data: dict, files: dict) -> bool:
        """
        Fill the Lever form with human-like behavior and retry logic
        """
        try:
            self.log("Starting Lever adapter...")
            human_delay(1000, 2000)
            
            # Wait for page to be ready
            self.page.wait_for_load_state('networkidle', timeout=15000)
            human_delay(500, 1000)
            
            # Click 'Apply' button if present (Lever sometimes has a top button)
            self.log("Looking for initial Apply button...")
            apply_btn_strategies = [
                {'type': 'css', 'value': 'a.postings-btn.template-btn-submit'},
                {'type': 'css', 'value': 'a:has-text("Apply")'},
                {'type': 'role', 'role': 'link', 'name': 'Apply'},
            ]
            
            apply_btn = find_element_multiple_strategies(self.page, apply_btn_strategies, self.log)
            if apply_btn:
                self.log("Clicking initial Apply button...")
                human_click(self.page, apply_btn_strategies[0]['value'])
                human_delay(2000, 3000)  # Wait for form to appear
                self.page.wait_for_load_state('networkidle', timeout=10000)

            # 1. Resume Upload with retry
            if files.get('cv') and os.path.exists(files['cv']):
                self.log("Uploading CV...")
                resume_strategies = [
                    {'type': 'css', 'value': 'input[name="resume"]'},
                    {'type': 'css', 'value': 'input[type="file"][name*="resume"]'},
                    {'type': 'css', 'value': 'input[type="file"]'},
                ]
                
                resume_input = find_element_multiple_strategies(self.page, resume_strategies, self.log)
                if resume_input:
                    resume_input.set_input_files(files['cv'])
                    self.log("CV uploaded")
                    human_delay(2000, 3000)  # Wait for processing
                else:
                    self.log("Warning: Could not find resume upload field")
            
            # 2. Basic Info with human-like typing
            self.log("Filling personal information...")
            
            # Name - Lever uses single name field or split
            name_strategies = [
                {'type': 'css', 'value': 'input[name="name"]'},
                {'type': 'css', 'value': 'input[id*="name"]'},
            ]
            name_field = find_element_multiple_strategies(self.page, name_strategies, self.log)
            if name_field and data.get('name'):
                full_name = data['name']
                human_fill(self.page, name_strategies[0]['value'], full_name)
            
            # Email
            email_strategies = [
                {'type': 'css', 'value': 'input[name="email"]'},
                {'type': 'css', 'value': 'input[type="email"]'},
            ]
            email_field = find_element_multiple_strategies(self.page, email_strategies, self.log)
            if email_field and data.get('email'):
                human_fill(self.page, email_strategies[0]['value'], data['email'])
            
            # Phone
            phone_strategies = [
                {'type': 'css', 'value': 'input[name="phone"]'},
                {'type': 'css', 'value': 'input[type="tel"]'},
            ]
            phone_field = find_element_multiple_strategies(self.page, phone_strategies, self.log)
            if phone_field and data.get('phone'):
                human_fill(self.page, phone_strategies[0]['value'], data['phone'])
            
            # 3. Links
            self.log("Filling links...")
            if data.get('linkedin'):
                linkedin_strategies = [
                    {'type': 'css', 'value': 'input[name="urls[LinkedIn]"]'},
                    {'type': 'css', 'value': 'input[name*="linkedin"]'},
                ]
                linkedin_field = find_element_multiple_strategies(self.page, linkedin_strategies, self.log)
                if linkedin_field:
                    human_fill(self.page, linkedin_strategies[0]['value'], data['linkedin'])
            
            if data.get('portfolio'):
                portfolio_strategies = [
                    {'type': 'css', 'value': 'input[name="urls[Portfolio]"]'},
                    {'type': 'css', 'value': 'input[name*="portfolio"]'},
                ]
                portfolio_field = find_element_multiple_strategies(self.page, portfolio_strategies, self.log)
                if portfolio_field:
                    human_fill(self.page, portfolio_strategies[0]['value'], data['portfolio'])
            
            # 4. Cover Letter
            if files.get('cover_letter') and os.path.exists(files['cover_letter']):
                self.log("Uploading Cover Letter...")
                cl_strategies = [
                    {'type': 'css', 'value': 'input[name="coverLetter"]'},
                    {'type': 'css', 'value': 'input[type="file"][name*="cover"]'},
                    {'type': 'css', 'value': 'textarea[name*="cover"]'},
                ]
                
                cl_input = find_element_multiple_strategies(self.page, cl_strategies, self.log)
                if cl_input:
                    try:
                        # Check if it's a file input
                        tag_name = cl_input.evaluate('el => el.tagName')
                        if tag_name == 'INPUT':
                            cl_input.set_input_files(files['cover_letter'])
                            self.log("Cover letter uploaded")
                        else:
                            # Text area
                            with open(files['cover_letter'], 'r', encoding='utf-8') as f:
                                cl_text = f.read()
                            human_type(self.page, cl_strategies[2]['value'], cl_text)
                    except Exception as e:
                        self.log(f"Cover letter handling failed: {e}")
            
            human_delay(1000, 2000)
            
            # 5. Submit Button - NOW ACTUALLY CLICKS IT
            self.log("Looking for submit button...")
            submit_strategies = [
                {'type': 'css', 'value': 'button[type="submit"]'},
                {'type': 'css', 'value': 'input[type="submit"]'},
                {'type': 'role', 'role': 'button', 'name': 'Submit'},
                {'type': 'css', 'value': 'button:has-text("Submit")'},
            ]
            
            submit_button = find_element_multiple_strategies(self.page, submit_strategies, self.log)
            if submit_button:
                # Validate button is enabled
                is_enabled = submit_button.is_enabled()
                if is_enabled:
                    self.log("Submitting application...")
                    submit_button.scroll_into_view_if_needed()
                    human_delay(300, 600)
                    submit_button.click()
                    
                    # Wait for submission
                    human_delay(2000, 3000)
                    
                    # Check for success
                    page_text = self.page.content().lower()
                    if any(word in page_text for word in ['thank you', 'submitted', 'success', 'confirmation']):
                        self.log("Application submitted successfully!")
                        return True
                    else:
                        self.log("Form submitted (verification pending)")
                        return True
                else:
                    self.log("Submit button disabled - form may be incomplete")
                    return False
            else:
                self.log("Could not find submit button")
                return False
            
        except Exception as e:
            self.log(f"Lever adapter error: {e}")
            import traceback
            self.log(traceback.format_exc())
            return False
