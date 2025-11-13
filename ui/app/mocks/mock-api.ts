import type { CreateJobOptions, Job } from "../../@types/job.types"
import type { LocalStore } from "../services/state/state.client"
import type { StoreAction } from "../services/state/state.types"
import { mockCases as mockJobs } from "./mock-jobs"

/**
 * Initialize the store with mock data for development/testing
 * This function is only used when VITE_USE_MOCK_DATA=true
 */
export const initializeMockData = (store: LocalStore) => {
    console.log("[MockData] Initializing store with mock jobs")

    // Dispatch actions to add mock data
    mockJobs.forEach((jobData) => {
        store.dispatch(store.actions.jobs.addJob(jobData as Job))
        jobData.caseMaterials?.forEach((material) => {
            store.dispatch(store.actions.caseMaterials.add(jobData.id, material))
        })
        if (jobData.uploads && jobData.uploads.length > 0) {
            store.dispatch(store.actions.files.addUploaded(jobData.id, jobData.uploads))
        }
    })

    console.log(`[MockData] Added ${mockJobs.length} mock jobs to store`)
}

/**
 * Mock async function to load cases - simulates API call
 * Returns a function that takes dispatch for compatibility with existing code
 */
export const mockLoadCasesAsync = () => async (dispatch: (action: StoreAction) => void) => {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Import cases dynamically to avoid circular imports
    const { mockCases } = await import("./mock-jobs")

    // Dispatch action to set cases in store
    dispatch({
        type: "JOBS/SET_JOBS",
        payload: mockCases,
    })
}

/**
 * Mock async function to create a case - simulates API call
 * Returns a function that takes dispatch for compatibility with existing code
 */
export const mockCreateCaseAsync =
    (jobData: CreateJobOptions) => async (dispatch: (action: StoreAction) => void) => {
        // Simulate network delay
        await new Promise((resolve) => setTimeout(resolve, 300))

        // Create a new case object
        const newJob = {
            id: `job-${Date.now()}`,
            title: jobData.title || "New Job",
            editedDate: new Date().toISOString(),
            status: "active",
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            jobMaterials: [],
            uploads: [],
        }

        // Dispatch action to add case to store
        dispatch({
            type: "JOBS/ADD_JOB",
            payload: newJob,
        })

        return newJob
    }
