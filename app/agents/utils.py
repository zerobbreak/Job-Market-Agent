"""
Utility functions for browser automation with human-like behavior
Based on industry best practices from Simplify, LazyApply, and other production systems
"""
import random
import time
from typing import Optional
from playwright.sync_api import Page, Locator


def human_delay(min_ms: float = 100, max_ms: float = 500):
    """Random delay to simulate human thinking/typing speed"""
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    time.sleep(delay)


def human_type(page: Page, selector: str, text: str, delay_range: tuple = (50, 150)):
    """
    Type text character by character with random delays (human-like)
    """
    element = page.locator(selector).first
    element.click()
    human_delay(100, 300)  # Pause before typing
    
    for char in text:
        element.type(char, delay=random.uniform(delay_range[0], delay_range[1]))
        # Occasionally add longer pauses (like human hesitation)
        if random.random() < 0.1:  # 10% chance
            human_delay(200, 500)


def human_click(page: Page, selector: str = None, element: Locator = None, wait_after: bool = True):
    """
    Click with human-like behavior: scroll into view, hover, then click
    Can accept either a selector string or a Locator element
    """
    if element is None:
        if selector is None:
            raise ValueError("Either selector or element must be provided")
        element = page.locator(selector).first
    
    # Scroll into view smoothly
    element.scroll_into_view_if_needed()
    human_delay(200, 400)
    
    # Hover before clicking (human behavior)
    element.hover()
    human_delay(100, 250)
    
    # Click
    element.click()
    
    if wait_after:
        human_delay(300, 600)  # Wait after click for page response


def human_fill(page: Page, selector: str, value: str, clear_first: bool = True):
    """
    Fill input field with human-like behavior
    """
    element = page.locator(selector).first
    element.scroll_into_view_if_needed()
    human_delay(100, 200)
    element.click()
    human_delay(50, 150)
    
    if clear_first:
        element.fill('')  # Clear first
        human_delay(50, 100)
    
    # Type with human-like speed
    human_type(page, selector, value)


def wait_for_element_with_retry(
    page: Page,
    selector: str,
    timeout: int = 10000,
    retries: int = 3,
    log_callback=None
) -> Optional[Locator]:
    """
    Wait for element with multiple retry strategies
    """
    strategies = [
        lambda: page.locator(selector).first,
        lambda: page.query_selector(selector),
        lambda: page.wait_for_selector(selector, timeout=timeout),
    ]
    
    for attempt in range(retries):
        for strategy in strategies:
            try:
                element = strategy()
                if element and (hasattr(element, 'is_visible') and element.is_visible() or True):
                    if log_callback:
                        log_callback(f"Found element with selector: {selector}")
                    return element
            except Exception:
                continue
        
        if attempt < retries - 1:
            wait_time = (attempt + 1) * 1000
            if log_callback:
                log_callback(f"Retrying element search (attempt {attempt + 1}/{retries})...")
            time.sleep(wait_time / 1000)
    
    return None


def find_element_multiple_strategies(
    page: Page,
    strategies: list,
    log_callback=None
) -> Optional[Locator]:
    """
    Try multiple selector strategies to find an element
    strategies: list of dicts with 'type' (css, xpath, text, role) and 'value'
    """
    for strategy in strategies:
        try:
            if strategy['type'] == 'css':
                element = page.locator(strategy['value']).first
            elif strategy['type'] == 'xpath':
                element = page.locator(f"xpath={strategy['value']}").first
            elif strategy['type'] == 'text':
                element = page.get_by_text(strategy['value'], exact=False).first
            elif strategy['type'] == 'role':
                element = page.get_by_role(strategy['role'], name=strategy.get('name', ''), exact=False).first
            else:
                continue
            
            if element.is_visible(timeout=2000):
                if log_callback:
                    log_callback(f"Found element using {strategy['type']}: {strategy.get('value', strategy.get('name', ''))}")
                return element
        except Exception:
            continue
    
    return None


def random_scroll(page: Page, min_scroll: int = 100, max_scroll: int = 500):
    """Random scroll to simulate human browsing behavior"""
    scroll_amount = random.randint(min_scroll, max_scroll)
    page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    human_delay(200, 400)


def simulate_human_browsing(page: Page):
    """Simulate human browsing patterns before automation"""
    # Random scroll
    random_scroll(page)
    human_delay(500, 1000)
    
    # Small mouse movement simulation
    page.evaluate("""
        const event = new MouseEvent('mousemove', {
            view: window,
            bubbles: true,
            cancelable: true,
            clientX: Math.random() * window.innerWidth,
            clientY: Math.random() * window.innerHeight
        });
        document.dispatchEvent(event);
    """)
    human_delay(300, 600)

