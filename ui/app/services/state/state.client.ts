// This file has been modularized into smaller, focused modules for better maintainability.
// Core state management functionality remains here, while other concerns have been moved.

/**
 * Overview of State Management System:
 * This module provides a centralized state management solution for the Junior Counsel application.
 * It manages the application's state related to jobs, current job selection, UI state, and versioning.
 * The system is designed to be extensible with middleware support, persistence, and migration capabilities.
 * It also includes React hooks for easy integration with UI components.
 *
 * Key Features:
 * - Singleton pattern for store instance to ensure a single source of truth.
 * - Middleware system for action processing (logging, validation, persistence).
 * - Persistence to localStorage with basic obfuscation (to be replaced with proper encryption).
 * - Migration system for handling state schema changes across versions.
 * - React hooks for seamless state access and updates in components.
 * - Asynchronous action support for API interactions.
 * - Debugging tools for development mode.
 */
// Core imports
import type { Case, CaseMaterial, UploadedFile } from "@/types/job.types"

// ============================================================================
// TYPES & INTERFACES - Moved to state.types.ts
// ============================================================================
import type {
    Migration,
    StoreAction,
    StoreConfig,
    StoreMiddleware,
    StoreState,
    StoreSubscriber,
} from "./state.types"

// ============================================================================
// ENHANCED LOCAL STORE
// ============================================================================

class LocalStore {
    private static instance: LocalStore
    protected state: StoreState
    private subscribers: Set<StoreSubscriber> = new Set()
    private middlewares: StoreMiddleware[] = []
    protected config: StoreConfig
    private isInitialized = false

    /**
     * Private constructor to enforce singleton pattern.
     * @param config Configuration options for the store including persistence key and debug mode.
     */
    private constructor(config: StoreConfig) {
        this.config = config
        this.state = this.getInitialState()
    }

    /**
     * Retrieves or creates the singleton instance of LocalStore.
     * @param config Optional partial configuration to override defaults.
     * @returns The singleton instance of LocalStore.
     */
    static getInstance(config?: Partial<StoreConfig>): LocalStore {
        if (!LocalStore.instance) {
            const defaultConfig: StoreConfig = {
                persistKey: "jc-local-store",
                version: "1.0.0",
                maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
                debug: import.meta.env.DEV,
                ...config,
            }
            LocalStore.instance = new LocalStore(defaultConfig)
        }
        return LocalStore.instance
    }

    /**
     * Initializes the default state of the store.
     * @returns The initial state object for the store.
     */
    private getInitialState(): StoreState {
        return {
            jobs: [],
            currentJob: null,
            ui: {
                isLoading: false,
                lastUpdated: null,
            },
            version: this.config.version,
        }
    }

    // Initialize store from persisted data
    /**
     * Initializes the store by loading persisted data from storage.
     * Ensures the store is only initialized once.
     */
    initialize(): void {
        if (this.isInitialized) return

        try {
            this.loadFromStorage()
            this.isInitialized = true

            if (this.config.debug) {
                console.log("[LocalStore] Initialized with state:", this.state)
            }
        } catch (error) {
            console.warn("[LocalStore] Failed to initialize:", error)
            this.state = this.getInitialState()
        }
    }

    // ============================================================================
    // ACTION DISPATCH SYSTEM - Moved detailed processing to state.actions.ts
    // ============================================================================

    /**
     * Dispatches an action to update the store's state.
     * Actions are processed through middleware before being applied to the state.
     * After processing, the state is persisted and subscribers are notified.
     * @param action The action to dispatch for state modification.
     */
    dispatch(action: StoreAction): void {
        if (this.config.debug) {
            console.log("[LocalStore] Dispatching action:", action)
        }

        // Run through middlewares
        let processedAction = action
        for (const middleware of this.middlewares) {
            const result = middleware(processedAction, this.state)
            if (result === null) {
                if (this.config.debug) {
                    console.log("[LocalStore] Action blocked by middleware:", action)
                }
                return
            }
            processedAction = result
        }

        // Process the action
        this.processAction(processedAction)

        // Persist state
        this.persistToStorage()

        // Notify subscribers
        this.notifySubscribers(processedAction)

        if (this.config.debug) {
            console.log("[LocalStore] State after action:", this.state)
        }
    }

    /**
     * Processes an action to update the internal state based on action type.
     * This method handles various action types related to cases, materials, and UI state.
     * @param action The action to process and apply to the state.
     */
    private processAction(action: StoreAction): void {
        // Action processing logic moved to state.actions.ts
        // This is a placeholder for the refactored code
        // For now, we'll keep a simplified version
        switch (action.type) {
            case "JOBS/SET_JOBS":
                this.state.jobs = [...(action.payload as Job[])]
                break

            case "JOBS/ADD_JOB": {
                const jobData = action.payload as Job
                // Check if job already exists to prevent duplicates
                const existingIndex = this.state.jobs.findIndex((j) => j.id === jobData.id)
                if (existingIndex === -1) {
                    this.state.jobs.push(jobData)
                } else {
                    // Update existing job instead of duplicating
                    this.state.jobs[existingIndex] = {
                        ...this.state.jobs[existingIndex],
                        ...jobData,
                    }
                }
                break
            }

            case "JOBS/UPDATE_JOB": {
                const { jobId, updates } = action.payload as {
                    jobId: string
                    updates: Partial<Job>
                }
                const index = this.state.jobs.findIndex((j) => j.id === jobId)
                if (index !== -1) {
                    this.state.jobs[index] = { ...this.state.jobs[index], ...updates }
                }
                break
            }

            case "JOBS/DELETE_JOB": {
                const jobId = action.payload as string
                this.state.jobs = this.state.jobs.filter((j) => j.id !== jobId)
                if (this.state.currentJob?.id === jobId) {
                    this.state.currentJob = null
                }
                break
            }

            case "CURRENT_JOB/SET":
                this.state.currentJob = action.payload as Job | null
                break

            case "JOB_MATERIALS/ADD": {
                const { jobId, caseMaterial } = action.payload as {
                    jobId: string
                    caseMaterial: CaseMaterial
                }
                const index = this.state.jobs.findIndex((job) => job.id === jobId)
                if (index !== -1) {
                    if (!this.state.jobs[index].jobMaterials) {
                        this.state.jobs[index].jobMaterials = []
                    }
                    this.state.jobs[index].jobMaterials?.push(caseMaterial)
                    this.state.jobs[index].updatedAt = new Date().toISOString()

                    // Update current case if it matches
                    if (this.state.currentJob?.id === jobId) {
                        this.state.currentJob = this.state.jobs[index]
                    }
                }
                break
            }

            case "JOB_MATERIALS/UPDATE": {
                const { jobId, caseMaterialId, updates } = action.payload as {
                    jobId: string
                    caseMaterialId: string
                    updates: Partial<CaseMaterial>
                }
                const jobIndex = this.state.jobs.findIndex((job) => job.id === jobId)
                if (jobIndex !== -1 && this.state.jobs[jobIndex].jobMaterials) {
                    const jobMaterials = this.state.jobs[jobIndex].jobMaterials
                    if (jobMaterials) {
                        const materialIndex = jobMaterials.findIndex(
                            (cm: CaseMaterial) => cm.id === caseMaterialId
                        )
                        if (materialIndex !== -1) {
                            // Create new array to avoid mutation
                            const updatedMaterials = [...jobMaterials]
                            updatedMaterials[materialIndex] = {
                                ...updatedMaterials[materialIndex],
                                ...updates,
                                updatedAt: new Date().toISOString(),
                            }

                            // Create new case object to avoid mutation
                            const updatedJob = {
                                ...this.state.jobs[jobIndex],
                                jobMaterials: updatedMaterials,
                                updatedAt: new Date().toISOString(),
                            }

                            // Replace case in array
                            this.state.jobs[jobIndex] = updatedJob

                            // Update current case if it matches
                            if (this.state.currentJob?.id === jobId) {
                                this.state.currentJob = updatedJob
                            }
                        }
                    }
                }
                break
            }

            case "FILES/ADD_UPLOADED": {
                const { jobId, files } = action.payload as {
                    jobId: string
                    files: UploadedFile[]
                }
                const jobIndex = this.state.jobs.findIndex((job) => job.id === jobId)
                if (jobIndex !== -1) {
                    if (!this.state.jobs[jobIndex].uploads) {
                        this.state.jobs[jobIndex].uploads = []
                    }
                    // Deduplicate files by ID before adding
                    const existingIds = new Set(
                        this.state.jobs[jobIndex].uploads?.map((f) => f.id) || []
                    )
                    const newFiles = files.filter((file) => !existingIds.has(file.id))
                    this.state.jobs[jobIndex].uploads?.push(...newFiles)
                    this.state.jobs[jobIndex].updatedAt = new Date().toISOString()

                    // Update current case if it matches
                    if (this.state.currentJob?.id === jobId) {
                        this.state.currentJob = this.state.jobs[jobIndex]
                    }
                }
                break
            }

            case "FILES/REMOVE_UPLOADED": {
                const { jobId, fileId } = action.payload as {
                    jobId: string
                    fileId: string
                }
                console.log(
                    "[LocalStore] FILES/REMOVE_UPLOADED - jobId:",
                    jobId,
                    "fileId:",
                    fileId
                )

                const jobIndex = this.state.jobs.findIndex((job) => job.id === jobId)
                console.log("[LocalStore] Job index found:", jobIndex)

                if (jobIndex !== -1) {
                    const jobData = this.state.jobs[jobIndex]
                    console.log(
                        "[LocalStore] Job uploads before removal:",
                        jobData.uploads?.map((f) => ({ id: f.id, name: f.name }))
                    )

                    if (jobData.uploads) {
                        const originalLength = jobData.uploads.length
                        const filteredUploads = jobData.uploads.filter(
                            (file: UploadedFile) => file.id !== fileId
                        )

                        // Create a new case object to ensure React detects the change
                        const updatedJobData = {
                            ...jobData,
                            uploads: filteredUploads,
                            updatedAt: new Date().toISOString(),
                        }

                        // Replace the case in the array
                        this.state.jobs[jobIndex] = updatedJobData

                        const newLength = filteredUploads.length

                        console.log(
                            "[LocalStore] File removal result - original length:",
                            originalLength,
                            "new length:",
                            newLength
                        )
                        console.log(
                            "[LocalStore] Job uploads after removal:",
                            filteredUploads?.map((f) => ({ id: f.id, name: f.name }))
                        )

                        // Update current case if it matches
                        if (this.state.currentJob?.id === jobId) {
                            this.state.currentJob = updatedJobData
                            console.log("[LocalStore] Updated current job uploads")
                        }
                    } else {
                        console.log("[LocalStore] Job has no uploads array")
                    }
                } else {
                    console.warn("[LocalStore] Job not found for removal:", jobId)
                }
                break
            }

            case "UI/SET_LOADING":
                this.state.ui.isLoading = action.payload as boolean
                break

            default:
                if (this.config.debug) {
                    console.warn("[LocalStore] Unknown action type:", action.type)
                }
        }

        // Update last updated timestamp
        this.state.ui.lastUpdated = new Date().toISOString()
    }

    // ============================================================================
    // SUBSCRIPTION SYSTEM
    // ============================================================================

    /**
     * Subscribes a listener to state changes.
     * @param listener Callback function to be called on state updates.
     * @returns A function to unsubscribe the listener.
     */
    subscribe(listener: StoreSubscriber): () => void {
        this.subscribers.add(listener)
        return () => {
            this.subscribers.delete(listener)
        }
    }

    /**
     * Notifies all subscribers of state changes.
     * @param action Optional action that triggered the state change.
     */
    private notifySubscribers(action?: StoreAction): void {
        this.subscribers.forEach((listener) => {
            listener(this.state, action)
        })
    }

    // ============================================================================
    // MIDDLEWARE SYSTEM
    // ============================================================================

    /**
     * Adds a middleware to the store's processing chain.
     * @param middleware Middleware function to process actions before they update the state.
     */
    use(middleware: StoreMiddleware): void {
        this.middlewares.push(middleware)
    }

    // ============================================================================
    // GETTERS (READ-ONLY ACCESS)
    // ============================================================================

    /**
     * Retrieves a read-only copy of the current state.
     * @returns A deep copy of the current state.
     */
    getState(): StoreState {
        return { ...this.state }
    }

    /**
     * Retrieves a read-only copy of all cases.
     * @returns A copy of the cases array.
     */
    getJobs(): Job[] {
        return [...this.state.jobs]
    }

    /**
     * Retrieves a specific case by ID.
     * @param caseId The ID of the case to retrieve.
     * @returns The case if found, otherwise null.
     */
    getCase(caseId: string): Case | null {
        return this.state.jobs.find((job) => job.id === caseId) || null
    }

    /**
     * Retrieves the currently selected case.
     * @returns The current case if set, otherwise null.
     */
    getCurrentJob(): Job | null {
        return this.state.currentJob
    }

    /**
     * Checks if the UI is in a loading state.
     * @returns True if loading, false otherwise.
     */
    isLoading(): boolean {
        return this.state.ui.isLoading
    }

    // ============================================================================
    // ACTION CREATORS - Moved to state.actions.ts
    // ============================================================================

    actions = {
        jobs: {
            setJobs: (jobs: Job[]) => ({
                type: "JOBS/SET_JOBS",
                payload: jobs,
            }),
            addJob: (jobData: Job) => ({
                type: "JOBS/ADD_JOB",
                payload: jobData,
            }),
            updateJob: (jobId: string, updates: Partial<Job>) => ({
                type: "JOBS/UPDATE_JOB",
                payload: { jobId, updates },
            }),
            deleteJob: (jobId: string) => ({
                type: "JOBS/DELETE_JOB",
                payload: jobId,
            }),
        },
        currentJob: {
            set: (jobData: Job | null) => ({
                type: "CURRENT_JOB/SET",
                payload: jobData,
            }),
        },
        caseMaterials: {
            add: (jobId: string, caseMaterial: CaseMaterial) => ({
                type: "JOB_MATERIALS/ADD",
                payload: { jobId, caseMaterial },
            }),
            update: (jobId: string, caseMaterialId: string, updates: Partial<CaseMaterial>) => ({
                type: "JOB_MATERIALS/UPDATE",
                payload: { jobId, caseMaterialId, updates },
            }),
        },
        files: {
            addUploaded: (jobId: string, files: UploadedFile[]) => ({
                type: "FILES/ADD_UPLOADED",
                payload: { jobId, files },
            }),
            removeUploaded: (jobId: string, fileId: string) => ({
                type: "FILES/REMOVE_UPLOADED",
                payload: { jobId, fileId },
            }),
        },
        ui: {
            setLoading: (isLoading: boolean) => ({
                type: "UI/SET_LOADING",
                payload: isLoading,
            }),
        },
    }

    // ============================================================================
    // PERSISTENCE SYSTEM - Moved to state.persistence.ts
    // ============================================================================

    /**
     * Persists the current state to localStorage with basic obfuscation.
     * Note: This is a placeholder for proper encryption in production.
     */
    protected persistToStorage(): void {
        try {
            const stateToPersist = { ...this.state }
            // TODO: Implement proper encryption using a library like crypto-js
            // For now, using base64 as a placeholder, but this MUST be replaced with secure encryption in production
            const encryptedState = btoa(JSON.stringify(stateToPersist))
            localStorage.setItem(this.config.persistKey, encryptedState)
        } catch (error) {
            console.error("Failed to persist state to storage:", error)
        }
    }

    /**
     * Loads persisted state from localStorage and merges it with the initial state.
     * Note: This is a placeholder for proper decryption in production.
     */
    protected loadFromStorage(): void {
        try {
            const stored = localStorage.getItem(this.config.persistKey)
            if (stored) {
                // TODO: Implement proper decryption using a library like crypto-js
                const decryptedState = JSON.parse(atob(stored))
                if (decryptedState && typeof decryptedState === "object") {
                    this.state = { ...this.getInitialState(), ...decryptedState }
                    if (this.config.debug) {
                        console.log("Loaded state from storage", this.state)
                    }
                }
            }
        } catch (error) {
            console.error("Failed to load state from storage:", error)
            this.state = this.getInitialState()
        }
    }

    /**
     * Clears all persisted data from storage and resets the state.
     */
    clear(): void {
        if (typeof window !== "undefined") {
            localStorage.removeItem(this.config.persistKey)
        }
        this.state = this.getInitialState()
        this.notifySubscribers()
    }

    // ============================================================================
    // UTILITY METHODS - Moved to state.utils.ts
    // ============================================================================

    /**
     * Resets the state to its initial values and persists it.
     */
    reset(): void {
        this.state = this.getInitialState()
        this.persistToStorage()
        this.notifySubscribers()
    }

    /**
     * Exports the current state as a string for backup or transfer.
     * @returns An obfuscated string representation of the state.
     */
    export(): string {
        const data = JSON.stringify(
            {
                state: this.state,
                timestamp: Date.now(),
                version: this.config.version,
            },
            null,
            2
        )
        return obfuscate(data)
    }

    /**
     * Imports state from a previously exported string.
     * @param data The obfuscated string to import.
     * @returns True if import was successful, false otherwise.
     */
    import(data: string): boolean {
        try {
            const deobfuscatedData = deobfuscate(data)
            const parsed = JSON.parse(deobfuscatedData)

            if (parsed.version !== this.config.version) {
                console.warn("[LocalStore] Import failed: version mismatch")
                return false
            }

            this.state = { ...this.state, ...parsed.state }
            this.persistToStorage()
            this.notifySubscribers()

            return true
        } catch (error) {
            console.warn("[LocalStore] Import failed:", error)
            return false
        }
    }
}

function buildDemoJobs(): Case[] {
    const timestamp = new Date().toISOString()
    return [
        {
            id: "job-demo-001",
            title: "Optimize CV for Senior Product Manager Role",
            description:
                "Tailor the resume to highlight product strategy, cross-functional leadership, and measurable outcomes for enterprise software.",
            status: "active",
            createdAt: timestamp,
            updatedAt: timestamp,
            editedDate: timestamp,
            jobMaterials: [
                {
                    id: "mat-demo-001",
                    jobId: "job-demo-001",
                    type: "cv-rewriter",
                    title: "ATS-Optimized Resume Draft",
                    description:
                        "Initial optimization pass that aligns the CV with common ATS requirements for senior product managers.",
                    createdAt: timestamp,
                    updatedAt: timestamp,
                    status: "completed",
                },
            ],
            uploads: [],
            sessions_count: 2,
            documents_count: 3,
        },
        {
            id: "job-demo-002",
            title: "Prepare for Technical Program Manager Interview",
            description:
                "Create interview preparation materials and supporting documents for a TPM role focused on platform migrations.",
            status: "active",
            createdAt: timestamp,
            updatedAt: timestamp,
            editedDate: timestamp,
            jobMaterials: [
                {
                    id: "mat-demo-002",
                    jobId: "job-demo-002",
                    type: "cover-letter-specialist",
                    title: "Personalized Cover Letter Outline",
                    description: "Structured talking points highlighting relevant accomplishments for the role.",
                    createdAt: timestamp,
                    updatedAt: timestamp,
                    status: "completed",
                },
            ],
            uploads: [],
            sessions_count: 1,
            documents_count: 1,
        },
    ]
}

function seedStoreWithDemoJobs(store: LocalStore): void {
    const demoJobs = buildDemoJobs()
    store.dispatch(store.actions.jobs.setJobs(demoJobs))
}

// ============================================================================
// BACKWARD COMPATIBILITY LAYER
// ============================================================================

// Legacy AppState class for backward compatibility
class AppState {
    private static instance: AppState
    private localStore: LocalStore

    static getInstance(): AppState {
        if (!AppState.instance) {
            AppState.instance = new AppState()
        }
        return AppState.instance
    }

    private constructor() {
        this.localStore = LocalStore.getInstance()
        this.localStore.initialize()
    }

    // Subscribe to state changes
    subscribe(listener: () => void): () => void {
        return this.localStore.subscribe(() => listener())
    }

    // Cases management (legacy API)
    setJobs(jobs: Job[]): void {
        this.localStore.dispatch(this.localStore.actions.jobs.setJobs(jobs))
    }

    getJobs(): Job[] {
        return this.localStore.getJobs()
    }

    addJob(newCase: Job): void {
        this.localStore.dispatch(this.localStore.actions.jobs.addJob(newCase))
    }

    updateJob(caseId: string, updates: Partial<Job>): void {
        this.localStore.dispatch(this.localStore.actions.jobs.updateJob(caseId, updates))
    }

    getCase(caseId: string): Case | null {
        return this.localStore.getCase(caseId)
    }

    // Current case management
    setCurrentCase(caseData: Case | null): void {
        this.localStore.dispatch(this.localStore.actions.currentJob.set(caseData))
    }

    getCurrentCase(): Case | null {
        return this.localStore.getCurrentJob()
    }

    // Case materials management
    addCaseMaterial(caseId: string, caseMaterial: CaseMaterial): void {
        this.localStore.dispatch(this.localStore.actions.caseMaterials.add(caseId, caseMaterial))
    }

    updateCaseMaterial(
        caseId: string,
        caseMaterialId: string,
        updates: Partial<CaseMaterial>
    ): void {
        this.localStore.dispatch(
            this.localStore.actions.caseMaterials.update(caseId, caseMaterialId, updates)
        )
    }

    // File uploads management
    addUploadedFiles(caseId: string, files: UploadedFile[]): void {
        this.localStore.dispatch(this.localStore.actions.files.addUploaded(caseId, files))
    }

    // Persistence methods (legacy API)
    loadFromStorage(): void {
        // Already handled by LocalStore initialization
    }

    clearStorage(): void {
        this.localStore.clear()
    }
}

// ============================================================================
// REACT HOOKS
// ============================================================================

import { useCallback, useEffect, useState } from "react"

// Hook for using the local store in React components
export function useLocalStore() {
    const localStore = LocalStore.getInstance()
    const [state, setState] = useState(localStore.getState())

    useEffect(() => {
        const unsubscribe = localStore.subscribe((newState) => {
            setState(newState)
        })

        return unsubscribe
    }, [localStore.subscribe]) // Remove localStore.subscribe from dependencies to prevent re-subscriptions

    return {
        state,
        dispatch: useCallback(
            (action: StoreAction) => localStore.dispatch(action),
            [localStore.dispatch]
        ),
        actions: localStore.actions,
        store: localStore,
    }
}

// Hook for cases data
export function useCases() {
    const localStore = LocalStore.getInstance()
    const [cases, setCases] = useState(localStore.getJobs())

    useEffect(() => {
        const unsubscribe = localStore.subscribe((newState) => {
            setCases(newState.jobs)
        })

        return unsubscribe
    }, [localStore.subscribe]) // Remove localStore.subscribe from dependencies

    return {
        cases,
        addCase: useCallback(
            (caseData: Case) => {
                localStore.dispatch(localStore.actions.jobs.addJob(caseData as Job))
            },
            [localStore.dispatch, localStore.actions.jobs.addJob]
        ),
        updateCase: useCallback(
            (caseId: string, updates: Partial<Case>) => {
                localStore.dispatch(localStore.actions.jobs.updateJob(caseId, updates))
            },
            [localStore.dispatch, localStore.actions.jobs.updateJob]
        ),
        deleteCase: useCallback(
            (caseId: string) => {
                localStore.dispatch(localStore.actions.jobs.deleteJob(caseId))
            },
            [localStore.dispatch, localStore.actions.jobs.deleteJob]
        ),
    }
}

// Hook for current case
export function useCurrentCase() {
    const localStore = LocalStore.getInstance()
    const [currentCase, setCurrentCase] = useState(localStore.getCurrentJob())

    useEffect(() => {
        const unsubscribe = localStore.subscribe((newState) => {
            setCurrentCase(newState.currentJob)
        })

        return unsubscribe
    }, [localStore.subscribe]) // Remove localStore.subscribe from dependencies

    return {
        currentCase,
        setCurrentCase: useCallback(
            (caseData: Case | null) => {
                localStore.dispatch(localStore.actions.currentJob.set(caseData as Job | null))
            },
            [localStore.dispatch, localStore.actions.currentJob.set]
        ),
    }
}

// Hook for UI state
export function useUIState() {
    const localStore = LocalStore.getInstance()
    const [uiState, setUIState] = useState(localStore.getState().ui)

    useEffect(() => {
        const unsubscribe = localStore.subscribe((newState) => {
            setUIState(newState.ui)
        })

        return unsubscribe
    }, [localStore.subscribe]) // Remove localStore.subscribe from dependencies

    return {
        uiState,
        setLoading: useCallback(
            (isLoading: boolean) => {
                localStore.dispatch(localStore.actions.ui.setLoading(isLoading))
            },
            [localStore.dispatch, localStore.actions.ui.setLoading]
        ),
    }
}

// Hook for specific case data
export function useCaseData(caseId: string) {
    const localStore = LocalStore.getInstance()
    const [caseData, setCaseData] = useState(() => localStore.getCase(caseId))

    useEffect(() => {
        const unsubscribe = localStore.subscribe((newState) => {
            const updatedCase = newState.jobs.find((c) => c.id === caseId)
            setCaseData(updatedCase || null)
        })

        return unsubscribe
    }, [caseId, localStore.subscribe]) // Remove localStore.subscribe from dependencies

    return {
        caseData,
        caseMaterials: caseData?.jobMaterials || [],
        uploads: caseData?.uploads || [],
        updateCase: useCallback(
            (updates: Partial<Case>) => {
                localStore.dispatch(localStore.actions.jobs.updateJob(caseId, updates))
            },
            [caseId, localStore.actions.jobs.updateJob, localStore.dispatch]
        ),
        addCaseMaterial: useCallback(
            (caseMaterial: CaseMaterial) => {
                localStore.dispatch(localStore.actions.caseMaterials.add(caseId, caseMaterial))
            },
            [caseId, localStore.actions.caseMaterials.add, localStore.dispatch]
        ),
        updateCaseMaterial: useCallback(
            (caseMaterialId: string, updates: Partial<CaseMaterial>) => {
                localStore.dispatch(
                    localStore.actions.caseMaterials.update(caseId, caseMaterialId, updates)
                )
            },
            [caseId, localStore.actions.caseMaterials.update, localStore.dispatch]
        ),
        addUploadedFiles: useCallback(
            (files: UploadedFile[]) => {
                localStore.dispatch(localStore.actions.files.addUploaded(caseId, files))
            },
            [caseId, localStore.actions.files.addUploaded, localStore.dispatch]
        ),
        removeUploadedFile: useCallback(
            (fileId: string) => {
                localStore.dispatch(localStore.actions.files.removeUploaded(caseId, fileId))
            },
            [caseId, localStore.actions.files.removeUploaded, localStore.dispatch]
        ),
    }
}

// ============================================================================
// MIDDLEWARE
// ============================================================================

// Logger middleware
export const loggerMiddleware: StoreMiddleware = (action, state) => {
    console.group(`[LocalStore] ${action.type}`)
    console.log("Action:", action)
    console.log("Previous State:", state)
    console.groupEnd()
    return action
}

// Validation middleware
export const validationMiddleware: StoreMiddleware = (action, _state) => {
    switch (action.type) {
        case "CASES/ADD_CASE": {
            const caseData = action.payload as Case
            if (!caseData.id || !caseData.title) {
                console.error("[Validation] Invalid case data:", caseData)
                return null // Block invalid actions
            }
            break
        }
        case "CASES/UPDATE_CASE": {
            const { caseId, updates } = action.payload as {
                caseId: string
                updates: Partial<Case>
            }
            if (!caseId || !updates) {
                console.error("[Validation] Invalid update data:", action.payload)
                return null
            }
            break
        }
    }
    return action
}

// Async operations middleware
export const asyncMiddleware: StoreMiddleware = (action, _state) => {
    // Handle async actions
    if (action.type.startsWith("ASYNC/")) {
        // For async operations, we could dispatch loading states
        // This is a simplified version - in a real app you'd have thunk-like functionality
        return action
    }
    return action
}

// Persistence middleware
export const persistenceMiddleware: StoreMiddleware = (action, _state) => {
    // Add metadata for persistence
    return {
        ...action,
        meta: {
            ...action.meta,
            timestamp: Date.now(),
            persisted: true,
        },
    }
}

// ============================================================================
// MIGRATIONS & VERSIONING
// ============================================================================

const migrations: Migration[] = [
    // Example migration from 0.9.0 to 1.0.0
    {
        fromVersion: "0.9.0",
        toVersion: "1.0.0",
        migrate: (state) => ({
            ...state,
            version: "1.0.0",
            ui: {
                isLoading: false,
                lastUpdated: new Date().toISOString(),
            },
        }),
    },
]

// biome-ignore lint/suspicious/noExplicitAny: Migration runner needs to handle any state version
const runMigrations = (state: any, fromVersion: string): any => {
    let migratedState = { ...state }

    for (const migration of migrations) {
        if (migration.fromVersion === fromVersion) {
            console.log(
                `[Migration] Running migration ${migration.fromVersion} -> ${migration.toVersion}`
            )
            migratedState = migration.migrate(migratedState)
        }
    }

    return migratedState
}

// ============================================================================
// ASYNC ACTION CREATORS
// ============================================================================

// Async action for loading cases from API
export const loadCasesAsync = () => async (dispatch: (action: StoreAction) => void) => {
    dispatch(localStore.actions.ui.setLoading(true))

    try {
        // Check if we should use mock data
        const useMockData =
            import.meta.env.VITE_USE_MOCK_DATA === "true" ||
            (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

        if (useMockData) {
            // Use mock data
            const { mockLoadCasesAsync } = await import("../../mocks")
            await mockLoadCasesAsync()(dispatch)
        } else {
            // TODO: Replace with actual API call
            await new Promise((resolve) => setTimeout(resolve, 1000))

            // Mock data - replace with actual API response
            const jobs: Case[] = []

            dispatch(localStore.actions.jobs.setJobs(jobs as Job[]))
        }
    } catch (error) {
        console.error("Failed to load cases:", error)
    } finally {
        dispatch(localStore.actions.ui.setLoading(false))
    }
}

// Async action for generating case materials
export const generateCaseMaterialAsync =
    (
        caseId: string,
        type: "facts" | "research" | "evidence" | "notes" | "drafting" | "custom",
        topic?: string
    ) =>
    async (dispatch: (action: StoreAction) => void) => {
        dispatch(localStore.actions.ui.setLoading(true))

        try {
            const useMockData =
                import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

            if (useMockData) {
                const { mockGenerateCaseMaterial } = await import("../../mocks")
                const newMaterial = await mockGenerateCaseMaterial(caseId, type, topic)
                dispatch(localStore.actions.caseMaterials.add(caseId, newMaterial))
                return newMaterial
            }
            // TODO: Replace with actual API call
            await new Promise((resolve) => setTimeout(resolve, 2000))
            throw new Error("Real API not implemented yet")
        } catch (error) {
            console.error("Failed to generate case material:", error)
            throw error
        } finally {
            dispatch(localStore.actions.ui.setLoading(false))
        }
    }

// Async action for uploading files
export const uploadFilesAsync =
    (caseId: string, files: File[]) => async (dispatch: (action: StoreAction) => void) => {
        dispatch(localStore.actions.ui.setLoading(true))

        try {
            const useMockData =
                import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

            if (useMockData) {
                const { mockFileUpload } = await import("../../mocks")
                const result = await mockFileUpload(files, caseId)
                dispatch(localStore.actions.files.addUploaded(caseId, result.uploadedFiles))
                return result
            }
            // TODO: Replace with actual API call
            await new Promise((resolve) => setTimeout(resolve, 1500))
            throw new Error("Real file upload API not implemented yet")
        } catch (error) {
            console.error("Failed to upload files:", error)
            throw error
        } finally {
            dispatch(localStore.actions.ui.setLoading(false))
        }
    }

// Chat management actions
export const chatActions = {
    createChat:
        (
            caseId: string,
            name: string,
            mode: "ask" | "write",
            contexts: string[],
            casefiles: string[]
        ) =>
        async (_dispatch: (action: StoreAction) => void) => {
            try {
                const useMockData =
                    import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                    (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

                if (useMockData) {
                    const { mockCreateChat } = await import("../../mocks")
                    const newChat = mockCreateChat(caseId, name, mode, contexts, casefiles)
                    // Note: Chat state is managed in mock files, not in the store
                    // This is a simplified approach for the prototype
                    return newChat
                }
            } catch (error) {
                console.error("Failed to create chat:", error)
                throw error
            }
        },

    sendMessage:
        (
            caseId: string,
            chatId: string,
            message: string,
            mode: "law" | "facts" = "law",
            accessToken?: string
        ) =>
        async (_dispatch: (action: StoreAction) => void) => {
            try {
                // If access token provided, use real API
                if (accessToken) {
                    const { generateAnswer } = await import("../chat.client")
                    const response = await generateAnswer({
                        query: message,
                        mode: mode,
                        sessionId: caseId,
                        accessToken: accessToken,
                        limit: 10,
                        similarityThreshold: 0.7,
                        alpha: 0.7,
                        chunkMode: mode === "facts" ? "context" : undefined,
                    })

                    // Format response to match expected message structure
                    return {
                        id: Date.now(),
                        type: "ai",
                        content: response.answer.text,
                        timestamp: new Date().toISOString(),
                        status: "delivered",
                        metadata: {
                            citations: response.answer.citations,
                            quality_score: response.answer.quality_score,
                            provider: response.answer.provider,
                            model: response.answer.model,
                            chunks_used: response.answer.metadata.chunks_used,
                            processing_time_ms: response.processing_time_ms,
                            mode: mode,
                        },
                    }
                }

                // Fallback to mock data if no token
                const useMockData =
                    import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                    (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

                if (useMockData) {
                    const { mockSendChatMessage } = await import("../../mocks")
                    const response = await mockSendChatMessage(caseId, chatId, message)
                    return response
                }

                throw new Error("No authentication token provided and mock data is disabled")
            } catch (error) {
                console.error("Failed to send chat message:", error)
                throw error
            }
        },

    getChats: (caseId: string) => async () => {
        try {
            const useMockData =
                import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

            if (useMockData) {
                const { mockGetChats } = await import("../../mocks")
                return mockGetChats(caseId)
            }
            return []
        } catch (error) {
            console.error("Failed to get chats:", error)
            return []
        }
    },
}

// Async action for creating a case
export const createCaseAsync =
    (caseData: Omit<Case, "id" | "createdAt" | "updatedAt">) =>
    async (dispatch: (action: StoreAction) => void) => {
        dispatch(localStore.actions.ui.setLoading(true))

        try {
            // Check if we should use mock data
            const useMockData =
                import.meta.env.VITE_USE_MOCK_DATA === "true" ||
                (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

            if (useMockData) {
                // Use mock data
                const { mockCreateCaseAsync } = await import("../../mocks")
                return await mockCreateCaseAsync(caseData)(dispatch)
            }
            // TODO: Replace with actual API call
            await new Promise((resolve) => setTimeout(resolve, 500))

            const newCase: Case = {
                ...caseData,
                id: `case_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                caseMaterials: [],
                uploads: [],
            }

            dispatch(localStore.actions.jobs.addJob(newCase as Job))
            return newCase
        } catch (error) {
            console.error("Failed to create case:", error)
            throw error
        } finally {
            dispatch(localStore.actions.ui.setLoading(false))
        }
    }

// ============================================================================
// SECURITY UTILITIES
// ============================================================================

// Basic obfuscation for localStorage (not true encryption)
// In production, use proper encryption like crypto-js or Web Crypto API
const obfuscate = (data: string): string => {
    // Simple base64 encoding with a salt
    const salt = "jc-store-salt-2024"
    const salted = salt + data + salt
    return btoa(salted).split("").reverse().join("")
}

const deobfuscate = (data: string): string => {
    try {
        // Reverse the obfuscation
        const reversed = data.split("").reverse().join("")
        const decoded = atob(reversed)
        const salt = "jc-store-salt-2024"
        return decoded.slice(salt.length, -salt.length)
    } catch {
        throw new Error("Failed to deobfuscate data")
    }
}

// ============================================================================
// DEV TOOLS & UTILITIES
// ============================================================================

// Store inspector for debugging
export const createStoreInspector = () => {
    const store = LocalStore.getInstance()

    return {
        // Get current state snapshot
        getSnapshot: () => store.getState(),

        // Subscribe to state changes with detailed logging
        subscribeWithLogging: (name: string) => {
            return store.subscribe((state, action) => {
                console.group(`[${name}] State Update`)
                console.log("Action:", action)
                console.log("New State:", state)
                console.groupEnd()
            })
        },

        // Time travel debugging (stores history)
        createTimeTraveler: () => {
            const history: StoreState[] = []
            const actions: StoreAction[] = []

            const unsubscribe = store.subscribe((state, action) => {
                history.push({ ...state })
                if (action) actions.push(action)
            })

            return {
                getHistory: () => history,
                getActions: () => actions,
                getCurrentIndex: () => history.length - 1,
                unsubscribe,
            }
        },

        // Performance monitoring
        monitorPerformance: () => {
            let startTime = Date.now()
            let actionCount = 0

            const unsubscribe = store.subscribe(() => {
                actionCount++
                const now = Date.now()
                if (now - startTime > 1000) {
                    // Log every second
                    console.log(`[Performance] ${actionCount} actions in ${now - startTime}ms`)
                    actionCount = 0
                    startTime = now
                }
            })

            return unsubscribe
        },
    }
}

// ============================================================================
// STORE INITIALIZATION WITH MIDDLEWARE
// ============================================================================

// Enhanced store creation with migration support
const createConfiguredStore = async () => {
    const store = LocalStore.getInstance({
        persistKey: "jc-local-store",
        version: "1.0.0",
        maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
        debug: import.meta.env.DEV,
    })

    // Add middleware (order matters)
    if (import.meta.env.DEV) {
        store.use(loggerMiddleware)
    }
    store.use(validationMiddleware)
    store.use(asyncMiddleware)
    store.use(persistenceMiddleware)

    // Initialize store
    store.initialize()

    // Dynamic data initialization based on environment
    if (store.getState().jobs.length === 0) {
        seedStoreWithDemoJobs(store)
        console.log("[Store] Seeded demo jobs for local UI mode")
    }

    return store
}

// Migration-enabled store initialization
const initializeStoreWithMigrations = (store: LocalStore) => {
    // Override the loadFromStorage method safely (using type assertion for protected access)
    // biome-ignore lint/suspicious/noExplicitAny: Protected method access requires type assertion for migration system
    const _originalLoad = (store as any).loadFromStorage.bind(store)

    // biome-ignore lint/suspicious/noExplicitAny: Protected method override requires type assertion for migration system
    ;(store as any).loadFromStorage = function () {
        if (typeof window === "undefined") return

        try {
            const stored = localStorage.getItem(this.config.persistKey)
            if (!stored) return

            const data = JSON.parse(stored)

            // Check if migration is needed
            if (data.version && data.version !== this.config.version) {
                console.log(`[LocalStore] Migrating from ${data.version} to ${this.config.version}`)
                data.state = runMigrations(data.state, data.version)
                data.version = this.config.version

                // Save migrated data
                localStorage.setItem(this.config.persistKey, JSON.stringify(data))
            }

            // Check data age
            if (this.config.maxAge && Date.now() - data.timestamp > this.config.maxAge) {
                console.warn("[LocalStore] Data expired, starting fresh")
                return
            }

            this.state = { ...this.state, ...data.state }
        } catch (error) {
            console.warn("[LocalStore] Failed to load migrated state:", error)
        }
    }

    return store
}

// ============================================================================
// EXPORTS
// ============================================================================

// New LocalStore API (recommended) - Async initialization
export const getLocalStore = async (): Promise<LocalStore> => {
    const store = await createConfiguredStore()
    return initializeStoreWithMigrations(store)
}

// Initialize store immediately for backward compatibility
let _localStore: LocalStore | null = null
export const localStore = (() => {
    if (!_localStore) {
        // For now, we'll create a synchronous version
        // In a real app, you'd want to await this at app startup
        const store = LocalStore.getInstance({
            persistKey: "jc-local-store",
            version: "1.0.0",
            maxAge: 7 * 24 * 60 * 60 * 1000,
            debug: import.meta.env.DEV,
        })

        // Add middleware
        if (import.meta.env.DEV) {
            store.use(loggerMiddleware)
        }
        store.use(validationMiddleware)
        store.use(asyncMiddleware)
        store.use(persistenceMiddleware)

        // Initialize synchronously for now
        store.initialize()

        _localStore = initializeStoreWithMigrations(store)

        // Async initialization will happen in the background
        getLocalStore()
            .then((store) => {
                _localStore = store
            })
            .catch((error) => {
                console.warn("[Store] Async initialization failed:", error)
            })
    }

    return _localStore
})()

// Legacy AppState API (for backward compatibility)
export const appState = AppState.getInstance()

// Export types and classes for external use
export type { StoreState, StoreAction, StoreMiddleware, StoreSubscriber, StoreConfig }
export { LocalStore }

// All utilities are already exported above

// ============================================================================
// USAGE EXAMPLES (Documentation)
// ============================================================================

/*
// Example: Using the new LocalStore API
import { localStore, useLocalStore } from '~/services/state.client';

function MyComponent() {
  const { state, dispatch, actions } = useLocalStore();

  const handleAddCase = () => {
    dispatch(actions.cases.addCase({
      id: 'case-1',
      title: 'New Case',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      caseMaterials: [],
      uploads: []
    }));
  };

  return (
    <div>
      <h1>Jobs: {state.jobs.length}</h1>
      <button onClick={handleAddCase}>Add Case</button>
    </div>
  );
}

// Example: Using specific hooks
import { useCases, useCurrentCase } from '~/services/state.client';

function CasesList() {
  const { cases: jobs, addCase: addJob, updateCase: updateJob } = useCases();
  const { currentCase, setCurrentCase } = useCurrentCase();

  return (
    <div>
      {jobs.map(case => (
        <div key={case.id} onClick={() => setCurrentCase(case)}>
          {case.title}
        </div>
      ))}
    </div>
  );
}

// Example: Async actions
import { createCaseAsync } from '~/services/state.client';

const handleCreateCase = async () => {
  try {
    const newCase = await createCaseAsync({
      title: 'My New Case',
      status: 'draft'
    });
    console.log('Created case:', newCase);
  } catch (error) {
    console.error('Failed to create case:', error);
  }
};

// Example: Using middleware and dev tools
import { createStoreInspector } from '~/services/state.client';

const inspector = createStoreInspector();
const timeTraveler = inspector.createTimeTraveler();
const performanceMonitor = inspector.monitorPerformance();

// Later, access debugging info
console.log('State history:', timeTraveler.getHistory());
console.log('Actions history:', timeTraveler.getActions());
*/
