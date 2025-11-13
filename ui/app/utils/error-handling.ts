/**
 * Standardized Error Handling Utilities
 *
 * Provides consistent error handling patterns across the application
 */

export interface ServiceError {
    message: string
    code?: string
    status?: number
    details?: unknown
    userFriendly?: boolean
}

export interface ServiceResult<T> {
    success: boolean
    data?: T
    error?: ServiceError
}

/**
 * Creates a standardized service result
 */
export function createServiceResult<T>(data?: T, error?: ServiceError): ServiceResult<T> {
    return {
        success: !error,
        data,
        error,
    }
}

/**
 * Creates a success result
 */
export function createSuccessResult<T>(data: T): ServiceResult<T> {
    return createServiceResult(data)
}

/**
 * Creates an error result
 */
export function createErrorResult<T>(error: ServiceError): ServiceResult<T> {
    return createServiceResult<T>(undefined, error)
}

/**
 * Wraps an async function with standardized error handling
 */
export async function withErrorHandling<T>(
    operation: () => Promise<T>,
    context: string
): Promise<ServiceResult<T>> {
    try {
        const data = await operation()
        return createSuccessResult(data)
    } catch (error) {
        console.error(`[${context}] Operation failed:`, error)

        const serviceError: ServiceError = {
            message: error instanceof Error ? error.message : "Unknown error occurred",
            code: "OPERATION_FAILED",
            details: error,
            userFriendly: true,
        }

        return createErrorResult(serviceError)
    }
}

/**
 * Extracts user-friendly error message from various error types
 */
export function extractUserFriendlyMessage(error: unknown): string {
    if (error instanceof Error) {
        return error.message
    }

    if (typeof error === "string") {
        return error
    }

    if (error && typeof error === "object" && "message" in error) {
        return String(error.message)
    }

    return "An unexpected error occurred"
}

/**
 * Determines if an error is a network error
 */
export function isNetworkError(error: unknown): boolean {
    if (error instanceof TypeError && error.message.includes("fetch")) {
        return true
    }

    if (error && typeof error === "object" && "name" in error && error.name === "TypeError") {
        return true
    }

    return false
}

/**
 * Determines if an error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
    if (error && typeof error === "object" && "status" in error) {
        const status = error.status
        return status === 401 || status === 403
    }

    return false
}

/**
 * Creates a standardized error for API responses
 */
export function createApiError(response: Response, _context: string): ServiceError {
    const status = response.status
    let message = `Request failed with status ${status}`

    if (status === 401) {
        message = "Authentication required"
    } else if (status === 403) {
        message = "Access denied"
    } else if (status === 404) {
        message = "Resource not found"
    } else if (status === 500) {
        message = "Server error occurred"
    }

    return {
        message,
        code: `HTTP_${status}`,
        status,
        userFriendly: true,
    }
}

/**
 * Handles common error scenarios consistently
 */
export function handleCommonErrors(error: unknown, _context: string): ServiceError {
    if (isNetworkError(error)) {
        return {
            message: "Network error: Please check your connection and try again",
            code: "NETWORK_ERROR",
            userFriendly: true,
        }
    }

    if (isAuthError(error)) {
        return {
            message: "Authentication failed: Please log in again",
            code: "AUTH_ERROR",
            userFriendly: true,
        }
    }

    return {
        message: extractUserFriendlyMessage(error),
        code: "UNKNOWN_ERROR",
        userFriendly: true,
    }
}
