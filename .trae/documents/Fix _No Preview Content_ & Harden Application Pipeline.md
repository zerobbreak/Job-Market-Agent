# Robust "Apply with AI" & Preview Fix

The "No preview content" issue is caused by the backend generating empty HTML when the AI service fails or returns an invalid response, combined with potential concurrency issues in the new persistence system.

## 1. Backend Resilience (Root Cause Fix)
### A. Strengthen CV Generation Fallback
Modify `utils/cv_tailoring.py` to ensure `generate_tailored_cv` **never** returns empty content.
- If AI generation fails, it will strictly fall back to a structured version of the original CV.
- If the original CV is missing/empty, it will return a "CV Data Missing" placeholder instead of `None`.

### B. Thread-Safe Persistence
Modify `main.py` to add a `threading.Lock()` for the `preview_jobs` and `automation_jobs` dictionaries.
- This prevents `RuntimeError: dictionary changed size during iteration` or race conditions that could corrupt the job state when multiple threads (polling + generation) access the data simultaneously.

### C. Explicit Error Reporting
Update `main.py` to check if the generated HTML is empty.
- If `cv_html` is empty, explicitly set the job status to `error` or inject a "Generation Failed" HTML error page, so the frontend receives actionable information instead of a silent failure.

## 2. Frontend UX Improvements
### A. Retry Capability
Update `ApplicationPreviewDialog.tsx` to:
- Detect if the preview content is missing or indicates an error.
- Show a **"Retry Preview"** button in the dialog footer to allow the user to try again without reloading the page.
- Improve the `iframe` fallback to be more styled and informative.

## 3. Verification
- Verify that disconnecting the AI (simulated failure) still produces a visible (fallback) preview.
- Verify that "Auto-Apply" works even with the fallback content.
