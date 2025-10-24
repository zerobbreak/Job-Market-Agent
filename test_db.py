import main
print(f'Jobs in database: {main.jobs_collection.count()}')
if main.jobs_collection.count() > 0:
    results = main.jobs_collection.query(query_texts=['software engineer'], n_results=3)
    for i, job_id in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][i]
        print(f'Job {i+1}: {metadata["title"]} at {metadata["company"]}');
