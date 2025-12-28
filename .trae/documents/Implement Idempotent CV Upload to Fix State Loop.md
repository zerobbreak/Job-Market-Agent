# Implement Battle-Tested Idempotent Uploads

The issue is that the "Duplicate CV" check is blocking you from proceeding, even though the profile data might not be loaded in the UI. When you reload, the persistence layer tries to recover, but if it fails or is incomplete, you are forced to re-upload, which then fails because "File already exists". This is a classic "State Loop" trap.

## The Solution: Idempotent Upsert (The "Battle-Tested" Approach)
In distributed systems (like industry-standard microservices), operations should be **idempotent**. This means performing the same operation multiple times has the same result as performing it once.

If you upload a CV that already exists:
-   **Current Behavior**: Error 409 (Conflict) -> User stuck.
-   **New Behavior**: Success 200 OK (with existing data) -> User happy.

The server will recognize the file is identical (via SHA-256 hash) and, instead of complaining, it will say: *"I already have this file. Here is the profile data associated with it."* This immediately "heals" the UI state without wasting AI resources on re-analysis.

## Implementation Plan

### 1. Modify `analyze_cv` in `main.py`
I will change the logic when `file_hash == existing_hash`:
-   Instead of returning an error, I will trigger a **Rehydration** of the profile from the database.
-   I will return a JSON response identical to a successful new upload (`success: True`, `profile`: ...).
-   This allows the frontend to update the dashboard immediately, effectively bypassing the "Upload" screen.

### 2. Verify Persistence
I verified the `_rehydrate_pipeline_from_profile` function in the previous step, and it is now robust. This new change relies on that robustness to serve the data instantly.

### 3. Frontend Impact
No changes needed in the frontend code! The frontend already handles `success: True` by updating the profile context and redirecting. By changing the backend response, the existing frontend code will "just work".

I will apply this change now.
