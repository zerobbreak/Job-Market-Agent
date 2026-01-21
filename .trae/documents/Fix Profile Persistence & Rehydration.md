# Fix Profile Persistence Issues

The issue is that profile data is not persisting correctly, leading to the "Welcome to Job Market" screen reappearing even after a CV has been uploaded.

## Root Cause
In `main.py`, specifically the `analyze_cv` function, there is a section where we attempt to save the profile to Appwrite. While there is retry logic for the Appwrite operation itself, there's a critical flaw in how we handle the `pipeline_store` and `profile_store`.

1.  **In-Memory Store vs. Database**: The application relies heavily on `pipeline_store` (in-memory) for subsequent requests like `match_jobs`. If the server restarts (which happens frequently in dev), this memory is wiped.
2.  **Rehydration Logic**: Although there is a `_rehydrate_pipeline_from_profile` function, it seems it might not be getting called correctly or failing silently if the Appwrite session/token handling is slightly off, or if the `cv_file_id` isn't properly linked.
3.  **Frontend State**: The frontend might not be refetching the profile on load if it thinks it's already authenticated but the backend session is fresh (empty memory).

## Plan

### 1. Robust Database Persistence (Backend)
-   I will review the `analyze_cv` function in `main.py` to ensure that after a successful CV upload, the profile data is **definitely** committed to the Appwrite database with all necessary fields (`cv_file_id`, `cv_filename`, etc.).
-   I will verify that `_rehydrate_pipeline_from_profile` is robust enough to rebuild the `CVTailoringEngine` state purely from the database record + file storage, without relying on the upload happening in the same session.

### 2. Frontend Profile Fetching
-   The frontend should attempt to fetch the current profile (`/api/profile/current` or similar) when the user lands on the dashboard or profile page. If this returns 404, *then* show the upload screen. If it returns success, load the profile.
-   I will check `Job-Market-Frontend/src/hooks/useProfile.ts` (or similar) to ensure it handles the "profile exists but needs loading" state correctly.

### 3. "Real World" Persistence Fix
-   **Problem**: `profile_store` is just a global Python dict.
-   **Solution**: We will treat the Appwrite Database as the source of truth.
-   In `match_jobs` and other endpoints, if `session_id` is not in `pipeline_store`, we **must** force a rehydration attempt from the DB before giving up. I will verify this logic is airtight in `main.py`.

## Implementation Steps
1.  **Modify `main.py`**: Enhance `_rehydrate_pipeline_from_profile` to be more aggressive in logging errors and trying to recover.
2.  **Modify `analyze_cv`**: Ensure the "profile updated" state is correctly returned to the frontend.
3.  **Frontend Check**: (If needed) Update the frontend to poll for profile status on init.

I will start by hardening `main.py`'s rehydration logic, as that is the single point of failure for "disappearing" profiles across server restarts.
