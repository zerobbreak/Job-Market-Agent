# Fix: Force Real-Time Scraping & Eliminate Stale Cache

I have identified the root cause: The `AdvancedJobScraper` is aggressively caching old search results (like "Sales Operations Manager" and "Cashier") in the `job_cache` directory and serving them repeatedly, even when you request a "fresh" match.

I will implement a true "Force Refresh" mechanism that bypasses this cache and triggers a live search.

## 1. Clear Existing Stale Cache
- Delete all files in `Job-Market-Agent/job_cache/` to immediately remove the "Sales Operations Manager" and "Cashier" records.

## 2. Update `AdvancedJobScraper` (`utils/scraping.py`)
- Modify `scrape_with_advanced_features` to accept a `force_refresh` boolean.
- If `force_refresh=True`:
    - Skip the `load_from_cache` check.
    - Delete the existing cache file for that search query (if it exists) before scraping.
    - Force a new live scrape.

## 3. Update Pipeline & Routes
- **`services/pipeline_service.py`**: Update `search_jobs` to accept and pass the `force_refresh` flag to the scraper.
- **`routes/job_routes.py`**: Update `_perform_fresh_matching` to pass `force_refresh=True` to the pipeline when the user clicks "Refresh Matches".

## 4. Outcome
- When you click "Refresh Matches", the system will ignore the old "library" of jobs.
- It will perform a live scrape based on your AI-suggested role (e.g., "Senior Python Developer").
- You will only see new, relevant jobs fetched in that specific session.
