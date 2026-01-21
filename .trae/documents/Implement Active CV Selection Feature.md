# Implementation Plan: Battle-Tested "Active CV" Management

I have analyzed the "Active CV" issue and identified that while the system supports multiple CV uploads, it lacks the mechanism to explicitly select which one is "active" for job applications. It currently defaults to the first one found, which is why your changes aren't taking effect.

## 1. Industry Analysis & Battle-Tested Solutions
**The Problem**: "State Stickiness" - users upload a new document, but the system continues using the old one because the selection logic is implicit (first-found) rather than explicit.

**Top 3 Real-World Solutions**:
1.  **Explicit "Active/Default" Flag (The Winner)**: Used by **LinkedIn** and **Indeed**. You have a library of resumes, but one is marked as "Default" for Quick Apply. This is robust and transparent.
2.  **Session-Based Selection**: Used by **Greenhouse/Lever** application portals. You select the CV *at the time of application*. Good for tailoring, but adds friction.
3.  **Most Recently Used (MRU)**: The last uploaded/edited CV becomes active. Used by simple job boards. Prone to errors if you view an old CV and it accidentally becomes active.

**Chosen Solution**: **Explicit "Active" Flag**. This provides the most control and clarity for the user, preventing accidental submissions of the wrong CV.

## 2. Implementation Steps

### Phase 1: Backend Core (Python)
We will implement an explicit `is_active` field in the database logic.
*   **Update `get_current_profile`**: Modify the query to prioritize `is_active=true` profiles.
*   **New Endpoint `PUT /api/profile/<id>/active`**:
    *   Transactionally sets the target profile to `active=true`.
    *   Sets all other profiles for the user to `active=false`.
*   **Update Upload Logic**: Ensure newly uploaded CVs are automatically marked as active.

### Phase 2: Frontend Integration (React)
We will update the UI to visualize and control this state.
*   **Update Types**: Add `is_active` to the `CVProfile` interface.
*   **Service Layer**: Add `setActive(id)` to `cv.service.ts`.
*   **CVList Component**:
    *   Add a visual "Active" badge to the current CV.
    *   Add a "Make Active" button to other CVs.
    *   Sort the list to show the Active CV at the top.

### Phase 3: Verification
*   Upload multiple CVs.
*   Toggle the "Active" status between them.
*   Verify that the "Current Profile" endpoint returns the correct CV after switching.
