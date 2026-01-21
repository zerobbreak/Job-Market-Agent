# Fix CV Upload Schema Error

I have identified the root cause of the issue from the logs. The CV upload failed silently (returning 200 OK but logging an error) because of a schema mismatch.

**The Error:**
`ERROR - Failed to save profile to database: Invalid document structure: Unknown attribute: "work_experience"`

**The Cause:**
The `analyze_cv` function is trying to save a field named `work_experience` to the Appwrite database, but the `profiles` collection does not have this attribute defined in its schema. It likely expects `experience` instead (based on my review of the `CVStore` frontend code earlier, which uses `experience`).

**The Solution:**
1.  **Correct the Field Name**: In `routes/profile_routes.py`, change `work_experience` to `experience` (or simply remove it if it's not needed/schema-compliant). I will verify the schema first.
2.  **Verify Schema**: I will check `debug_schema.py` or similar to confirm the correct attribute name.
3.  **Improve Error Handling**: The backend caught the error but returned `200 OK` (success=True) because the exception handling block for "Save profile to database" just logged the error and continued. I will make it return an error to the frontend so the user knows the upload failed.

## Plan Steps
1.  **Verify Schema**: Run a script to list the actual attributes of the `profiles` collection to confirm if it's `experience` or `work_experience`.
2.  **Fix `profile_routes.py`**:
    *   Rename `work_experience` to the correct attribute name.
    *   Update the error handling to return `500` if saving to the DB fails (don't silently fail).
3.  **Restart Backend**: Apply changes and restart.
4.  **Verification**: Ask you to upload the CV again.

## Why this fixes "Old CV is active"
Since the new CV upload failed to save to the database, the system naturally only showed the old one. Once we fix the save error, the new CV will appear and be set to active automatically by the logic I added in the previous step.
