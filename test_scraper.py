from scrapper import scrape_all

# Test the enhanced scraper
jobs = scrape_all("software engineer", "Johannesburg")

print(f"\nTotal jobs scraped: {len(jobs)}")
for i, job in enumerate(jobs[:3]):  # Show first 3 jobs
    print(f"\nJob {i+1}:")
    print(f"  Title: {job['title']}")
    print(f"  Company: {job['company']}")
    print(f"  Description length: {len(job.get('description', ''))}")
    print(f"  Description preview: {job.get('description', '')[:150]}...")
