import logging
import base64
import time
import os
import random
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

# Try to import stealth
try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

from .utils import human_delay, simulate_human_browsing

logger = logging.getLogger(__name__)

class BrowserAutomation:
    """
    Manages headless browser sessions for automated job applications.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.playwright = None
        
    def __enter__(self):
        self.playwright = sync_playwright().start()
        # Enhanced bot detection bypass - industry best practices
        # Based on solutions from Simplify, LazyApply, and other production systems
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu',
                '--start-maximized',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def capture_screenshot(self, page: Page) -> str:
        """Capture screenshot and return as base64 string"""
        try:
            screenshot_bytes = page.screenshot(type='jpeg', quality=50)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return ""

    def apply_to_job(self, job_url: str, form_data: Dict[str, Any], files: Dict[str, str], log_callback=None) -> Dict[str, Any]:
        """
        Main entry point to apply for a job.
        Detects ATS and delegates to specific adapter.
        """
        if not self.browser:
            raise RuntimeError("Browser not initialized. Use 'with BrowserAutomation() as bot:'")

        # Enhanced browser context with realistic fingerprinting
        # Rotate user agents to avoid detection
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        context = self.browser.new_context(
            user_agent=random.choice(user_agents),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # NYC default
            color_scheme='light',
            # Add extra HTTP headers to look more legitimate
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
        )
        
        page = context.new_page()
        
        # Inject anti-detection scripts before stealth
        page.add_init_script("""
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Chrome runtime
            window.chrome = {
                runtime: {}
            };
        """)
        
        # Apply stealth if available
        if HAS_STEALTH:
            try:
                stealth_sync(page)
            except Exception as e:
                logger.warning(f"Stealth application failed: {e}")

        result = {'success': False, 'status': 'failed', 'log': []}
        
        def log(msg):
            if log_callback: log_callback(msg)
            result['log'].append(msg)
            logger.info(f"[AutoApply] {msg}")

        try:
            log(f"Navigating to {job_url}...")
            try:
                # Navigate with retry logic
                max_nav_retries = 3
                nav_success = False
                for nav_attempt in range(max_nav_retries):
                    try:
                        page.goto(job_url, timeout=30000, wait_until='domcontentloaded')
                        # Wait for page to be interactive
                        page.wait_for_load_state('domcontentloaded', timeout=10000)
                        human_delay(1000, 2000)  # Simulate human reading time
                        nav_success = True
                        break
                    except Exception as nav_e:
                        if nav_attempt < max_nav_retries - 1:
                            log(f"Navigation attempt {nav_attempt + 1} failed, retrying...")
                            human_delay(2000, 4000)
                        else:
                            raise nav_e
                
                if not nav_success:
                    raise Exception("Failed to navigate after retries")
                
                # Simulate human browsing behavior before automation
                log("Simulating human browsing behavior...")
                simulate_human_browsing(page)
                
            except Exception as e:
                log(f"Navigation error: {e}")
                raise
            
            # Detect ATS with improved detection
            url_lower = page.url.lower()
            page_title = page.title().lower()
            page_content = page.content().lower()
            
            success = False
            
            # Enhanced ATS detection with multiple signals
            ats_detected = None
            
            if 'lever.co' in url_lower or 'lever' in page_content[:5000]:
                ats_detected = 'lever'
                log("Detected Lever.co ATS")
            elif 'greenhouse.io' in url_lower or 'greenhouse' in page_content[:5000]:
                ats_detected = 'greenhouse'
                log("Detected Greenhouse ATS")
            elif 'workday' in url_lower or 'workday' in page_content[:5000]:
                ats_detected = 'workday'
                log("Detected Workday ATS")
            elif 'smartrecruiters' in url_lower or 'smartrecruiters' in page_content[:5000]:
                ats_detected = 'smartrecruiters'
                log("Detected SmartRecruiters ATS")
            elif 'linkedin.com' in url_lower:
                ats_detected = 'linkedin'
                log("Detected LinkedIn Easy Apply")
            
            # Route to appropriate adapter
            if ats_detected == 'lever':
                from .adapters.lever import LeverAdapter
                adapter = LeverAdapter(page, log)
                success = adapter.fill(form_data, files)
            elif ats_detected == 'greenhouse':
                from .adapters.greenhouse import GreenhouseAdapter
                adapter = GreenhouseAdapter(page, log)
                success = adapter.fill(form_data, files)
            else:
                log(f"Using Generic Adapter for {ats_detected or 'unknown'} ATS...")
                from .adapters.generic import GenericAdapter
                adapter = GenericAdapter(page, log)
                success = adapter.fill(form_data, files)
                
            if success:
                log("Application submitted (or form filled) successfully!")
                result['success'] = True
                result['status'] = 'submitted'
            else:
                log("Could not complete application automatically.")
                result['status'] = 'manual_review_needed'

        except PlaywrightTimeoutError as e:
            log(f"Timeout error during automation: {str(e)}")
            result['error'] = f"Timeout: {str(e)}"
            result['status'] = 'timeout'
        except Exception as e:
            log(f"Error during automation: {str(e)}")
            result['error'] = str(e)
            result['status'] = 'error'
            import traceback
            result['traceback'] = traceback.format_exc()
        finally:
            # Always capture final state for debugging
            try:
                result['screenshot'] = self.capture_screenshot(page)
            except Exception as screenshot_err:
                log(f"Failed to capture screenshot: {screenshot_err}")
                result['screenshot'] = ""
            
            try:
                context.close()
            except Exception:
                pass
            
        return result
