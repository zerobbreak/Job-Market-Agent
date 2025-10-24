import json
from playwright.sync_api import sync_playwright
import time

def handle_popups(page):
    """
    Handle common popups like cookie consent, policy acceptance, etc.
    """
    popup_selectors = [
        # Cookie consent buttons
        "button:has-text('Accept')",
        "button:has-text('Accept All')",
        "button:has-text('I Accept')",
        "button:has-text('Agree')",
        "button:has-text('OK')",
        "button:has-text('Got it')",
        "button:has-text('Continue')",
        "button:has-text('Allow')",
        "[id*='accept']",
        "[class*='accept']",
        "[id*='cookie'] button",
        "[class*='cookie'] button",
        "[id*='consent'] button",
        "[class*='consent'] button",
        # Close buttons
        "button.close",
        "button[aria-label='Close']",
        "[class*='close']",
        ".modal button",
    ]
    
    for selector in popup_selectors:
        try:
            button = page.query_selector(selector)
            if button and button.is_visible():
                print(f"   🔘 Clicking popup button: {selector}")
                button.click()
                page.wait_for_timeout(1000)
                return True
        except:
            continue
    
    return False


def scrape_pnet(page, job_title, location):
    print("🔹 Scraping PNet...")
    jobs = []
    
    try:
        # Go to PNet homepage first
        print("   📍 Navigating to PNet homepage...")
        page.goto("https://www.pnet.co.za/", timeout=60000)
        page.wait_for_timeout(3000)
        
        # Handle popups
        print("   🔄 Checking for popups...")
        handle_popups(page)
        page.wait_for_timeout(2000)
        
        # Try to accept policy again if needed
        handle_popups(page)
        page.wait_for_timeout(1000)
        
        # Find and fill the search form
        print(f"   🔍 Searching for: {job_title} in {location}")
        
        # Try multiple search input selectors
        search_input_selectors = [
            "input[name='keywords']",
            "input[placeholder*='Job title']",
            "input[placeholder*='keyword']",
            "input[type='text'][class*='search']",
            "input#keywords",
            "#search-keywords",
            "input.search-input"
        ]
        
        search_input = None
        for selector in search_input_selectors:
            try:
                search_input = page.query_selector(selector)
                if search_input and search_input.is_visible():
                    print(f"   ✓ Found search input: {selector}")
                    break
            except:
                continue
        
        if not search_input:
            print("   ⚠️ Could not find search input. Taking screenshot...")
            page.screenshot(path="pnet_no_search.png")
            with open("pnet_homepage.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            return jobs
        
        # Fill in the search term
        search_input.click()
        search_input.fill(job_title)
        page.wait_for_timeout(500)
        
        # Try to find location input
        location_input_selectors = [
            "input[name='location']",
            "input[placeholder*='Location']",
            "input[placeholder*='location']",
            "input#location",
            "#search-location"
        ]
        
        location_input = None
        for selector in location_input_selectors:
            try:
                location_input = page.query_selector(selector)
                if location_input and location_input.is_visible():
                    print(f"   ✓ Found location input: {selector}")
                    break
            except:
                continue
        
        if location_input:
            location_input.click()
            location_input.fill(location)
            page.wait_for_timeout(500)
        
        # Find and click search button
        search_button_selectors = [
            "button[type='submit']",
            "button:has-text('Search')",
            "input[type='submit']",
            "button.search-button",
            "button[class*='search']",
            ".search-form button"
        ]
        
        search_button = None
        for selector in search_button_selectors:
            try:
                search_button = page.query_selector(selector)
                if search_button and search_button.is_visible():
                    print(f"   ✓ Found search button: {selector}")
                    break
            except:
                continue
        
        if search_button:
            print("   🔘 Clicking search button...")
            search_button.click()
        else:
            # Try pressing Enter instead
            print("   ⌨️ Pressing Enter to search...")
            search_input.press("Enter")
        
        # Wait for results to load
        print("   ⏳ Waiting for results...")
        page.wait_for_timeout(5000)
        
        # Take screenshot after search
        page.screenshot(path="pnet_results.png")
        print("   📸 Screenshot saved as pnet_results.png")
        
        # Wait for job listings to load
        try:
            page.wait_for_selector("div[class*='job'], article, [class*='result']", timeout=10000)
        except:
            print("   ⚠️ Timeout waiting for job listings")
        
        # Try different selectors for job cards
        selectors_to_try = [
            "div.job-result-card",
            "div[class*='job-result']",
            "div[class*='jobCard']",
            "div[class*='job-card']",
            "article[class*='job']",
            "div[data-automation*='job']",
            "[data-testid*='job']",
            ".result-card",
            ".job-listing",
            "div.result",
            "li[class*='job']",
            "[class*='JobCard']",
            "div[class*='Result']"
        ]
        
        cards = []
        used_selector = None
        for selector in selectors_to_try:
            cards = page.query_selector_all(selector)
            if cards and len(cards) > 0:
                used_selector = selector
                print(f"   ✓ Found {len(cards)} job cards with selector: {selector}")
                break
        
        if not cards:
            print("   ⚠️ No job cards found. Saving page HTML for inspection...")
            with open("pnet_results.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("   💡 Check pnet_results.html to find the correct selectors")
            print("   💡 Also check pnet_results.png screenshot")
            return jobs
        
        # Extract job info
        print(f"   📋 Extracting job details from {len(cards)} cards...")
        for i, card in enumerate(cards[:15]):  # Get first 15 jobs
            try:
                # Get all text content first for debugging
                card_text = card.inner_text()
                
                # Try multiple ways to get the title
                title = None
                title_selectors = [
                    "h3", "h2", "h4", "h1",
                    "[class*='title']", 
                    "[class*='Title']",
                    "a[class*='title']",
                    ".job-title",
                    "span[class*='title']",
                    "div[class*='title']"
                ]
                
                for ts in title_selectors:
                    title_el = card.query_selector(ts)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if title and len(title) > 3:
                            break
                
                # If no title found, try getting first heading
                if not title:
                    all_headings = card.query_selector_all("h1, h2, h3, h4")
                    if all_headings:
                        title = all_headings[0].inner_text().strip()
                
                # Get company
                company = None
                company_selectors = [
                    "[class*='company']",
                    "[class*='Company']", 
                    ".company-name",
                    "span.company",
                    "div[class*='company']"
                ]
                
                for cs in company_selectors:
                    company_el = card.query_selector(cs)
                    if company_el:
                        company = company_el.inner_text().strip()
                        if company and len(company) > 1:
                            break
                
                # Get location
                location_text = None
                location_selectors = [
                    "[class*='location']",
                    "[class*='Location']",
                    ".location",
                    "span.location",
                    "div[class*='location']"
                ]
                
                for ls in location_selectors:
                    location_el = card.query_selector(ls)
                    if location_el:
                        location_text = location_el.inner_text().strip()
                        if location_text and len(location_text) > 1:
                            break
                
                # Get URL - try all links
                url = None
                all_links = card.query_selector_all("a")
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and ("/job/" in href or "job-id" in href or "vacancy" in href or "/jobs/" in href):
                        url = href if href.startswith("http") else f"https://www.pnet.co.za{href}"
                        break
                
                # Fallback to first link
                if not url and all_links:
                    href = all_links[0].get_attribute("href")
                    if href:
                        url = href if href.startswith("http") else f"https://www.pnet.co.za{href}"
                
                # Try to extract job description snippet from the card
                description = ""
                desc_selectors = [
                    "[class*='description']",
                    "[class*='summary']",
                    "[class*='snippet']",
                    "[class*='excerpt']",
                    "p",
                    "div:not([class*='title']):not([class*='company']):not([class*='location'])"
                ]

                for ds in desc_selectors:
                    desc_els = card.query_selector_all(ds)
                    for desc_el in desc_els:
                        text = desc_el.inner_text().strip()
                        if text and len(text) > 20 and not any(word in text.lower() for word in ['apply now', 'save job', 'share']):
                            description += text + " "
                            if len(description) > 200:  # Limit description length
                                break
                    if len(description) > 50:
                        break

                description = description.strip()[:500]  # Limit to 500 chars

                # Only add if we have at least a title
                if title and len(title) > 3:
                    job = {
                        "title": title,
                        "company": company or "N/A",
                        "location": location_text or "N/A",
                        "url": url or "N/A",
                        "description": description or f"{title} position at {company or 'Company'} in {location_text or 'Location'}",
                        "source": "PNet"
                    }
                    jobs.append(job)
                    print(f"   ✓ Job {i+1}: {title[:50]}")
                else:
                    print(f"   ⚠️ Card {i+1}: No valid title found")
                    if i < 3:  # Show first 3 card texts for debugging
                        print(f"      Card text: {card_text[:100]}...")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing card {i+1}: {e}")
                continue
                
    except Exception as e:
        print(f"   ❌ Error scraping PNet: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"✅ Found {len(jobs)} jobs on PNet\n")
    return jobs


def scrape_indeed(page, job_title, location):
    print("🔹 Scraping Indeed...")
    jobs = []
    
    try:
        search_url = f"https://za.indeed.com/jobs?q={job_title.replace(' ', '+')}&l={location.replace(' ', '+')}"
        print(f"   URL: {search_url}")
        
        page.goto(search_url, timeout=60000)
        page.wait_for_timeout(3000)
        
        # Handle popups
        print("   🔄 Checking for popups...")
        handle_popups(page)
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="indeed_debug.png")
        print("   📸 Screenshot saved as indeed_debug.png")
        
        # Wait for job listings
        try:
            page.wait_for_selector("div[class*='job'], td.resultContent", timeout=10000)
        except:
            print("   ⚠️ Timeout waiting for job listings")
        
        # Try different selectors for Indeed
        selectors_to_try = [
            "div.job_seen_beacon",
            "td.resultContent",
            "div[data-jk]",
            "div.slider_container div.job_seen_beacon",
            "[class*='jobsearch-ResultsList'] > li",
            "div[class*='result']",
            "li[class*='job']"
        ]
        
        cards = []
        for selector in selectors_to_try:
            cards = page.query_selector_all(selector)
            if cards and len(cards) > 0:
                print(f"   ✓ Found {len(cards)} elements with selector: {selector}")
                break
        
        if not cards:
            print("   ⚠️ No job cards found. Saving page HTML...")
            with open("indeed_debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            return jobs
        
        for i, card in enumerate(cards[:15]):
            try:
                # Indeed-specific selectors
                title = None
                title_selectors = [
                    "h2.jobTitle span[title]",
                    "h2.jobTitle span",
                    "h2.jobTitle",
                    "span[title]",
                    "a.jcs-JobTitle",
                    "h2 a span"
                ]
                
                for ts in title_selectors:
                    title_el = card.query_selector(ts)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if not title:
                            title = title_el.get_attribute("title")
                        if title and len(title) > 3:
                            break
                
                company = None
                company_selectors = [
                    "span[data-testid='company-name']",
                    "span.companyName",
                    "[class*='company']"
                ]
                
                for cs in company_selectors:
                    company_el = card.query_selector(cs)
                    if company_el:
                        company = company_el.inner_text().strip()
                        if company:
                            break
                
                location_text = None
                location_selectors = [
                    "div[data-testid='text-location']",
                    "div.companyLocation",
                    "[class*='location']"
                ]
                
                for ls in location_selectors:
                    location_el = card.query_selector(ls)
                    if location_el:
                        location_text = location_el.inner_text().strip()
                        if location_text:
                            break
                
                # Get job link
                link = card.query_selector("a[data-jk]") or card.query_selector("h2 a") or card.query_selector("a")
                url = None
                if link:
                    href = link.get_attribute("href")
                    if href:
                        url = href if href.startswith("http") else f"https://za.indeed.com{href}"
                
                # Try to extract job description snippet from the card
                description = ""
                desc_selectors = [
                    "[class*='description']",
                    "[class*='summary']",
                    "[class*='snippet']",
                    "[class*='excerpt']",
                    "[class*='job-snippet']",
                    "p",
                    "div:not([class*='title']):not([class*='company']):not([class*='location'])"
                ]

                for ds in desc_selectors:
                    desc_els = card.query_selector_all(ds)
                    for desc_el in desc_els:
                        text = desc_el.inner_text().strip()
                        if text and len(text) > 20 and not any(word in text.lower() for word in ['apply now', 'save job', 'share']):
                            description += text + " "
                            if len(description) > 200:  # Limit description length
                                break
                    if len(description) > 50:
                        break

                description = description.strip()[:500]  # Limit to 500 chars

                if title and len(title) > 3:
                    job = {
                        "title": title,
                        "company": company or "N/A",
                        "location": location_text or "N/A",
                        "url": url or "N/A",
                        "description": description or f"{title} position at {company or 'Company'} in {location_text or 'Location'}",
                        "source": "Indeed"
                    }
                    jobs.append(job)
                    print(f"   ✓ Job {i+1}: {title[:50]}")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing card {i+1}: {e}")
                continue
                
    except Exception as e:
        print(f"   ❌ Error scraping Indeed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"✅ Found {len(jobs)} jobs on Indeed\n")
    return jobs


def scrape_careerjunction(page, job_title, location):
    print("🔹 Scraping CareerJunction...")
    jobs = []
    
    try:
        search_url = f"https://www.careerjunction.co.za/jobs/results?keywords={job_title.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        print(f"   URL: {search_url}")
        
        page.goto(search_url, timeout=60000)
        page.wait_for_timeout(3000)
        
        # Handle popups
        print("   🔄 Checking for popups...")
        handle_popups(page)
        page.wait_for_timeout(2000)
        
        page.screenshot(path="careerjunction_debug.png")
        print("   📸 Screenshot saved as careerjunction_debug.png")
        
        # Wait for results
        try:
            page.wait_for_selector("div[class*='job'], article", timeout=10000)
        except:
            print("   ⚠️ Timeout waiting for job listings")
        
        selectors_to_try = [
            "div.job-card",
            "article.job",
            "[class*='job-card']",
            "[class*='jobCard']",
            "div[class*='result']",
            "article",
            "li[class*='job']"
        ]
        
        cards = []
        for selector in selectors_to_try:
            cards = page.query_selector_all(selector)
            if cards and len(cards) > 0:
                print(f"   ✓ Found {len(cards)} elements with selector: {selector}")
                break
        
        if not cards:
            print("   ⚠️ No job cards found. Saving page HTML...")
            with open("careerjunction_debug.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            return jobs
        
        for i, card in enumerate(cards[:15]):
            try:
                title = None
                title_selectors = ["h2", "h3", "h4", "[class*='title']", "a"]
                for ts in title_selectors:
                    title_el = card.query_selector(ts)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if title and len(title) > 3:
                            break
                
                company = None
                company_el = card.query_selector("[class*='company']")
                if company_el:
                    company = company_el.inner_text().strip()
                
                location_text = None
                location_el = card.query_selector("[class*='location']")
                if location_el:
                    location_text = location_el.inner_text().strip()
                
                link = card.query_selector("a")
                url = None
                if link:
                    href = link.get_attribute("href")
                    if href:
                        url = href if href.startswith("http") else f"https://www.careerjunction.co.za{href}"
                
                # Try to extract job description snippet from the card
                description = ""
                desc_selectors = [
                    "[class*='description']",
                    "[class*='summary']",
                    "[class*='snippet']",
                    "[class*='excerpt']",
                    "p",
                    "div:not([class*='title']):not([class*='company']):not([class*='location'])"
                ]

                for ds in desc_selectors:
                    desc_els = card.query_selector_all(ds)
                    for desc_el in desc_els:
                        text = desc_el.inner_text().strip()
                        if text and len(text) > 20 and not any(word in text.lower() for word in ['apply now', 'save job', 'share']):
                            description += text + " "
                            if len(description) > 200:  # Limit description length
                                break
                    if len(description) > 50:
                        break

                description = description.strip()[:500]  # Limit to 500 chars

                if title and len(title) > 3:
                    job = {
                        "title": title,
                        "company": company or "N/A",
                        "location": location_text or "N/A",
                        "url": url or "N/A",
                        "description": description or f"{title} position at {company or 'Company'} in {location_text or 'Location'}",
                        "source": "CareerJunction"
                    }
                    jobs.append(job)
                    print(f"   ✓ Job {i+1}: {title[:50]}")
                    
            except Exception as e:
                print(f"   ⚠️ Error parsing card {i+1}: {e}")
                continue
                
    except Exception as e:
        print(f"   ❌ Error scraping CareerJunction: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"✅ Found {len(jobs)} jobs on CareerJunction\n")
    return jobs


def scrape_all(job_title, location):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=True,  # Run in background for better performance
            slow_mo=1000  # Slow down actions to avoid being blocked
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        print(f"\n🔍 Scraping jobs for: {job_title} in {location}")
        print("=" * 60)

        pnet_jobs = scrape_pnet(page, job_title, location)
        time.sleep(2)

        indeed_jobs = scrape_indeed(page, job_title, location)
        time.sleep(2)

        cj_jobs = scrape_careerjunction(page, job_title, location)

        all_jobs = pnet_jobs + indeed_jobs + cj_jobs

        browser.close()
        print(f"\n{'=' * 60}")
        print(f"✅ Total jobs scraped: {len(all_jobs)}")
        print(f"   PNet: {len(pnet_jobs)}")
        print(f"   Indeed: {len(indeed_jobs)}")
        print(f"   CareerJunction: {len(cj_jobs)}")

        # Save results
        if all_jobs:
            with open("jobs.json", "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, ensure_ascii=False, indent=2)
            print("💾 Saved results to jobs.json")
        else:
            print("⚠️ No jobs found to save")

        return all_jobs


if __name__ == "__main__":
    scrape_all("software engineer", "Johannesburg")