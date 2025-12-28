# Fix Authentication & Preview Generation Issues

The core issue is that the frontend is failing to authenticate requests to the backend (`401 Unauthorized`), which causes the user profile to not load. Without a loaded profile, the preview generation fails (or hangs) because it depends on user data (skills, experience, etc.) to tailor the CV.

## Root Cause Analysis
1.  **Missing/Expired Token**: The `apiClient` in `src/utils/api.ts` attempts to get a JWT from Appwrite (`account.createJWT()`). If this fails (e.g., user session expired or network error), it silently catches the error (`catch (_) {}`) and proceeds *without* a token.
2.  **Backend Enforcement**: The backend endpoints (`/api/profile/structured`, `/api/apply-preview/start`) are protected by `@login_required`. When they receive a request without a valid `Authorization` header, they return `401`.
3.  **Silent Failure**: The frontend catches these `401` errors in some places but doesn't trigger a re-login or clear the stale state, leading to a broken UI state where "Applications" list is empty and "Preview" spins forever or fails.

## Plan

### 1. Fix `apiClient` Auth Handling (`src/utils/api.ts`)
-   Modify `apiClient` to handle the case where `account.createJWT()` fails.
-   Instead of silently continuing, we should probably throw an error or redirect to login if the endpoint requires auth.
-   However, to be robust, we will ensure that if `createJWT` fails, we try to refresh the session or at least log a clear error.

### 2. Update `useJobApplication.ts` to Handle Auth Errors
-   In `initiatePreview`, check if the user is authenticated before calling the API.
-   If the API returns `401`, catch it and show a "Please log in" toast instead of a generic error.

### 3. Backend Profile Fallback (Robustness)
-   In `main.py`, the `@login_required` decorator is strict.
-   I will add a check in the preview generation to ensure that if the user *is* logged in but the profile is missing in the DB, we don't crash but return a helpful error. (The current code already tries to rehydrate, but if auth fails, it never gets there).

### 4. Fix "Applications Not Updating"
-   This is a side effect of the `401`. The `useApplications` (or similar hook fetching the list) is failing. Fixing the auth token injection in `apiClient` will fix this.

## Implementation Steps
1.  **Modify `src/utils/api.ts`**: Improve token retrieval and error handling.
2.  **Modify `src/hooks/useJobApplication.ts`**: Add explicit auth checks and better error messages.
3.  **Verify**: Restart backend and frontend to ensure clean state.
