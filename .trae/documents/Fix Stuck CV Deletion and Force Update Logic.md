# Fix CV Delete & Upload Restoration Logic

I understand the two issues you are facing:
1.  **Cannot Delete**: You cannot delete the "ghost" CV entry. This is likely because the backend delete endpoint fails when it tries to delete the non-existent storage file (which throws an error and aborts the database deletion).
2.  **"Restored" instead of Updated**: When you re-upload a CV, the system detects it's the same file (via hash) and "restores" the old profile data instead of creating a new one. This prevents you from fixing the broken state.

## Plan

### 1. Fix Delete Logic (Backend)
I will modify `delete_profile` in `routes/profile_routes.py` to be more resilient.
*   **Current Behavior**: If `storage.delete_file` fails (e.g., file not found), the code might be stopping or throwing an exception that prevents the subsequent `databases.delete_document` call.
*   **Fix**: Wrap the storage deletion in a `try/except` block that *logs* the error but **continues** to delete the database record. This ensures that even if the file is missing (ghost entry), the database record gets removed.

### 2. Fix Upload "Restore" Logic (Backend)
I will modify `analyze_cv` in `routes/profile_routes.py`.
*   **Current Behavior**: It calculates a file hash. If a profile with that hash exists, it says "Idempotent upload detected - rehydrating profile" and returns the old data.
*   **Fix**:
    *   If the user provides the `overwrite=true` flag (which the frontend usually sends on "Replace"), we should **force** a re-analysis.
    *   However, since you are uploading a "new" file that happens to be the same content, the system thinks it's a duplicate.
    *   I will verify that the "idempotent check" logic respects the `overwrite` flag. If `overwrite` is true, it should bypass the restoration and process the file as new.

### 3. Frontend Check
*   Ensure the frontend sends `overwrite=true` when necessary (though the backend fix for deletion is the primary solution for the "ghost" file).

## Execution Steps
1.  **Modify `delete_profile`**: Ensure database deletion happens even if storage deletion fails.
2.  **Review `analyze_cv`**: Ensure duplicate hash detection doesn't block updates when we want to force them.
3.  **Restart Backend**: Apply changes.
