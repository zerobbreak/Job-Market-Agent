/**
 * Mock file upload simulation
 */
export const mockFileUpload = async (files: File[], caseId: string) => {
    // Simulate upload delay
    await new Promise((resolve) => setTimeout(resolve, 1000 + Math.random() * 2000))

    const uploadedFiles = files.map((file, index) => ({
        id: `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${index}`,
        name: file.name,
        size: file.size,
        type: file.type || "application/octet-stream",
        uploadedAt: new Date().toISOString(),
        caseId,
        status: Math.random() > 0.1 ? ("completed" as const) : ("uploading" as const), // 90% success rate
        url: `/mock-files/${file.name.replace(/[^a-zA-Z0-9.]/g, "_")}`,
    }))

    return { uploadedFiles, errors: [] }
}
