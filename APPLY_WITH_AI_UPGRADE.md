# Apply with AI Upgrade: Strategic Reframing & Gap Analysis

## Overview
We have upgraded the "Apply with AI" feature to match industry leaders like Teal and Rezi. instead of just "rewriting" the CV, the AI now performs a deep **Strategic Analysis** of the gap between the candidate and the job, and actively reframes experience to bridge that gap.

## Key Changes

### 1. New "ApplicationWriterAgent" Logic
- **Model**: Upgraded to `gemini-2.0-flash-exp` (configurable).
- **Strategy**: Implemented "Match & Pivot" methodology.
- **Output**: Returns a rich JSON object including `strategic_analysis` and `cv_improvements`.

### 2. New Data Structure
The `generate_tailored_cv` method now returns (and stores) the following additional fields in the `cv_versions` map:

```json
{
  "strategic_analysis": {
    "role_type": "Senior Backend Engineer",
    "key_requirements": ["Python", "AWS", "System Design"],
    "candidate_match_level": "High/Medium/Low",
    "gap_strategy": "Emphasized general cloud experience to compensate for lack of specific Azure knowledge."
  },
  "cv_improvements": [
    {
      "type": "quantification",
      "before": "Managed team",
      "after": "Led cross-functional team of 8 engineers",
      "reason": "Added scope and team size"
    },
    {
      "type": "keyword",
      "added": "Microservices",
      "context": "Added to Professional Summary to match JD title"
    }
  ]
}
```

### 3. Frontend Implementation Guide
To fully leverage these upgrades, the Frontend `ApplicationPreviewDialog` should be updated to display:
1.  **The "Gap Strategy"**: Show the user *how* the AI decided to position them (e.g., "We highlighted your Python experience to match the JD").
2.  **Improvement Highlights**: Show a "What Changed" section listing the key keywords and metrics added.
3.  **Match Score**: Display the `ats_score_prediction`.

### 4. Bug Fixes
- Fixed an issue where `GEMINI_API_KEY` was being deleted from the environment, causing authentication failures for the Agent.
