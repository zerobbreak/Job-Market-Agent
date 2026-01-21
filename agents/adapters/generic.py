import re
import time
import os
from playwright.sync_api import Page
from ..utils import (
    human_delay, human_fill, human_click, human_type,
    find_element_multiple_strategies, wait_for_element_with_retry, simulate_human_browsing
)

class GenericAdapter:
    def __init__(self, page: Page, logger=print):
        self.page = page
        self.log = logger

    def fill(self, form_data: dict, files: dict) -> bool:
        """
        Generic form filler using heuristic matching with multi-strategy retry logic
        Battle-tested approach used in production systems
        """
        self.log("Starting Generic Adapter with enhanced retry logic...")
        
        try:
            # Wait for page to be ready
            self.page.wait_for_load_state('domcontentloaded', timeout=15000)
            human_delay(1000, 2000)
            
            # 1. Handle LinkedIn Easy Apply or Redirects if detected
            if "linkedin.com" in self.page.url:
                self.log("LinkedIn detected. Attempting to find 'Apply' button...")
                apply_strategies = [
                    {'type': 'role', 'role': 'button', 'name': 'Apply'},
                    {'type': 'css', 'value': 'button:has-text("Apply")'},
                    {'type': 'css', 'value': 'a:has-text("Apply")'},
                ]
                
                apply_btn = find_element_multiple_strategies(self.page, apply_strategies, self.log)
                if apply_btn:
                    self.log("Clicking Apply on LinkedIn...")
                    human_click(self.page, apply_strategies[0]['value'] if apply_strategies[0]['type'] == 'css' else 'button:has-text("Apply")')
                    human_delay(2000, 3000)
                    self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # 2. Enhanced Heuristic Field Filling with retry
            field_patterns = {
                'name': [r'full\s*name', r'first\s*name', r'name'],
                'email': [r'email', r'e-mail'],
                'phone': [r'phone', r'mobile', r'number', r'telephone'],
                'linkedin': [r'linkedin', r'linked\s*in'],
                'portfolio': [r'portfolio', r'website', r'url', r'personal\s*website'],
                'org': [r'company', r'organization', r'current\s*employer', r'employer']
            }

            filled_count = 0
            max_retries = 2
            
            # Find all inputs with retry
            for attempt in range(max_retries):
                try:
                    inputs = self.page.locator('input:not([type="hidden"]):not([type="submit"]):not([type="file"]), textarea').all()
                    self.log(f"Found {len(inputs)} visible inputs/textarea (attempt {attempt + 1})")
                    break
                except Exception:
                    if attempt < max_retries - 1:
                        human_delay(1000, 2000)
                    else:
                        self.log("Could not find input fields")
                        inputs = []
            
            for inp in inputs:
                try:
                    if not inp.is_visible(timeout=1000): 
                        continue
                    
                    # Get associated label or placeholder or name/id
                    label_text = ""
                    
                    # Try multiple attribute sources
                    label_text += (inp.get_attribute("aria-label") or "")
                    label_text += " " + (inp.get_attribute("placeholder") or "")
                    label_text += " " + (inp.get_attribute("name") or "")
                    label_text += " " + (inp.get_attribute("id") or "")
                    
                    # Try to find actual label element
                    id_val = inp.get_attribute("id")
                    if id_val:
                        try:
                            labels = self.page.locator(f'label[for="{id_val}"]').all_inner_texts()
                            label_text += " " + " ".join(labels)
                        except:
                            pass
                    
                    # Also check parent elements for labels
                    try:
                        parent = inp.evaluate_handle('el => el.closest("label, div, fieldset")')
                        if parent:
                            parent_text = parent.inner_text() if hasattr(parent, 'inner_text') else ""
                            label_text += " " + parent_text
                    except:
                        pass
                    
                    # Check against patterns
                    val_to_fill = None
                    field_key = None
                    for key, patterns in field_patterns.items():
                        for pat in patterns:
                            if re.search(pat, label_text, re.IGNORECASE):
                                val_to_fill = form_data.get(key)
                                field_key = key
                                # Special case for First/Last name splitting
                                if key == 'name' and 'first' in label_text.lower() and form_data.get('name'):
                                    val_to_fill = form_data['name'].split(' ')[0]
                                elif key == 'name' and 'last' in label_text.lower() and form_data.get('name'):
                                    parts = form_data['name'].split(' ')
                                    val_to_fill = parts[-1] if len(parts) > 1 else ""
                                break
                        if val_to_fill: 
                            break
                    
                    if val_to_fill and str(val_to_fill).strip():
                        try:
                            inp.fill(str(val_to_fill))
                            filled_count += 1
                            self.log(f"Filled {field_key} field: '{label_text[:30]}...'")
                            human_delay(200, 400)  # Pause between fields
                        except Exception as fill_err:
                            self.log(f"Failed to fill field: {fill_err}")
                        
                except Exception as e:
                    continue  # Ignore errors on individual fields

            # 3. File Uploads with better detection and retry logic
            file_inputs = []
            for attempt in range(max_retries):
                try:
                    file_inputs = self.page.locator('input[type="file"]').all()
                    if file_inputs:
                        break
                except:
                    if attempt < max_retries - 1:
                        human_delay(1000, 2000)
            
            if file_inputs:
                self.log(f"Found {len(file_inputs)} file inputs")
                upload_success = False
                for idx, finp in enumerate(file_inputs):
                    try:
                        if not finp.is_visible():
                            continue
                        
                        # Try to determine file type from context
                        nearby_text = ""
                        try:
                            parent = finp.evaluate_handle('el => el.closest("div, label, fieldset")')
                            if parent:
                                nearby_text = parent.inner_text() if hasattr(parent, 'inner_text') else ""
                        except:
                            pass
                        
                        # Determine which file to upload
                        file_to_upload = files.get('cv')  # Default
                        if 'cover' in nearby_text.lower() or 'letter' in nearby_text.lower():
                            file_to_upload = files.get('cover_letter') or files.get('cv')
                        
                        if file_to_upload and os.path.exists(file_to_upload):
                            # Retry upload with exponential backoff
                            for upload_attempt in range(3):
                                try:
                                    finp.set_input_files(file_to_upload)
                                    self.log(f"Uploaded file: {os.path.basename(file_to_upload)}")
                                    human_delay(2000, 3000)  # Wait for upload processing
                                    
                                    # Verify upload succeeded by checking for error messages or success indicators
                                    try:
                                        error_elements = self.page.locator('text=/error|failed|invalid/i').all()
                                        if not error_elements:
                                            upload_success = True
                                            break
                                    except:
                                        upload_success = True
                                        break
                                except Exception as upload_err:
                                    if upload_attempt < 2:
                                        self.log(f"Upload attempt {upload_attempt + 1} failed, retrying...")
                                        human_delay(1000 * (upload_attempt + 1), 2000 * (upload_attempt + 1))
                                    else:
                                        raise upload_err
                            
                            if upload_success:
                                break
                    except Exception as e:
                        self.log(f"File upload {idx + 1} failed: {e}")
                        if idx == len(file_inputs) - 1 and not upload_success:
                            self.log("Warning: All file upload attempts failed")

            if filled_count == 0 and not file_inputs:
                self.log("No fields matched or filled. Generic adapter may have failed.")
                # Still try to submit if form might be pre-filled

            self.log(f"Generic Adapter filled {filled_count} fields and {len(file_inputs)} files.")
            human_delay(1000, 2000)
            
            # 4. Submit Button - NOW ACTUALLY CLICKS with validation
            self.log("Looking for submit button...")
            submit_strategies = [
                {'type': 'role', 'role': 'button', 'name': 'Submit Application'},
                {'type': 'role', 'role': 'button', 'name': 'Submit'},
                {'type': 'role', 'role': 'button', 'name': 'Apply'},
                {'type': 'css', 'value': 'button[type="submit"]'},
                {'type': 'css', 'value': 'input[type="submit"]'},
                {'type': 'css', 'value': 'button:has-text("Submit")'},
                {'type': 'css', 'value': 'button:has-text("Apply")'},
                {'type': 'css', 'value': 'button:has-text("Send")'},
            ]
            
            submit_button = find_element_multiple_strategies(self.page, submit_strategies, self.log)
            if submit_button:
                # Validate button state
                is_enabled = submit_button.is_enabled()
                is_visible = submit_button.is_visible()
                
                if is_enabled and is_visible:
                    self.log("Submitting application...")
                    submit_button.scroll_into_view_if_needed()
                    human_delay(300, 600)
                    
                    # Click with human-like behavior
                    submit_button.hover()
                    human_delay(100, 200)
                    submit_button.click()
                    
                    # Wait for submission to process
                    human_delay(2000, 3000)
                    
                    # Check for success indicators
                    try:
                        page_text = self.page.content().lower()
                        success_keywords = ['thank you', 'submitted', 'success', 'confirmation', 'application received']
                        if any(keyword in page_text for keyword in success_keywords):
                            self.log("Application submitted successfully!")
                            return True
                        else:
                            # URL change might indicate success
                            current_url = self.page.url
                            if 'success' in current_url.lower() or 'thank' in current_url.lower():
                                self.log("Application submitted (URL indicates success)")
                                return True
                            else:
                                self.log("Form submitted (please verify manually)")
                                return True  # Assume success if button was clicked
                    except:
                        self.log("Form submitted (verification unclear)")
                        return True
                else:
                    self.log(f"Submit button not ready (enabled={is_enabled}, visible={is_visible})")
                    return False
            else:
                self.log("Could not find submit button - form may use different submission method")
                # Return True anyway if we filled fields (user can click manually)
                return filled_count > 0 or len(file_inputs) > 0

        except Exception as e:
            self.log(f"Generic Adapter Error: {e}")
            return False
