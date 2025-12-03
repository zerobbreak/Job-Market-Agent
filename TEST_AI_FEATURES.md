# Testing AI Features Guide

## 🚀 Quick Setup

### Step 1: Set GEMINI_API_KEY in Render

1. Go to your Render dashboard: https://dashboard.render.com
2. Select your service: `job-market-agent`
3. Go to **Environment** tab
4. Add environment variable:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your Google Gemini API key (get it from https://aistudio.google.com/apikey)
5. Click **Save Changes**
6. Render will automatically redeploy your service

### Step 2: Verify API Key is Set

After redeployment, check the logs. You should see:
```
INFO:utils.scraping:Created cache directory: job_cache
```
(No more "GEMINI_API_KEY not set" warning)

---

## 🧪 Testing AI Features

### Base URL
```
https://job-market-agent.onrender.com
```

### Authentication
All endpoints require authentication. You'll need:
1. Register/Login via Appwrite
2. Get JWT token from Appwrite
3. Include in requests: `Authorization: Bearer <token>`

---

## 📋 Available AI Endpoints

### 1. **Analyze CV & Build Profile** (AI-Powered)
**Endpoint**: `POST /api/analyze-cv`

**What it does**: Uses AI to analyze your CV and extract:
- Skills
- Experience level
- Education
- Strengths
- Career goals

**Test with cURL**:
```bash
curl -X POST https://job-market-agent.onrender.com/api/analyze-cv \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "cv=@/path/to/your/cv.pdf"
```

**Expected Response**:
```json
{
  "success": true,
  "session_id": "user_id",
  "profile": {
    "skills": ["Python", "JavaScript", "React", ...],
    "experience_level": "Mid-level (3-5 years)",
    "education": "Bachelor's in Computer Science",
    "strengths": ["Problem solving", "Team leadership", ...],
    "career_goals": "Senior software engineer role..."
  },
  "raw_profile": "Full AI-generated profile text...",
  "cv_filename": "CV.pdf"
}
```

---

### 2. **Match Jobs** (AI-Powered Matching)
**Endpoint**: `POST /api/match-jobs`

**What it does**: Uses AI to:
- Find jobs matching your profile
- Score each job (0-100%)
- Explain why each job matches

**Test with cURL**:
```bash
curl -X POST https://job-market-agent.onrender.com/api/match-jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location": "South Africa",
    "max_results": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "matches": [
    {
      "job": {
        "id": "job_hash",
        "title": "Python Developer",
        "company": "Tech Corp",
        "location": "Cape Town",
        "description": "Job description...",
        "url": "https://..."
      },
      "match_score": 85,
      "match_reasons": [
        "Matches your skills: Python, Django",
        "Mid-level match",
        "Aligns with career goals"
      ]
    }
  ]
}
```

---

### 3. **Search Jobs**
**Endpoint**: `POST /api/search-jobs`

**What it does**: Searches for jobs (note: job scraping is currently disabled)

**Test with cURL**:
```bash
curl -X POST https://job-market-agent.onrender.com/api/search-jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python Developer",
    "location": "South Africa",
    "max_results": 10
  }'
```

---

### 4. **Get Profile**
**Endpoint**: `POST /api/profile`

**What it does**: Retrieves your analyzed profile

**Test with cURL**:
```bash
curl -X POST https://job-market-agent.onrender.com/api/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_user_id"
  }'
```

---

## 🎯 Testing Workflow

### Complete Test Flow:

1. **Upload CV** → Get profile analyzed
   ```bash
   POST /api/analyze-cv
   ```

2. **Match Jobs** → Get AI-powered job recommendations
   ```bash
   POST /api/match-jobs
   ```

3. **View Profile** → See your extracted profile
   ```bash
   POST /api/profile
   ```

---

## 🔍 Testing with Postman/Thunder Client

### Import Collection:

1. Create a new collection
2. Set base URL: `https://job-market-agent.onrender.com`
3. Add environment variable: `{{token}}` = your JWT token
4. Add header to all requests: `Authorization: Bearer {{token}}`

### Test Sequence:

1. **Analyze CV**
   - Method: POST
   - URL: `/api/analyze-cv`
   - Body: form-data
   - Key: `cv` (type: File)
   - Value: Select your CV PDF

2. **Match Jobs**
   - Method: POST
   - URL: `/api/match-jobs`
   - Body: JSON
   ```json
   {
     "location": "South Africa",
     "max_results": 5
   }
   ```

3. **Get Profile**
   - Method: POST
   - URL: `/api/profile`
   - Body: JSON
   ```json
   {
     "session_id": "your_user_id_from_step_1"
   }
   ```

---

## ✅ Success Indicators

### When AI is Working:

1. **CV Analysis**:
   - Returns structured profile data
   - Skills are extracted correctly
   - Experience level is identified
   - No errors in response

2. **Job Matching**:
   - Returns jobs with match scores (0-100)
   - Provides match reasons
   - Scores are relevant to your profile

3. **Logs Show**:
   - No "GEMINI_API_KEY not set" warnings
   - AI agent calls are successful
   - Profile building completes

### When AI is NOT Working:

- Response contains: `"error": "GEMINI_API_KEY not set"`
- Profile data is empty or generic
- Match scores are all 0 or very low
- Logs show API errors

---

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not set"
**Solution**: 
1. Check Render environment variables
2. Ensure key is set correctly (no extra spaces)
3. Redeploy service after adding key

### Issue: "Failed to build profile"
**Solution**:
1. Check API key is valid
2. Verify CV file is readable PDF
3. Check logs for specific error

### Issue: "No jobs found"
**Solution**:
- Job scraping is currently disabled (jobspy not installed)
- This is expected behavior
- AI matching will work once you have jobs from another source

---

## 📊 Expected AI Capabilities

✅ **Working**:
- CV analysis and profile extraction
- Job matching and scoring
- Skill extraction
- Experience level detection

⚠️ **Limited**:
- Job scraping (jobspy not installed)
- Real-time job search

---

## 🎓 Next Steps

1. Set your `GEMINI_API_KEY` in Render
2. Test CV analysis endpoint
3. Verify profile extraction works
4. Test job matching (if you have jobs in database)
5. Check logs for any AI-related errors

---

**Need Help?** Check the logs in Render dashboard for detailed error messages.

