Based on your request and the current state of `CVUpload.tsx`, the most significant "industry standard" missing functionality is **Drag-and-Drop** support. While the UI looks like a dropzone, it currently only supports clicking. Industry leaders (like LinkedIn, Indeed, etc.) universally support drag-and-drop for resume uploads to reduce friction.

I propose refactoring the upload component using **`react-dropzone`**, which is the React ecosystem standard for this functionality.

### **Refactoring Plan: Implement `react-dropzone`**

1.  **Install Dependency**
    *   Install `react-dropzone` in the frontend project.
    *   *Why:* It provides a robust, headless hook (`useDropzone`) that handles cross-browser drag events, file selection, and accessibility automatically.

2.  **Refactor `CVUpload.tsx`**
    *   **Remove**: The manual `label` + hidden `input` hack.
    *   **Implement**: `useDropzone` hook with:
        *   `onDrop`: Connect to your existing `handleCVUpload`.
        *   `accept`: Move the file type validation (`.pdf`, `.doc`, `.docx`) into the hook configuration.
        *   `maxSize`: Move the 10MB limit validation into the hook.
    *   **Visual Feedback**: Add dynamic styling (e.g., blue border/background) when `isDragActive` is true, giving users immediate feedback when they drag a file over the area.

3.  **Verification**
    *   Verify that clicking still opens the file dialog.
    *   Verify that dragging a file onto the box triggers the upload.
    *   Verify that invalid files (wrong type/size) are rejected with your existing toast error messages.

This change will make the CV upload feel professional and modern, matching the "industry leader" experience you requested.
