export interface JobMaterial {
    id: string
    type: "ats-optimizer" | "cv-rewriter" | "cover-letter-specialist" | "interview-copilot" | "interview-prep-agent" | "notes" | "research"
    title: string
    description?: string
    content?: string
    files?: File[]
    aiProcessing?: boolean
    status?: "active" | "processing" | "completed" | "error"
    createdAt: string
    updatedAt: string
    jobId: string
}

export interface Job {
    id: string
    title: string
    editedDate: string
    status?: "active" | "draft" | "archived"
    jobMaterials?: JobMaterial[]
    uploads?: UploadedFile[]
    createdAt?: string
    updatedAt?: string
    description?: string
    job_type?: "full-time" | "part-time" | "contract" | "freelance" | "internship" | "temporary" | "other"
    sessions_count?: number
    documents_count?: number
    last_activity?: string
}

export interface UploadedFile {
    id: string
    name: string
    size: number
    type: string
    uploadedAt: string
    status: "uploading" | "completed" | "error"
    url?: string
    error?: string
}

export interface CreateJobOptions {
    title: string
    description?: string
}

export interface CreateJobMaterialOptions {
    jobId: string
    type: "ats-optimizer" | "cv-rewriter" | "cover-letter-specialist" | "interview-copilot" | "interview-prep-agent" | "notes" | "research"
    title: string
    description?: string
}

export interface CreateJobResult {
    id: string
    title: string
    message: string
}

export interface CreateJobMaterialResult {
    id: string
    type: string
    title: string
    message: string
}

export interface UploadFilesOptions {
    jobId: string
    files: File[]
    accessToken?: string
    onProgress?: (fileName: string, progress: number) => void
}

export interface UploadFilesResult {
    uploadedFiles: UploadedFile[]
    message: string
}

export type Case = Job
export type CaseMaterial = JobMaterial
