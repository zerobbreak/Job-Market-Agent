I have identified the root cause of the "download still isn't working" issue.

### **The Problem**
1.  **Critical Bug in `ApplicationPreviewDialog.tsx`:**
    *   The code uses `const { toast: show } = useToast();`.
    *   The `useToast` hook returns an object `{ show, remove, toasts }`, but **does not** have a `toast` property.
    *   This makes `show` `undefined`, causing the `TypeError: show is not a function` crash when trying to display notifications (including error messages).
2.  **Masked Error:** Because the error notification system itself was crashing, the actual reason for any download failure (if any) was hidden.

### **The Solution**
I will fix the destructuring in `ApplicationPreviewDialog.tsx` to correctly extract the `show` function.

**Plan:**
1.  **Modify `ApplicationPreviewDialog.tsx`:**
    *   Change: `const { toast: show } = useToast();`
    *   To: `const { show } = useToast();`
2.  **Verify:** This will stop the crash. If the download authorization (OTP) works, you will see a "Success" toast. If it fails, you will now properly see the "Download Failed" error message instead of a white screen/crash.

This aligns with the "Battle-Tested" OTP solution we already implemented; we just need to unblock the UI logic to let it run.
