import {
    DocumentArrowUpIcon,
    DocumentTextIcon,
    MagnifyingGlassIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline"
import { useRef, useState } from "react"
import type { UploadedFile } from "@/types/job.types"
import { ErrorBoundary } from "~/components/ui/error-boundary"
import { uploadJobFiles } from "~/services/job.client"
import { withErrorHandling } from "~/utils/error-handling"

interface JobUploadAreaProps {
    jobId: string
    uploads: UploadedFile[]
    accessToken: string
    onFilesUploaded?: (files: UploadedFile[]) => void
    onFileRemoved?: (fileId: string) => void
}

// Action Cards Component - moved outside to avoid nested component definition
const ActionCards = () => (
    <div className="flex gap-6 justify-center mt-12">
        {/* Generate Facts Card */}
        <div className="bg-white border border-[#edebe5] rounded-xl p-6 hover:bg-[#f7f4ed] transition-colors cursor-pointer min-w-[280px]">
            <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-[#f7f4ee] rounded-lg flex items-center justify-center">
                    <DocumentTextIcon className="w-5 h-5 text-[#7a7a7a]" />
                </div>
                <h3 className="text-lg font-medium text-[#151515]">Generate Facts</h3>
            </div>
            <p className="text-sm text-[#7a7a7a]">Summarise key points with source references.</p>
        </div>

        {/* Research Case Law Card */}
        <div className="bg-white border border-[#edebe5] rounded-xl p-6 hover:bg-[#f7f4ed] transition-colors cursor-pointer min-w-[280px]">
            <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 bg-[#f7f4ee] rounded-lg flex items-center justify-center">
                    <MagnifyingGlassIcon className="w-5 h-5 text-[#7a7a7a]" />
                </div>
                <h3 className="text-lg font-medium text-[#151515]">Research Case Law</h3>
            </div>
            <p className="text-sm text-[#7a7a7a]">Find precedents and judgments that apply.</p>
        </div>
    </div>
)

// File validation constants
const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
const ALLOWED_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/tiff",
]

// File validation function
const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
        return `File "${file.name}" is too large. Maximum size is 50MB.`
    }
    if (!ALLOWED_TYPES.includes(file.type)) {
        return `File type "${file.type}" is not supported for "${file.name}". Please upload PDF, Word, Excel, PowerPoint, text files, or images.`
    }
    return null
}

// Format file size for display
const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${Number.parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`
}

// Get file icon based on type
const getFileIcon = (fileName: string): string => {
    const ext = fileName.split(".").pop()?.toLowerCase()
    switch (ext) {
        case "pdf":
            return "📄"
        case "doc":
        case "docx":
            return "📝"
        case "xls":
        case "xlsx":
            return "📊"
        case "ppt":
        case "pptx":
            return "📈"
        case "txt":
            return "📝"
        case "jpg":
        case "jpeg":
        case "png":
        case "gif":
        case "bmp":
        case "tiff":
            return "🖼️"
        default:
            return "📎"
    }
}

function JobUploadAreaContent({
    jobId,
    uploads,
    accessToken,
    onFilesUploaded,
    onFileRemoved,
}: JobUploadAreaProps) {
    const [isDragOver, setIsDragOver] = useState(false)
    const [_dragCounter, setDragCounter] = useState(0)
    const [uploadingFiles, setUploadingFiles] = useState<UploadedFile[]>([])
    const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
    const [validationErrors, setValidationErrors] = useState<string[]>([])
    const removingFilesRef = useRef<Set<string>>(new Set())

    const handleFileSelect = async (files: FileList) => {
        const fileArray = Array.from(files)

        // Validate files first
        const errors: string[] = []
        const validFiles: File[] = []

        for (const file of fileArray) {
            const validationError = validateFile(file)
            if (validationError) {
                errors.push(validationError)
            } else {
                validFiles.push(file)
            }
        }

        // Show validation errors if any
        if (errors.length > 0) {
            setValidationErrors(errors)
            // Clear errors after 5 seconds
            setTimeout(() => setValidationErrors([]), 5000)
            return
        }

        // Clear any previous errors
        setValidationErrors([])

        // Set initial progress for valid files
        const progressMap = Object.fromEntries(validFiles.map((file) => [file.name, 0]))
        setUploadProgress(progressMap)

        // Add files to uploading state
        const uploadingFileObjects: UploadedFile[] = validFiles.map((file) => ({
            id: `uploading-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            name: file.name,
            size: file.size,
            type: file.type,
            uploadedAt: new Date().toISOString(),
            status: "uploading" as const,
        }))
        setUploadingFiles((prev) => [...prev, ...uploadingFileObjects])

        const result = await withErrorHandling(
            () =>
                uploadJobFiles({
                    jobId,
                    files: validFiles,
                    accessToken,
                    onProgress: (fileName, progress) => {
                        setUploadProgress((prev) => ({ ...prev, [fileName]: progress }))
                    },
                }),
            "CaseUploadArea.handleFileSelect"
        )

        // Clear progress and uploading files
        setUploadProgress({})
        setUploadingFiles((prev) =>
            prev.filter((f) => !uploadingFileObjects.some((uf) => uf.id === f.id))
        )

        if (result.success && result.data) {
            // Files successfully uploaded
            onFilesUploaded?.(result.data.uploadedFiles)
        } else {
            console.error("Failed to upload files:", result.error?.message)
            const errorMessage = result.error?.message || "Failed to upload files"
            setValidationErrors([errorMessage])
            // Clear errors after 5 seconds
            setTimeout(() => setValidationErrors([]), 5000)
        }
    }

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault()
        setDragCounter(0)
        setIsDragOver(false)
        const files = e.dataTransfer.files
        if (files.length > 0) {
            handleFileSelect(files)
        }
    }

    const handleDragEnter = (e: React.DragEvent) => {
        e.preventDefault()
        setDragCounter((prev) => prev + 1)
        setIsDragOver(true)
    }

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault()
        setDragCounter((prev) => {
            const newCounter = prev - 1
            if (newCounter === 0) {
                setIsDragOver(false)
            }
            return newCounter
        })
    }

    const handleClick = () => {
        const input = document.createElement("input")
        input.type = "file"
        input.multiple = true
        input.accept =
            ".pdf,.doc,.docx,.txt,.rtf,.odt,.png,.jpg,.jpeg,.gif,.bmp,.tiff,.xls,.xlsx,.ppt,.pptx"
        input.onchange = (e) => {
            const files = (e.target as HTMLInputElement).files
            if (files && files.length > 0) {
                handleFileSelect(files)
            }
        }
        input.click()
    }

    // Removed formatFileSize as it's not used in icon-only display

    const removeFile = (fileId: string) => {
        // Prevent duplicate removal attempts
        if (removingFilesRef.current.has(fileId)) {
            return
        }

        // Check if file exists before attempting removal
        const fileExists =
            uploads.some((f) => f.id === fileId) || uploadingFiles.some((f) => f.id === fileId)
        if (!fileExists) {
            return
        }

        // Mark file as being removed
        removingFilesRef.current.add(fileId)

        // In development mode, all files go directly to uploads prop
        // So we always use the parent callback to remove files
        onFileRemoved?.(fileId)

        // Also remove from local uploadingFiles state just in case
        setUploadingFiles((prev) => prev.filter((f) => f.id !== fileId))

        // Clean up the removing flag after a short delay
        setTimeout(() => {
            removingFilesRef.current.delete(fileId)
        }, 100)
    }

    // Render based on whether files exist or not
    const hasFiles = uploads.length > 0 || uploadingFiles.length > 0

    // Display validation errors
    const renderErrors = () => {
        if (validationErrors.length === 0) return null

        return (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg max-w-4xl mx-auto">
                <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-5 h-5 text-red-400 mt-0.5">⚠️</div>
                    <div className="flex-1">
                        <h4 className="text-sm font-medium text-red-800 mb-2">
                            Upload Error{validationErrors.length > 1 ? "s" : ""}
                        </h4>
                        <ul className="text-sm text-red-700 space-y-1">
                            {validationErrors.map((error) => (
                                <li key={error}>• {error}</li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        )
    }

    if (!hasFiles) {
        // No uploads state - centered drop zone matching the design
        return (
            <div className="flex flex-col items-center justify-center text-center relative">
                {renderErrors()}
                {/* Main drop zone with column-reverse layout and 8px gap like the design */}
                {/* biome-ignore lint/a11y/useSemanticElements: Div required for drag-and-drop file upload functionality */}
                <div
                    className={`flex flex-col-reverse items-center gap-4 p-20 transition-all duration-200 ${
                        isDragOver
                            ? "bg-[#f7f4ed] border-[#4b92ff] shadow-lg scale-[1.02]"
                            : "bg-transparent hover:bg-[#f7f4ed] hover:border-[#4b92ff]"
                    } border-2 border-dashed border-transparent rounded-2xl cursor-pointer min-w-[800px] min-h-[300px]`}
                    role="button"
                    tabIndex={0}
                    onDrop={handleDrop}
                    onDragEnter={handleDragEnter}
                    onDragLeave={handleDragLeave}
                    onClick={handleClick}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") handleClick()
                    }}
                >
                    {/* Drop zone text - positioned above the icon in column-reverse */}
                    <div className="text-center">
                        <p className="text-2xl text-[#7a7a7a] mb-4">
                            Drop any files here to start a new case
                        </p>
                        <h2 className="text-4xl font-medium text-[#151515]">Drop files here</h2>
                        <p className="text-lg text-[#7a7a7a] mt-4">Select multiple files at once</p>
                    </div>

                    {/* File icon - positioned below text in column-reverse */}
                    <div className="w-16 h-16 text-[#151515] mb-6">
                        <DocumentArrowUpIcon className="w-full h-full" />
                    </div>
                </div>

                {/* Action Cards */}
                <ActionCards />
            </div>
        )
    }

    // Has files state - show upload area with file list matching the design
    return (
        <div className="flex flex-col items-center justify-center text-center relative">
            {renderErrors()}
            {/* Main container with column-reverse layout and 8px gap like the design */}
            {/* biome-ignore lint/a11y/useSemanticElements: Div required for drag-and-drop file upload functionality */}
            <div
                className={`flex flex-col-reverse items-center gap-4 p-16 transition-all duration-200 ${
                    isDragOver
                        ? "bg-[#f7f4ed] border-[#4b92ff] shadow-lg scale-[1.02]"
                        : "bg-transparent hover:bg-[#f7f4ed] hover:border-[#4b92ff]"
                } border-2 border-dashed border-transparent rounded-2xl cursor-pointer min-w-[700px] min-h-[200px]`}
                role="button"
                tabIndex={0}
                onDrop={handleDrop}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onClick={handleClick}
                onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") handleClick()
                }}
            >
                {/* Drop zone text - positioned above the icon in column-reverse */}
                <div className="text-center mb-8">
                    <p className="text-xl text-[#7a7a7a] mb-4">
                        Drop any files here to add more files
                    </p>
                    <h2 className="text-3xl font-medium text-[#151515]">Drop files here</h2>
                    <p className="text-lg text-[#7a7a7a] mt-4">Select multiple files at once</p>
                </div>

                {/* File icon - positioned below text in column-reverse */}
                <div className="w-14 h-14 text-[#151515] mb-6">
                    <DocumentArrowUpIcon className="w-full h-full" />
                </div>
            </div>

            {/* Files row - horizontal layout with file details */}
            <div className="mt-8 space-y-4">
                {/* Uploading files */}
                {uploadingFiles.length > 0 && (
                    <div className="max-w-4xl mx-auto">
                        <h3 className="text-sm font-medium text-[#151515] mb-3 flex items-center gap-2">
                            <div className="w-4 h-4 bg-blue-400 rounded-full flex items-center justify-center">
                                <div className="w-2 h-2 border border-white border-t-transparent rounded-full animate-spin" />
                            </div>
                            Uploading Files
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {uploadingFiles.map((file, index) => {
                                const progress = uploadProgress[file.name] || 0
                                return (
                                    <div
                                        key={`${file.id}-${index}`}
                                        className="flex items-center gap-3 p-3 bg-[#f7f4ee] rounded-lg border border-[#edebe5]"
                                    >
                                        <div className="flex-shrink-0">
                                            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center border border-[#edebe5]">
                                                <span className="text-lg">
                                                    {getFileIcon(file.name)}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <p
                                                    className="text-sm font-medium text-[#151515] truncate"
                                                    title={file.name}
                                                >
                                                    {file.name}
                                                </p>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.preventDefault()
                                                        e.stopPropagation()
                                                        removeFile(file.id)
                                                    }}
                                                    className="flex-shrink-0 ml-2 w-6 h-6 bg-white rounded-full flex items-center justify-center hover:bg-[#edebe5] transition-colors border border-[#edebe5]"
                                                    title="Cancel upload"
                                                >
                                                    <XMarkIcon className="w-3 h-3 text-[#7a7a7a]" />
                                                </button>
                                            </div>
                                            <p className="text-xs text-[#7a7a7a]">
                                                {formatFileSize(file.size)}
                                            </p>
                                            <div className="mt-2">
                                                <div className="w-full bg-white rounded-full h-1.5">
                                                    <div
                                                        className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                                                        style={{ width: `${progress}%` }}
                                                    />
                                                </div>
                                                <p className="text-xs text-[#7a7a7a] mt-1">
                                                    {progress}%
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                )}

                {/* Completed uploads */}
                {uploads.length > 0 && (
                    <div className="max-w-4xl mx-auto">
                        <h3 className="text-sm font-medium text-[#151515] mb-3 flex items-center gap-2">
                            <div className="w-4 h-4 bg-green-500 rounded-full flex items-center justify-center">
                                <div className="w-2 h-2 bg-white rounded-full" />
                            </div>
                            Uploaded Files ({uploads.length})
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {uploads.map((file, index) => (
                                <div
                                    key={`${file.id}-${index}`}
                                    className="flex items-center gap-3 p-3 bg-[#f7f4ee] rounded-lg border border-[#edebe5] hover:bg-[#f7f4ed] transition-colors"
                                >
                                    <div className="flex-shrink-0">
                                        <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center border border-[#edebe5]">
                                            <span className="text-lg">
                                                {getFileIcon(file.name)}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <p
                                                className="text-sm font-medium text-[#151515] truncate"
                                                title={file.name}
                                            >
                                                {file.name}
                                            </p>
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.preventDefault()
                                                    e.stopPropagation()
                                                    removeFile(file.id)
                                                }}
                                                className="flex-shrink-0 ml-2 w-6 h-6 bg-white rounded-full flex items-center justify-center hover:bg-[#edebe5] transition-colors border border-[#edebe5]"
                                                title="Remove file"
                                            >
                                                <XMarkIcon className="w-3 h-3 text-[#7a7a7a]" />
                                            </button>
                                        </div>
                                        <p className="text-xs text-[#7a7a7a]">
                                            {formatFileSize(file.size)}
                                        </p>
                                        <p className="text-xs text-[#7a7a7a]">
                                            Uploaded{" "}
                                            {new Date(file.uploadedAt).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Action Cards */}
            <ActionCards />
        </div>
    )
}

export function JobUploadArea(props: JobUploadAreaProps) {
    return (
        <ErrorBoundary
            fallback={
                <div className="p-4 border border-red-200 bg-red-50 rounded-lg">
                    <h3 className="penpot-body-medium font-medium mb-2">Upload Error</h3>
                    <p className="text-red-600 text-sm">
                        Something went wrong with the file upload area.
                    </p>
                </div>
            }
        >
            <CaseUploadAreaContent {...props} />
        </ErrorBoundary>
    )
}
