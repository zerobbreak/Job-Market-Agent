import { mockCases } from "./mock-jobs"

/**
 * Check if mock data should be used based on environment
 */
export const shouldUseMockData = (): boolean => {
    // Check environment variable
    if (import.meta.env.VITE_USE_MOCK_DATA === "true") {
        return true
    }

    // Default to false in production, true in development if not explicitly set
    return import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false"
}

/**
 * Get mock data for a specific case by ID
 */
export const getMockCase = (caseId: string) => {
    return mockCases.find((caseItem) => caseItem.id === caseId)
}

/**
 * Get mock case materials for a specific case
 */
export const getMockCaseMaterials = (caseId: string) => {
    const caseItem = getMockCase(caseId)
    return caseItem?.caseMaterials || []
}
