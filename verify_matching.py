import time
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add current directory to path
sys.path.append(os.getcwd())

from services.matching_service import SemanticMatcher

def test_matching():
    print("="*50)
    print("🧪 STARTING MATCHING LOGIC VERIFICATION")
    print("="*50)
    
    # Check API Key presence
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if api_key:
        print(f"✅ API Key found: {api_key[:5]}...")
    else:
        print("⚠️ No API Key found. Expecting fallback to TF-IDF (Keyword Matching).")

    print("\n1️⃣  Initializing SemanticMatcher...")
    matcher = SemanticMatcher()
    
    # Sample Profile
    profile = {
        'experience_level': 'Senior',
        'skills': ['Python', 'Django', 'AWS', 'PostgreSQL', 'Docker'],
        'career_goals': 'Senior Python Backend Engineer'
    }
    
    # Sample Jobs
    jobs = [
        {
            'title': 'Senior Python Developer',
            'company': 'Tech Corp',
            'description': 'We are looking for a Senior Python Developer with strong Django and Cloud experience.',
            'url': 'http://example.com/job1'
        },
        {
            'title': 'Marketing Manager',
            'company': 'Creative Agency',
            'description': 'Leading marketing campaigns and brand strategy.',
            'url': 'http://example.com/job2'
        }
    ]
    
    print(f"\n2️⃣  Testing Matching Logic")
    print(f"   Profile Goal: {profile['career_goals']}")
    
    start_time = time.time()
    
    for i, job in enumerate(jobs):
        print(f"\n   🔸 Matching Job {i+1}: {job['title']}...")
        step_start = time.time()
        
        match_result = matcher.calculate_match(profile, job)
        
        duration = time.time() - step_start
        print(f"      Score: {match_result.total_score}/100")
        print(f"      Semantic Score: {match_result.semantic_score}")
        print(f"      Keyword Score: {match_result.keyword_score}")
        print(f"      Time taken: {duration:.2f}s")
        
        if match_result.total_score > 70:
            print("      ✅ RESULT: High Match (Expected)")
        elif match_result.total_score < 30:
            print("      ✅ RESULT: Low Match (Expected)")
        else:
            print("      ⚠️ RESULT: Medium Match")

    total_time = time.time() - start_time
    print(f"\n3️⃣  Performance Summary")
    print(f"   Total Test Time: {total_time:.2f}s")
    
    if matcher.client:
        # If we used the API, we expect some delay due to rate limiting
        # 2 jobs * 2 embeddings each = 4 calls.
        # Call 1: 0s
        # Call 2: 6s
        # Call 3: 6s
        # Call 4: 6s
        # Total wait ~18s
        if total_time > 15:
            print("   ✅ Rate Limiting Active: Delays observed as expected.")
        else:
            print("   ⚠️ Rate Limiting Check: Faster than expected (Did we hit the cache or fallback?)")
    else:
         print("   ℹ️  Rate Limiting: N/A (Using TF-IDF Fallback)")

    print("\n4️⃣  Verifying Smart Query Logic")
    search_query = profile.get('career_goals', '').split('.')[0]
    if len(search_query) < 5:
        top_skill = (profile.get('skills', []) + ['Developer'])[0]
        exp_level = profile.get('experience_level', '')
        search_query = f"{exp_level} {top_skill}".strip()
    print(f"   Generated Query: '{search_query}'")
    if search_query == "Senior Python Backend Engineer":
        print("   ✅ Query Logic: Correctly used Career Goals.")
    else:
        print(f"   ⚠️ Query Logic: Generated '{search_query}'")

if __name__ == "__main__":
    test_matching()
