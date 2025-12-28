I will implement a **"Self-Healing" Data Retrieval Pattern** (also known as Read-Repair) to solve the issue where profile data is missing even after the CV loads.

### The Problem
The current `get_structured_profile` endpoint purely reads from the database. If the database record was created before the schema update (missing `name`, `email` columns) or if the save failed partially, the API returns empty fields. The system "knows" the data (it's in the CV PDF) but isn't using it to fill the gaps.

### The Solution: Read-Repair Strategy
I will modify the `get_structured_profile` endpoint in `main.py` to:
1.  **Check for Missing Data**: When fetching the profile, check if critical fields (Name, Email, Location) are empty.
2.  **On-Demand Rehydration**: If they are empty, automatically trigger the `_rehydrate_pipeline_from_profile` function. This function downloads the CV file and re-runs the AI/Parser to extract the data on the fly.
3.  **Auto-Heal (Write-Back)**: Once the data is re-extracted, **immediately update the database record** with these missing fields. This ensures that subsequent loads are fast and correct.

### Impact
*   **Immediate Fix**: Users with existing "broken" profiles will see them instantly fixed upon reload.
*   **Robustness**: If a future save fails, the next read will auto-correct it.
*   **No Frontend Changes**: The frontend will simply receive the complete data it expects.

### Implementation Steps
1.  Update `get_structured_profile` in `main.py` to include the healing logic.
2.  Restart the backend.
