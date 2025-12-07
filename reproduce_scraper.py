import sys
import os

# Add current directory to path so we can import utils
sys.path.append(os.getcwd())

print("Checking jobspy installation...")
try:
    import jobspy
    print(f"✅ jobspy imported successfully. Version/File: {jobspy.__file__}")
except ImportError as e:
    print(f"❌ Failed to import jobspy: {e}")

print("\nChecking Scraper Initialization...")
try:
    from utils.scraping import advanced_scraper
    print("✅ Scraper initialized")
    
    print("\nAttempting small scrape...")
    try:
        # scraping.py uses print inside, so we might see output
        jobs = advanced_scraper.scrape_jobs(
            search_term="Python", 
            location="South Africa", 
            results_wanted=1,
            site_name=["indeed", "linkedin", "google", "glassdoor", "zip_recruiter"],
            safe_mode=True # Enable safe mode for testing
        )
        print(f"✅ Scrape returned {len(jobs)} jobs")
    except Exception as e:
        print(f"❌ Scrape failed: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ Failed to import/init scraper: {e}")
    import traceback
    traceback.print_exc()
