# Fix 401 Unauthorized on Download

I have resolved the 401 Unauthorized error by implementing the **Short-Lived Token (OTP) Pattern**, a battle-tested enterprise solution for secure file downloads.

### **The Problem**
The previous download method used `window.location.href`, which sends a standard GET request. Browsers do **not** attach the `Authorization: Bearer <token>` header to these requests, causing the backend to reject them with a 401 Unauthorized error.

### **The Solution: Secure OTP Flow**
I implemented a 2-step secure download process that is standard among industry leaders (e.g., Dropbox, Slack, Enterprise SaaS):

1.  **Request OTP**: The frontend calls a new authenticated endpoint `/api/auth/otp` using the existing Bearer token.
2.  **Generate Token**: The backend verifies the user and generates a short-lived (30-second), single-use UUID token linked to the user's session.
3.  **Redirect with Token**: The frontend redirects the browser to the download URL, appending the OTP as a query parameter: `?token=<otp>`.
4.  **Validate & Stream**: The backend's `@login_required` decorator intercepts the request, validates the OTP, restores the user session, and allows the download to proceed.

### **Benefits**
*   **Security**: The token is short-lived and single-use, minimizing leak risks.
*   **Performance**: Uses native browser download manager (streaming) instead of loading the entire file into memory (Blob), which prevents crashes with large files.
*   **User Experience**: Provides proper progress indicators and native "Save As" dialogs.

### **Implementation Details**
*   **Backend (`main.py`)**:
    *   Added `otp_store` (in-memory) and `otp_lock` for thread safety.
    *   Updated `@login_required` to accept `token` query parameter.
    *   Added `/api/auth/otp` endpoint.
*   **Frontend (`ApplicationPreviewDialog.tsx`)**:
    *   Refactored `handleDownload` to fetch OTP first.
    *   Redirects to `downloadUrl` with the token.
    *   Added error handling and Toast notifications.
*   **Frontend (`ApplicationsList.tsx`)**:
    *   Fixed a crash (`TypeError`) where `fileUrl` could be undefined.
    *   Added null checks and error feedback.
