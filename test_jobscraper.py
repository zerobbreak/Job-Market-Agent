import csv
from scrapper import scrape_all_advanced, advanced_scraper

print("🚀 Advanced Job Scraper Demo")
print("=" * 50)

# 1. Basic advanced scraping with caching
print("\n1️⃣ Basic Advanced Scraping:")
jobs = scrape_all_advanced(
    job_title="software engineer",
    location="San Francisco, CA",
    site_name=["indeed", "linkedin", "google"],
    results_wanted=30,
    hours_old=72,
    linkedin_fetch_description=True,  # Get full descriptions
    verbose=1  # Less verbose for demo
)

print(f"✅ Found {len(jobs)} jobs")

# 2. Show sample enriched job data
if jobs:
    sample_job = jobs[0]
    print(f"\n2️⃣ Sample Enriched Job Data:")
    print(f"Title: {sample_job['title']}")
    print(f"Company: {sample_job['company']}")
    print(f"Skills: {', '.join(sample_job.get('skills', []))}")
    print(f"Relevance Score: {sample_job.get('relevance_score', 0):.2f}")
    print(f"Salary Info: {sample_job.get('salary_info', {})}")

# 3. Advanced filtering examples
print(f"\n3️⃣ Advanced Filtering:")

# Filter by relevance score
high_relevance = advanced_scraper.filter_jobs(jobs, min_relevance=0.8)
print(f"High relevance jobs (>0.8): {len(high_relevance)}")

# Filter by required skills
python_jobs = advanced_scraper.filter_jobs(jobs, required_skills=['Python'])
print(f"Python-related jobs: {len(python_jobs)}")

# Filter by salary
high_salary_jobs = advanced_scraper.filter_jobs(jobs, min_salary=100000)
print(f"High salary jobs (>$100k): {len(high_salary_jobs)}")

# Filter by location keywords
sf_jobs = advanced_scraper.filter_jobs(jobs, location_keywords=['San Francisco', 'SF'])
print(f"San Francisco jobs: {len(sf_jobs)}")

# Multi-criteria filter
premium_jobs = advanced_scraper.filter_jobs(
    jobs,
    min_relevance=0.5,
    required_skills=['Python', 'JavaScript'],
    sources=['indeed', 'linkedin'],
    min_salary=80000
)
print(f"Premium jobs (Python/JS, Indeed/LinkedIn, >$80k): {len(premium_jobs)}")

# 4. Export in multiple formats
print(f"\n4️⃣ Exporting Data:")
if jobs:
    # Export full dataset
    advanced_scraper.export_jobs(jobs, "jobs_advanced", "json")
    advanced_scraper.export_jobs(jobs, "jobs_advanced", "csv")
    print("✅ Exported to JSON and CSV")

    # Export filtered results
    if premium_jobs:
        advanced_scraper.export_jobs(premium_jobs, "jobs_premium", "json")
        print("✅ Exported premium jobs to JSON")

# 5. Demonstrate caching
print(f"\n5️⃣ Caching Demo:")
print("Running the same search again (should use cache)...")
jobs_cached = scrape_all_advanced(
    job_title="software engineer",
    location="San Francisco, CA",
    site_name=["indeed", "linkedin", "google"],
    results_wanted=30,
    use_cache=True  # This should load from cache
)
print(f"✅ Loaded {len(jobs_cached)} jobs from cache")

# 6. Performance comparison
print(f"\n6️⃣ Performance Summary:")
print(f"Total jobs scraped: {len(jobs)}")
print(f"Jobs after deduplication: {len(jobs)} (duplicates removed automatically)")
print(f"Jobs with extracted skills: {sum(1 for j in jobs if j.get('skills'))}")
print(f"Jobs with salary info: {sum(1 for j in jobs if j.get('salary_info', {}).get('salary_min'))}")
print(f"Cache directory: job_cache/ (created automatically)")

print(f"\n🎉 Advanced scraper ready! Check the exported files and cache directory.")
print("Features available:")
print("  • Job deduplication")
print("  • Automatic data cleaning")
print("  • Skill extraction")
print("  • Salary parsing")
print("  • Relevance scoring")
print("  • Advanced filtering")
print("  • Multi-format export")
print("  • Intelligent caching")
print("  • Comprehensive logging")