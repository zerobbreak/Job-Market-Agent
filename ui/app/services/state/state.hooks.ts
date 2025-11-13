// React hooks for state management

/**
 * This module provides React hooks for accessing and manipulating state managed by LocalStore.
 * Each hook is tailored to specific parts of the state, providing a focused interface for components.
 * Performance optimizations are applied using useMemo and useCallback to minimize unnecessary re-renders.
 */

import { useCallback, useEffect, useMemo, useState } from "react"
import type { Case, CaseMaterial, UploadedFile, Job } from "@/types/job.types"
import { LocalStore } from "./state.client"
import type { StoreAction } from "./state.types"

/**
 * useLocalStore hook provides access to the entire store state and methods to dispatch actions.
 * It uses useState for state updates and useEffect for subscribing to store changes.
 * @returns An object containing the current state and a dispatch function for actions.
 */
export function useLocalStore() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [state, setState] = useState(localStore.getState())

    useEffect(() => {
        // Subscribe to store updates
        const unsubscribe = localStore.subscribe((newState) => setState(newState))
        return () => unsubscribe()
    }, [localStore])

    const dispatch = useCallback(
        (action: StoreAction) => localStore.dispatch(action),
        [localStore.dispatch]
    )

    return useMemo(
        () => ({
            state,
            dispatch,
            actions: localStore.actions,
        }),
        [state, dispatch, localStore.actions]
    )
}

/**
 * useCases hook provides access to the list of cases and methods to manage them.
 * It optimizes performance by memoizing action functions with useCallback.
 * @returns An object with the list of cases and methods to add, update, and delete cases.
 */
export function useCases() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [cases, setCases] = useState(localStore.getJobs())

    useEffect(() => {
        const unsubscribe = localStore.subscribe((state) => setCases(state.jobs))
        return () => unsubscribe()
    }, [localStore])

    const addCase = useCallback(
        (newJob: Case) =>
            localStore.dispatch(localStore.actions.jobs.addJob(newJob as Job)),
        [localStore.dispatch, localStore.actions.jobs.addJob]
    )
    const updateCase = useCallback(
        (caseId: string, updates: Partial<Case>) =>
            localStore.dispatch(localStore.actions.jobs.updateJob(caseId, updates)),
        [localStore.dispatch, localStore.actions.jobs.updateJob]
    )
    const deleteCase = useCallback(
        (caseId: string) => localStore.dispatch(localStore.actions.jobs.deleteJob(caseId)),
        [localStore.dispatch, localStore.actions.jobs.deleteJob]
    )

    return useMemo(
        () => ({
            cases,
            addCase,
            updateCase,
            deleteCase,
        }),
        [cases, addCase, updateCase, deleteCase]
    )
}

/**
 * useCurrentCase hook provides access to the currently selected case and a method to set it.
 * It uses useMemo to optimize the returned object and prevent unnecessary re-renders.
 * @returns An object with the current case and a method to set the current case.
 */
export function useCurrentCase() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [currentCase, setCurrentCaseState] = useState(localStore.getCurrentJob())

    useEffect(() => {
        const unsubscribe = localStore.subscribe((state) => setCurrentCaseState(state.currentJob))
        return () => unsubscribe()
    }, [localStore])

    const setCurrentCase = useCallback(
        (caseData: Case | null) =>
            localStore.dispatch(
                localStore.actions.currentJob.set(caseData as Job | null)
            ),
        [localStore.dispatch, localStore.actions.currentJob.set]
    )

    return useMemo(
        () => ({
            currentCase,
            setCurrentCase,
        }),
        [currentCase, setCurrentCase]
    )
}

/**
 * useUIState hook provides access to UI-related state and a method to update loading status.
 * It memoizes the returned object to optimize performance.
 * @returns An object with UI state and a method to set loading status.
 */
export function useUIState() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [uiState, setUIState] = useState(localStore.getState().ui)

    useEffect(() => {
        const unsubscribe = localStore.subscribe((state) => setUIState(state.ui))
        return () => unsubscribe()
    }, [localStore])

    const setLoading = useCallback(
        (isLoading: boolean) => localStore.dispatch(localStore.actions.ui.setLoading(isLoading)),
        [localStore.actions.ui.setLoading, localStore.dispatch]
    )

    return useMemo(
        () => ({
            uiState,
            setLoading,
        }),
        [uiState, setLoading]
    )
}

/**
 * useCaseData hook provides access to data for a specific case identified by caseId.
 * It optimizes performance by memoizing action methods with useCallback.
 * @param caseId The ID of the case to retrieve data for.
 * @returns An object with case data and methods to manage case-related data.
 */
export function useCaseData(caseId: string) {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [caseData, setCaseData] = useState(() => localStore.getCase(caseId))

    useEffect(() => {
        const unsubscribe = localStore.subscribe((state) => {
            const updatedCase = state.jobs.find((job) => job.id === caseId) || null
            setCaseData(updatedCase)
        })
        return () => unsubscribe()
    }, [caseId, localStore])

    const updateCase = useCallback(
        (updates: Partial<Case>) =>
            localStore.dispatch(localStore.actions.jobs.updateJob(caseId, updates)),
        [caseId, localStore.dispatch, localStore.actions.jobs.updateJob]
    )
    const addCaseMaterial = useCallback(
        (caseMaterial: CaseMaterial) =>
            localStore.dispatch(localStore.actions.caseMaterials.add(caseId, caseMaterial)),
        [caseId, localStore.dispatch, localStore.actions.caseMaterials.add]
    )
    const updateCaseMaterial = useCallback(
        (caseMaterialId: string, updates: Partial<CaseMaterial>) =>
            localStore.dispatch(
                localStore.actions.caseMaterials.update(caseId, caseMaterialId, updates)
            ),
        [caseId, localStore.dispatch, localStore.actions.caseMaterials.update]
    )
    const addUploadedFiles = useCallback(
        (files: UploadedFile[]) =>
            localStore.dispatch(localStore.actions.files.addUploaded(caseId, files)),
        [caseId, localStore.dispatch, localStore.actions.files.addUploaded]
    )
    const removeUploadedFile = useCallback(
        (fileId: string) =>
            localStore.dispatch(localStore.actions.files.removeUploaded(caseId, fileId)),
        [caseId, localStore.dispatch, localStore.actions.files.removeUploaded]
    )

    return useMemo(
        () => ({
            caseData,
            caseMaterials: caseData?.caseMaterials || [],
            uploads: caseData?.uploads || [],
            updateCase,
            addCaseMaterial,
            updateCaseMaterial,
            addUploadedFiles,
            removeUploadedFile,
        }),
        [
            caseData,
            updateCase,
            addCaseMaterial,
            updateCaseMaterial,
            addUploadedFiles,
            removeUploadedFile,
        ]
    )
}

export function useCaseMaterials(caseId: string | null) {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [materials, setMaterials] = useState<CaseMaterial[]>([])

    useEffect(() => {
        const updateMaterials = (state: ReturnType<typeof localStore.getState>) => {
            const updatedCase = state.jobs.find((c) => c.id === caseId)
            if (updatedCase?.jobMaterials) {
                setMaterials(updatedCase.jobMaterials)
            } else {
                setMaterials([])
            }
        }

        const initialCase = localStore.getCase(caseId || "")
        if (initialCase?.jobMaterials) {
            setMaterials(initialCase.jobMaterials)
        }

        const unsubscribe = localStore.subscribe(updateMaterials)
        return () => unsubscribe()
    }, [caseId, localStore])

    const addMaterial = useCallback(
        (caseId: string, material: CaseMaterial) =>
            localStore.dispatch(localStore.actions.caseMaterials.add(caseId, material)),
        [localStore.actions.caseMaterials.add, localStore.dispatch]
    )
    const updateMaterial = useCallback(
        (caseId: string, materialId: string, updates: Partial<CaseMaterial>) =>
            localStore.dispatch(
                localStore.actions.caseMaterials.update(caseId, materialId, updates)
            ),
        [localStore.actions.caseMaterials.update, localStore.dispatch]
    )

    return useMemo(
        () => ({
            materials,
            addMaterial,
            updateMaterial,
        }),
        [materials, addMaterial, updateMaterial]
    )
}

export function useUploadedFiles(caseId: string | null) {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    const [files, setFiles] = useState<UploadedFile[]>([])

    useEffect(() => {
        const updateFiles = (state: ReturnType<typeof localStore.getState>) => {
            const currentJob = caseId ? state.jobs.find((job) => job.id === caseId) : null
            setFiles(currentJob?.uploads ?? [])
        }

        updateFiles(localStore.getState())

        const unsubscribe = localStore.subscribe(updateFiles)
        return () => unsubscribe()
    }, [caseId, localStore])

    const addUploadedFiles = useCallback(
        (caseId: string, uploadedFiles: UploadedFile[]) =>
            localStore.dispatch(localStore.actions.files.addUploaded(caseId, uploadedFiles)),
        [localStore.actions.files.addUploaded, localStore.dispatch]
    )

    const removeUploadedFile = useCallback(
        (caseId: string, fileId: string) =>
            localStore.dispatch(localStore.actions.files.removeUploaded(caseId, fileId)),
        [localStore.actions.files.removeUploaded, localStore.dispatch]
    )

    return useMemo(
        () => ({
            files,
            addUploadedFiles,
            removeUploadedFile,
        }),
        [files, addUploadedFiles, removeUploadedFile]
    )
}

export function useDispatch() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    return useMemo(() => localStore.dispatch.bind(localStore), [localStore])
}

export function useActions() {
    const localStore = useMemo(() => LocalStore.getInstance(), [])
    return useMemo(() => localStore.actions, [localStore])
}
