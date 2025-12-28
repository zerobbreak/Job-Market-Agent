# Fix "Blank Screen" in Preview Dialog

The issue is a **ReferenceError** in `ApplicationPreviewDialog.tsx`. The component is trying to access `previewStatus` and `generationError` variables in the JSX, but these variables are **not defined** in the component's scope (they were likely removed or renamed in a previous refactor). This causes React to crash when rendering the dialog, resulting in a blank white area.

## The Solution
I will clean up the `ApplicationPreviewDialog.tsx` component to correctly use the props passed to it (`loading`, `error`) instead of the undefined local variables.

### Implementation Steps
1.  **Edit `ApplicationPreviewDialog.tsx`**:
    -   Replace `previewStatus` with `"Initializing..."` or derived text based on `progress`.
    -   Replace `generationError` with the `error` prop.
    -   Ensure the Cover Letter tab uses the same robust logic as the CV tab.
    -   Add a fallback for `coverLetterHtml` similar to `cvHtml`.

2.  **Verify**:
    -   Reload the page.
    -   Click "Apply with AI".
    -   The dialog should now render the loading state, and then the content (or a specific error message) without crashing.

This is a "Battle-Tested" fix because it removes phantom state and relies on the "Single Source of Truth" (props from the parent hook).
