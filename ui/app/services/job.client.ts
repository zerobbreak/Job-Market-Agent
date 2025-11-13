/**
 * Job Service Module
 *
 * This module handles all client-side logic related to job management.
 * It provides functions for interacting with the backend API to create, retrieve,
 * update, and delete job data. The purpose of this file is to centralize
 * job-related operations, making it easier to maintain and extend functionality.
 */

// Job-related service logic and API interactions
// This file contains the actual implementations for job management operations

import type {
    Case,
    CaseMaterial,
    CreateJobMaterialOptions,
    CreateJobMaterialResult,
    CreateJobOptions,
    CreateJobResult,
    Job,
    JobMaterial,
    UploadedFile,
    UploadFilesOptions,
    UploadFilesResult,
} from "@/types/job.types"
import { withErrorHandling, type ServiceResult } from "~/utils/error-handling"
import {
    extractErrorMessage,
    makeErrorUserFriendly,
    validateAndSanitizeJobTitle,
    validateJobMaterialTitle,
    validateJobMaterialType,
} from "~/utils/validation"
import { localStore } from "./state/state.client"

let jobsInitialized = false

function nowISO(): string {
    return new Date().toISOString()
}

function createSampleJobs(): Case[] {
    const timestamp = nowISO()

    const jobOneId = "job-demo-001"
    const jobTwoId = "job-demo-002"

    const jobOneMaterials: CaseMaterial[] = [
        {
            id: "mat-demo-001",
            jobId: jobOneId,
            type: "cv-rewriter",
            title: "ATS-Optimized Resume Draft",
            description: "Initial optimization pass that aligns the CV with common ATS requirements for senior product managers.",
            createdAt: timestamp,
            updatedAt: timestamp,
            status: "completed",
        },
        {
            id: "mat-demo-002",
            jobId: jobOneId,
            type: "interview-prep-agent",
            title: "Targeted Interview Questions",
            description: "Competency-based questions derived from the job description and company research.",
            createdAt: timestamp,
            updatedAt: timestamp,
            status: "completed",
        },
    ]

    const jobTwoMaterials: CaseMaterial[] = [
        {
            id: "mat-demo-003",
            jobId: jobTwoId,
            type: "cover-letter-specialist",
            title: "Personalized Cover Letter Outline",
            description: "Structured talking points highlighting relevant accomplishments for the role.",
            createdAt: timestamp,
            updatedAt: timestamp,
            status: "completed",
        },
    ]

    return [
        {
            id: jobOneId,
            title: "Optimize CV for Senior Product Manager Role",
            description:
                "Tailor the resume to highlight product strategy, cross-functional leadership, and measurable outcomes for enterprise software.",
            status: "active",
            editedDate: timestamp,
            createdAt: timestamp,
            updatedAt: timestamp,
            jobMaterials: jobOneMaterials,
            sessions_count: 2,
            documents_count: 3,
            uploads: [],
        },
        {
            id: jobTwoId,
            title: "Prepare for Technical Program Manager Interview",
            description:
                "Create interview preparation materials and supporting documents for a TPM role focused on platform migrations.",
            status: "active",
            editedDate: timestamp,
            createdAt: timestamp,
            updatedAt: timestamp,
            jobMaterials: jobTwoMaterials,
            sessions_count: 1,
            documents_count: 1,
            uploads: [],
        },
    ]
}

function initializeMockJobs(): void {
    if (jobsInitialized) return

    const existing = localStore.getCases()
    if (existing.length === 0) {
        const samples = createSampleJobs()
        localStore.dispatch(localStore.actions.jobs.setJobs(samples as Job[]))
    }

    jobsInitialized = true
}

function getCase(jobId: string): Case | null {
    initializeMockJobs()
    return localStore.getCase(jobId)
}

function updateCase(jobId: string, updates: Partial<Case>): void {
    localStore.dispatch(localStore.actions.jobs.updateJob(jobId, updates))
}

export async function getJobs(): Promise<ServiceResult<Job[]>> {
    return withErrorHandling(async () => {
        initializeMockJobs()
        return localStore.getJobs() as Job[]
    }, "getJobs")
}

export async function createJob(
    options: CreateJobOptions,
    _accessToken?: string
): Promise<ServiceResult<CreateJobResult>> {
    return withErrorHandling(async () => {
        initializeMockJobs()

        const titleValidation = validateAndSanitizeJobTitle(options.title)
        if (!titleValidation.isValid) {
            throw new Error(titleValidation.errors.join(", "))
        }

        const jobId = `job-${Date.now()}`
        const timestamp = nowISO()
        const newCase: Case = {
            id: jobId,
            title: titleValidation.sanitized,
            description: options.description ?? "",
            status: "active",
            createdAt: timestamp,
            updatedAt: timestamp,
            editedDate: timestamp,
            jobMaterials: [],
            uploads: [],
            sessions_count: 0,
            documents_count: 0,
        }

        localStore.dispatch(localStore.actions.jobs.addJob(newCase as Job))

        return {
            id: jobId,
            title: newCase.title,
            message: "Job created successfully",
        }
    }, "createJob")
}

export async function deleteJob(jobId: string, _accessToken?: string): Promise<void> {
    initializeMockJobs()
    localStore.dispatch(localStore.actions.jobs.deleteJob(jobId))
}

export async function getJob(jobId: string): Promise<Job | null> {
    const job = getCase(jobId)
    return job ? (job as Job) : null
}

export async function getJobMaterials(jobId: string): Promise<JobMaterial[]> {
    const job = getCase(jobId)
    return job?.jobMaterials ? [...job.jobMaterials] : []
}

export async function createJobMaterial(
    options: CreateJobMaterialOptions
): Promise<CreateJobMaterialResult> {
    try {
        initializeMockJobs()

        const titleValidation = validateJobMaterialTitle(options.title)
        const typeValidation = validateJobMaterialType(options.type)

        if (!titleValidation.isValid) {
            throw new Error(titleValidation.errors.join(", "))
        }

        if (!typeValidation.isValid) {
            throw new Error(typeValidation.errors.join(", "))
        }

        const job = getCase(options.jobId)
        if (!job) {
            throw new Error("Job not found")
        }

        const materialId = options.jobId
            ? `mat-${options.jobId}-${Date.now()}`
            : `mat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
        const timestamp = nowISO()
        const newMaterial: CaseMaterial = {
            id: materialId,
            jobId: options.jobId,
            type: options.type,
            title: options.title.trim(),
            description: options.description?.trim(),
            createdAt: timestamp,
            updatedAt: timestamp,
            status: "processing",
            aiProcessing: true,
        }

        localStore.dispatch(localStore.actions.caseMaterials.add(options.jobId, newMaterial))
        updateCase(options.jobId, { editedDate: timestamp })

        setTimeout(() => {
            localStore.dispatch(
                localStore.actions.caseMaterials.update(options.jobId, materialId, {
                    aiProcessing: false,
                    status: "completed",
                    updatedAt: nowISO(),
                })
            )
        }, 1000)

        return {
            id: newMaterial.id,
            type: newMaterial.type,
            title: newMaterial.title,
            message: "Job material created successfully",
        }
    } catch (error) {
        const errorMessage = extractErrorMessage(error)
        const userFriendlyMessage = makeErrorUserFriendly(errorMessage)
        throw new Error(userFriendlyMessage)
    }
}

export async function uploadJobMaterialFiles(
    jobMaterialId: string,
    files: File[]
): Promise<{ success: boolean; message: string }> {
    initializeMockJobs()

    const owningCase = localStore
        .getCases()
        .find((caseItem) => caseItem.jobMaterials?.some((material) => material.id === jobMaterialId))

    if (!owningCase) {
        throw new Error("Job material not found")
    }

    localStore.dispatch(localStore.actions.caseMaterials.update(owningCase.id, jobMaterialId, {
        files,
        updatedAt: nowISO(),
    }))

    return {
        success: true,
        message: `${files.length} files attached successfully`,
    }
}

export async function uploadJobFiles(options: UploadFilesOptions): Promise<UploadFilesResult> {
    const { jobId, files, onProgress } = options

    if (!jobId) {
        throw new Error(makeErrorUserFriendly("Job ID is required to upload files"))
    }

    initializeMockJobs()

    const job = getCase(jobId)
    if (!job) {
        throw new Error(makeErrorUserFriendly("Job not found"))
    }

    const timestamp = nowISO()
    const uploadedFiles: UploadedFile[] = files.map((file, index) => {
        onProgress?.(file.name, 100)

        return {
            id: `upload-${jobId}-${Date.now()}-${index}`,
            name: file.name,
            size: file.size,
            type: file.type || "application/octet-stream",
            uploadedAt: timestamp,
            status: "completed",
            url: `mock://files/${encodeURIComponent(file.name)}`,
        }
    })

    localStore.dispatch(localStore.actions.files.addUploaded(jobId, uploadedFiles))

    updateCase(jobId, {
        uploads: [...(job.uploads ?? []), ...uploadedFiles],
        documents_count: (job.documents_count ?? 0) + uploadedFiles.length,
        editedDate: timestamp,
        updatedAt: timestamp,
    })

    return {
        uploadedFiles,
        message: `${uploadedFiles.length} file(s) uploaded successfully`,
    }
}

export const getCases = getJobs
export const deleteCase = deleteJob
