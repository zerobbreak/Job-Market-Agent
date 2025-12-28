I will fix the linter errors and diagnostics in the frontend codebase.

1.  **`ApplicationPreviewDialog.tsx`**:
    *   Update `ApplicationPreviewDialogProps` interface to include the missing `error` (string) and `onRetry` (function) properties.
    *   Remove unused imports (`Download`, `useToast`, `apiClient`, etc.).

2.  **`error-boundary.tsx`**:
    *   Refactor imports to use explicit type imports for `ErrorInfo` and `ReactNode` to satisfy `verbatimModuleSyntax`.
    *   Remove the unused default `React` import.

3.  **`useJobApplication.ts`**:
    *   Fix the `toast` variant assignment. Change the unsupported `"warning"` variant to `"default"` (or `"destructive"` if appropriate, but `"default"` is safer based on the allowed types `"success" | "default" | "error"`).

4.  **`MatchedJobs.tsx`**:
    *   Remove unused imports (`Suspense`, `Loader2`).
    *   (The error regarding `ApplicationPreviewDialog` props will be automatically resolved by step 1).