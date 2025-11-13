import { DocumentArrowUpIcon, XMarkIcon } from "@heroicons/react/24/outline"
import { useRef, useState } from "react"

interface FileUploadProps {
    onFilesUploaded?: (files: File[]) => void
    onQuickAction?: (action: "generate-facts" | "research-law") => void
}

interface UploadingFile {
    id: string
    file: File
    progress: number
    status: "uploading" | "completed" | "error"
    error?: string
}

export function FileUpload({ onFilesUploaded, onQuickAction }: FileUploadProps) {
    const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([])
    const [isDragOver, setIsDragOver] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const handleFileSelect = (files: FileList) => {
        // Validate file types
        const allowedTypes = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "image/png",
            "image/jpeg",
        ]
        const maxFileSize = 10 * 1024 * 1024 // 10MB

        const validatedFiles = Array.from(files).map((file) => {
            let status: "uploading" | "completed" | "error" = "uploading"
            let error: string | undefined

            // Check file type
            if (!allowedTypes.includes(file.type)) {
                status = "error"
                error = "Invalid file type. Please upload PDF, DOC, DOCX, TXT, or image files."
            }
            // Check file size
            else if (file.size > maxFileSize) {
                status = "error"
                error = "File size exceeds 10MB limit."
            }

            return {
                id: Math.random().toString(36).substr(2, 9),
                file,
                progress: 0,
                status,
                error,
            }
        })

        setUploadingFiles((prev) => [...prev, ...validatedFiles])

        // Process valid files
        const validFiles = validatedFiles.filter((f) => f.status === "uploading")

        validFiles.forEach((uploadingFile) => {
            const interval = setInterval(() => {
                setUploadingFiles((prev) =>
                    prev.map((f) =>
                        f.id === uploadingFile.id
                            ? {
                                  ...f,
                                  progress: Math.min(f.progress + Math.random() * 30, 100),
                              }
                            : f
                    )
                )
            }, 200)

            setTimeout(
                () => {
                    clearInterval(interval)
                    // Simulate occasional upload failures
                    const shouldFail = Math.random() < 0.1 // 10% failure rate
                    setUploadingFiles((prev) =>
                        prev.map((f) =>
                            f.id === uploadingFile.id
                                ? {
                                      ...f,
                                      progress: shouldFail ? f.progress : 100,
                                      status: shouldFail ? "error" : "completed",
                                      error: shouldFail
                                          ? "Upload failed. Network error occurred."
                                          : undefined,
                                  }
                                : f
                        )
                    )
                },
                2000 + Math.random() * 1000
            )
        })

        // Call callback with successfully uploaded files
        if (validFiles.length > 0) {
            onFilesUploaded?.(validFiles.map((f) => f.file))
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
        const files = e.dataTransfer.files
        if (files.length > 0) {
            handleFileSelect(files)
        }
    }

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(true)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        setIsDragOver(false)
    }

    const handleClick = () => {
        fileInputRef.current?.click()
    }

    const removeFile = (id: string) => {
        setUploadingFiles((prev) => prev.filter((f) => f.id !== id))
    }

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return "0 Bytes"
        const k = 1024
        const sizes = ["Bytes", "KB", "MB", "GB"]
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return `${Number.parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`
    }

    return (
        <div className="space-y-4">
            {/* Centered Upload Area - matching Penpot design */}
            <div className="flex flex-col items-center justify-center min-h-[400px] relative">
                {/* Main Upload Area */}
                {/* biome-ignore lint/a11y/useSemanticElements: Div required for drag-and-drop file upload functionality */}
                <div
                    className={`w-full max-w-2xl mx-auto transition-colors ${
                        isDragOver ? "bg-[#f7f4ed]" : "bg-[#f7f5f2]"
                    } border border-[#edebe5] rounded-lg shadow-[0px_4px_4px_0px_rgba(237,235,229,0.2)] p-12 text-center`}
                    role="button"
                    tabIndex={0}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={handleClick}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") handleClick()
                    }}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
                        className="hidden"
                        onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
                    />

                    {/* Large Upload Icon */}
                    <div className="mx-auto w-16 h-16 mb-6 text-[#7a7a7a]">
                        <DocumentArrowUpIcon className="w-full h-full" />
                    </div>

                    {/* Main Title */}
                    <h3 className="penpot-heading-large mb-4 text-[#151515]">Drop files here</h3>

                    {/* Subtitle */}
                    <p className="penpot-body-large text-[#7a7a7a] mb-8">
                        Drop any files here to start a new case
                    </p>

                    {/* Click to Upload Button */}
                    <button type="button" className="penpot-button-primary">
                        Choose Files
                    </button>

                    {/* Action Cards - positioned at bottom INSIDE the upload area */}
                    <div className="mt-16 pt-8 border-t border-[#edebe5]">
                        <div className="flex gap-6 justify-center">
                            {/* biome-ignore lint/a11y/useSemanticElements: Div needed for card styling and layout consistency */}
                            <div
                                className="penpot-card p-6 w-64 text-center hover:shadow-md transition-shadow cursor-pointer"
                                role="button"
                                tabIndex={0}
                                onClick={() => onQuickAction?.("generate-facts")}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" || e.key === " ")
                                        onQuickAction?.("generate-facts")
                                }}
                            >
                                <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <DocumentArrowUpIcon className="w-6 h-6 text-blue-600" />
                                </div>
                                <h4 className="penpot-heading-medium mb-2">Generate Facts</h4>
                                <p className="penpot-caption">
                                    Summarise key points with source references.
                                </p>
                            </div>

                            {/* biome-ignore lint/a11y/useSemanticElements: Div needed for card styling and layout consistency */}
                            <div
                                className="penpot-card p-6 w-64 text-center hover:shadow-md transition-shadow cursor-pointer"
                                role="button"
                                tabIndex={0}
                                onClick={() => onQuickAction?.("research-law")}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" || e.key === " ")
                                        onQuickAction?.("research-law")
                                }}
                            >
                                <div className="w-12 h-12 bg-pink-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg
                                        className="w-6 h-6 text-pink-600"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        role="img"
                                        aria-label="Research"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                        />
                                    </svg>
                                </div>
                                <h4 className="penpot-heading-medium mb-2">Research Case Law</h4>
                                <p className="penpot-caption">
                                    Find precedents and judgments that apply.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Uploading Files List */}
            {uploadingFiles.length > 0 && (
                <div className="space-y-3">
                    <h4 className="penpot-heading-medium">Uploading Files</h4>
                    {uploadingFiles.map((uploadingFile) => (
                        <div key={uploadingFile.id} className="penpot-card p-4">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-[#f7f4ee] rounded-lg flex items-center justify-center">
                                        <DocumentArrowUpIcon className="w-4 h-4 text-[#7a7a7a]" />
                                    </div>
                                    <div>
                                        <p className="penpot-body-medium">
                                            {uploadingFile.file.name}
                                        </p>
                                        <p className="penpot-caption">
                                            {formatFileSize(uploadingFile.file.size)}
                                        </p>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => removeFile(uploadingFile.id)}
                                    className="p-1 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#f7f4ee] transition-colors"
                                >
                                    <XMarkIcon className="w-4 h-4" />
                                </button>
                            </div>

                            {/* Progress Bar */}
                            <div className="w-full bg-[#edebe5] rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full transition-all duration-300 ${
                                        uploadingFile.status === "completed"
                                            ? "bg-green-500"
                                            : uploadingFile.status === "error"
                                              ? "bg-red-500"
                                              : "bg-[#4b92ff]"
                                    }`}
                                    style={{ width: `${uploadingFile.progress}%` }}
                                />
                            </div>

                            <div className="flex items-center justify-between mt-2">
                                <span className="penpot-caption">
                                    {uploadingFile.progress.toFixed(0)}%
                                </span>
                                <span className="penpot-caption">
                                    {uploadingFile.status === "completed" && "Completed"}
                                    {uploadingFile.status === "uploading" && "Uploading..."}
                                    {uploadingFile.status === "error" && "Failed"}
                                </span>
                            </div>

                            {/* Error Message */}
                            {uploadingFile.status === "error" && uploadingFile.error && (
                                <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
                                    <p className="penpot-caption text-red-600">
                                        {uploadingFile.error}
                                    </p>
                                    <button
                                        type="button"
                                        onClick={() => removeFile(uploadingFile.id)}
                                        className="penpot-caption text-red-600 hover:text-red-800 underline mt-1"
                                    >
                                        Remove file
                                    </button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
