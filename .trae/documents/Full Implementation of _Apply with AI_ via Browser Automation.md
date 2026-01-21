## Objective
Transform the "Apply with AI" feature from a file generator into a **fully functional automated applicant** that interacts with job boards on the user's behalf. This mirrors real-world solutions like Simplify, LazyApply, and massive aggregators.

## Core Solution: Server-Side Browser Automation (Playwright)
Instead of relying on the user to copy-paste, we will implement a backend **Automation Agent** that launches a headless browser, navigates to the job URL, and physically fills the application form using the tailored artifacts.

### 1. Automation Architecture (`agents/browser_automation.py`)
- **Headless Browser Service**: Manage a pool of Playwright instances (Chromium).
- **Site Adapters**: Modular classes to handle different ATS platforms (starting with **Lever** and **Greenhouse** as they have standard DOM structures).
- **Human-in-the-Loop**: Capture screenshots at key steps; if a CAPTCHA or unknown field appears, pause and request user intervention (or fail gracefully).

### 2. Intelligent Field Mapping (`utils/form_filler.py`)
- Upgrade the current heuristic mapper to a robust schema matcher.
- Map complex fields (Education history, Experience arrays) to standard ATS inputs.
- Handle "Yes/No" radio buttons for legal/sponsorship questions using profile defaults.

### 3. Backend API Expansion (`main.py`)
- `POST /api/apply-automation/start`:
  - Accepts `job_id` (from the preview phase).
  - Launches the automation job in a background thread.
  - Returns `automation_id`.
- `GET /api/apply-automation/status`:
  - Returns live logs ("Navigating...", "Uploading CV..."), progress, and a **latest screenshot** (base64) so the user can watch.

### 4. Frontend "Live Terminal" Experience
- Update `ApplicationPreviewDialog` to include an "Auto-Apply (Beta)" button.
- When clicked, switch the view to a "Live Status" mode:
  - Show the live screenshot stream from the backend.
  - Show a log of actions being performed.
  - Final success/failure state.

## Implementation Steps (Phased)

### Phase 1: Infrastructure & Lever Adapter (Immediate)
1.  **Install Playwright**: Add dependency and install browsers.
2.  **Create Automation Agent**: Implement the base `BrowserAutomation` class with error handling and screenshot capture.
3.  **Implement Lever Adapter**: Build the specific logic to fill `lever.co` forms (widely used, easy to test).
    - Selectors for Name, Email, Phone, URLs.
    - File upload handling for CV/Cover Letter.
4.  **Backend Integration**: Wire up the `/apply-automation` endpoints.

### Phase 2: Frontend "Watch Mode"
1.  Add the UI to trigger the automation.
2.  Poll for status and display the "ghost in the machine" working.

### Phase 3: Expansion (Future)
- Add adapters for Greenhouse, Workable, and Indeed.
- Add CAPTCHA solving services (e.g., 2Captcha integration).

## Why this is "Real World"
- **Resilience**: It handles dynamic DOMs, unlike simple HTTP requests.
- **Visibility**: Providing screenshots builds trust (users see the agent working).
- **Control**: `dry_run` mode allows users to review filled forms before the final submit click.

I will begin by implementing **Phase 1**, setting up the automation engine and the Lever adapter, as this provides the highest impact "true apply" capability.