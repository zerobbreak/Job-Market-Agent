import main

# Test the complete flow
student_profile = {
    'summary': 'Computer science student with skills in React, Node.js, Python, Java, SQL, Machine Learning',
    'skills': ['Python', 'Java', 'SQL', 'Machine Learning', 'React', 'Node.js'],
    'desired_role': 'Software Engineer',
    'industry': 'fintech',
    'field_of_study': 'Computer Science',
    'location': 'South Africa'
}

print('🔄 Testing complete job matching flow...')

# Discover jobs
matched_jobs = main.discover_new_jobs(student_profile)
print(f'\n✅ Job discovery completed. Found {len(matched_jobs)} matches.')

# Show results
for i, job in enumerate(matched_jobs[:3]):  # Show first 3 matches
    print(f'\n--- Job {i+1} ---')
    print(f'Title: {job["job_id"]}')
    print(f'Score: {job["match_score"]:.1f}%')
    print(f'Analysis: {job["analysis"][:200]}...')
