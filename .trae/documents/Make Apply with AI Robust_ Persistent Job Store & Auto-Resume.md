## Root Cause Analysis
- The backend's in-memory job store (`preview_jobs = {}`) is cleared every time the dev server (`main.py`) auto-reloads.
- The dev server reloads frequently when files are modified or when the filesystem is touched (e.g., creating temporary files or log files).
- The client (frontend) holds a `job_id` from the initial request and polls `/status`.
- After a reload, the new server instance receives the poll request, checks its empty `preview_jobs`, and returns `Invalid job_id`, breaking the flow.
- The 5% progress corresponds to the initial "running" state before any heavy lifting, which confirms the job starts but gets lost mid-flight.

## Solution Plan: Persistent Job State & Robust Execution
To make "Apply with AI" fully functional and resilient to restarts, we need to move job state out of volatile memory and into a persistent store (file-based for simplicity in this setup, or database).

### 1. Persistent Job Store (File-Based)
- **Goal**: Ensure job metadata survives server restarts.
- **Implementation**:
  - Create a local directory `preview_jobs_data/` (added to `.gitignore`).
  - When a job starts (`/start`), save its state (status, progress, user_id, job_payload) to `preview_jobs_data/<job_id>.json`.
  - Update this JSON file whenever progress changes (5%, 25%, 50%, etc.).
  - Modify `/status` endpoint:
    - First check in-memory `preview_jobs`.
    - If missing, check `preview_jobs_data/<job_id>.json`.
    - If found on disk but not in memory (implies restart), **auto-resume** the job in a new thread if it was incomplete.

### 2. Job Resume Logic
- **Goal**: Automatically restart processing for interrupted jobs.
- **Implementation**:
  - In `apply_preview_status`, if loading from disk shows `status='running'` or `'queued'`, re-spawn the `_run_preview_job` thread with the saved payload.
  - This ensures the heavy AI work (CV tailoring) continues even after a server blip.

### 3. Frontend Polling Hardening
- **Goal**: Handle transient errors gracefully.
- **Implementation**:
  - In `useJobApplication.ts`, if `/status` returns 404/400 (Invalid ID) *once*, verify if it's a permanent failure.
  - (The backend fix is the primary solver here, but the frontend can be more patient).
  - Add a "Retry" button in the UI if it truly fails, rather than just closing the dialog.

### 4. Full Functional Verification
- **Test Case**:
  1. Start "Apply with AI" preview.
  2. While it spins (at 5% or 25%), manually kill/restart `main.py` or trigger a reload (touch file).
  3. Verify the frontend continues polling.
  4. Verify the backend picks up the job from disk and resumes processing.
  5. Verify the preview eventually renders (100%).

## Steps to Execute
1.  **Modify `main.py`**:
    - Add `_save_preview_job(job_id, data)` and `_load_preview_job(job_id)` helpers.
    - Update `apply_preview_start` to write initial state to disk.
    - Update `_run_preview_job` to write progress updates to disk at every step.
    - Update `apply_preview_status` to fallback to disk load and trigger resume if needed.
2.  **Verify Frontend**:
    - Ensure `useJobApplication.ts` handles the response correctly (already done, but verify timeout settings).
3.  **Clean Up**:
    - Add a cleanup routine to delete old JSON files from `preview_jobs_data/` (older than 1 hour).

This approach makes the feature "production-grade" in terms of reliability, solving the "Invalid job_id" issue definitively.