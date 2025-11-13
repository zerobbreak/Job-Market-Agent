// Type guards and validation utilities

export function isValidEmail(email: string): boolean {
    if (!email || typeof email !== "string") return false

    // More comprehensive email validation
    const emailRegex =
        /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

    if (!emailRegex.test(email)) return false

    // Additional checks
    const [localPart, domain] = email.split("@")
    if (localPart.length > 64 || domain.length > 253) return false
    if (localPart.startsWith(".") || localPart.endsWith(".")) return false
    if (domain.includes("..")) return false

    return true
}

export function validateEmail(email: string): ValidationResult {
    const errors: string[] = []

    if (!email || typeof email !== "string") {
        errors.push("Email is required")
    } else {
        const trimmed = email.trim()
        if (trimmed.length === 0) {
            errors.push("Email cannot be empty")
        } else if (!isValidEmail(trimmed)) {
            errors.push("Please enter a valid email address")
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

export function validateUsername(username: string): ValidationResult {
    const errors: string[] = []

    if (!username || typeof username !== "string") {
        errors.push("Username is required")
    } else {
        const trimmed = username.trim()
        if (trimmed.length === 0) {
            errors.push("Username cannot be empty")
        } else if (trimmed.length < 3) {
            errors.push("Username must be at least 3 characters long")
        } else if (trimmed.length > 50) {
            errors.push("Username cannot exceed 50 characters")
        } else if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
            errors.push("Username can only contain letters, numbers, and underscores")
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

export function validatePassword(password: string): ValidationResult {
    const errors: string[] = []

    if (!password || typeof password !== "string") {
        errors.push("Password is required")
    } else {
        if (password.length < 8) {
            errors.push("Password must be at least 8 characters long")
        }
        if (password.length > 128) {
            errors.push("Password cannot exceed 128 characters")
        }
        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
            errors.push(
                "Password must contain at least one uppercase letter, one lowercase letter, and one number"
            )
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

export function isValidCaseId(id: string): boolean {
    return typeof id === "string" && id.length > 0 && /^[a-zA-Z0-9_-]+$/.test(id)
}

export function isValidJobMaterialType(
    type: string
): type is "ats-optimizer" | "cv-rewriter" | "cover-letter-specialist" | "interview-copilot" | "interview-prep-agent" | "notes" | "research" {
    return ["ats-optimizer", "cv-rewriter", "cover-letter-specialist", "interview-copilot", "interview-prep-agent", "notes", "research"].includes(type)
}

export function isValidCaseStatus(status: string): status is "active" | "draft" | "archived" {
    return ["active", "draft", "archived"].includes(status)
}

export function isValidCaseMaterialStatus(
    status: string
): status is "active" | "processing" | "completed" | "error" {
    return ["active", "processing", "completed", "error"].includes(status)
}

export function isValidFileType(file: File, allowedTypes: string[]): boolean {
    return allowedTypes.includes(file.type)
}

export function isValidFileSize(file: File, maxSizeInMB: number): boolean {
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024
    return file.size <= maxSizeInBytes
}

// ============================================================================
// INPUT SANITIZATION
// ============================================================================

export function sanitizeString(input: string): string {
    if (!input || typeof input !== "string") return ""

    return input
        .trim()
        .replace(/[<>"']/g, "") // Remove potential XSS characters
        .slice(0, 1000) // Limit length
}

export function sanitizeHtml(input: string): string {
    if (!input || typeof input !== "string") return ""

    // Basic HTML sanitization - in production use a proper library like DOMPurify
    return input
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
        .replace(/<[^>]*>?/gm, "")
        .trim()
        .slice(0, 10000) // Limit length
}

export function validateAndSanitizeCaseTitle(title: string): {
    isValid: boolean
    sanitized: string
    errors: string[]
} {
    const errors: string[] = []
    let sanitized = sanitizeString(title)

    if (!sanitized) {
        errors.push("Case title is required")
    } else if (sanitized.length < 3) {
        errors.push("Case title must be at least 3 characters long")
    } else if (sanitized.length > 100) {
        errors.push("Case title cannot exceed 100 characters")
        sanitized = sanitized.slice(0, 100)
    }

    // Check for potentially malicious content
    if (sanitized.includes("<script") || sanitized.includes("javascript:")) {
        errors.push("Invalid characters in case title")
        sanitized = sanitized.replace(/<script|javascript:/gi, "")
    }

    return {
        isValid: errors.length === 0,
        sanitized,
        errors,
    }
}

export function validateAndSanitizeJobTitle(title: string): {
    isValid: boolean
    sanitized: string
    errors: string[]
} {
    const errors: string[] = []
    let sanitized = sanitizeString(title)

    if (!sanitized) {
        errors.push("Job title is required")
    } else if (sanitized.length < 3) {
        errors.push("Job title must be at least 3 characters long")
    } else if (sanitized.length > 100) {
        errors.push("Job title cannot exceed 100 characters")
        sanitized = sanitized.slice(0, 100)
    }

    // Check for potentially malicious content
    if (sanitized.includes("<script") || sanitized.includes("javascript:")) {
        errors.push("Invalid characters in job title")
        sanitized = sanitized.replace(/<script|javascript:/gi, "")
    }

    return {
        isValid: errors.length === 0,
        sanitized,
        errors,
    }
}

// Validation schemas
export interface ValidationResult {
    isValid: boolean
    errors: string[]
}

export function validateJobTitle(title: string): ValidationResult {
    const errors: string[] = []

    if (!title || typeof title !== "string") {
        errors.push("Job title is required")
    } else {
        const trimmed = title.trim()
        if (trimmed.length === 0) {
            errors.push("Job title cannot be empty")
        } else if (trimmed.length < 3) {
            errors.push("Job title must be at least 3 characters long")
        } else if (trimmed.length > 150) {
            errors.push("Job title cannot exceed 150 characters")
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

// Deprecated: Use validateJobTitle instead
export function validateCaseTitle(title: string): ValidationResult {
    return validateJobTitle(title)
}

export function validateJobMaterialTitle(title: string): ValidationResult {
    const errors: string[] = []

    if (!title || typeof title !== "string") {
        errors.push("Job material title is required")
    } else {
        const trimmed = title.trim()
        if (trimmed.length === 0) {
            errors.push("Job material title cannot be empty")
        } else if (trimmed.length < 3) {
            errors.push("Job material title must be at least 3 characters long")
        } else if (trimmed.length > 100) {
            errors.push("Job material title cannot exceed 100 characters")
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

export function validateJobMaterialType(type: string): ValidationResult {
    const errors: string[] = []

    if (!type || typeof type !== "string") {
        errors.push("Job material type is required")
    } else if (!isValidJobMaterialType(type)) {
        errors.push("Invalid job material type")
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

export function validateFiles(
    files: File[],
    options: {
        maxFiles?: number
        maxSizePerFile?: number // in MB
        allowedTypes?: string[]
    }
): ValidationResult {
    const errors: string[] = []
    const { maxFiles = 10, maxSizePerFile = 50, allowedTypes } = options

    if (!Array.isArray(files)) {
        errors.push("Files must be an array")
        return { isValid: false, errors }
    }

    if (files.length === 0) {
        errors.push("At least one file is required")
        return { isValid: false, errors }
    }

    if (files.length > maxFiles) {
        errors.push(`Maximum ${maxFiles} files allowed`)
    }

    files.forEach((file, index) => {
        if (!(file instanceof File)) {
            errors.push(`File at index ${index} is not a valid file`)
            return
        }

        if (allowedTypes && !isValidFileType(file, allowedTypes)) {
            errors.push(
                `File "${file.name}" has an invalid type. Allowed types: ${allowedTypes.join(", ")}`
            )
        }

        if (!isValidFileSize(file, maxSizePerFile)) {
            errors.push(`File "${file.name}" is too large. Maximum size: ${maxSizePerFile}MB`)
        }
    })

    return {
        isValid: errors.length === 0,
        errors,
    }
}

// Runtime type checking for API responses
export function isCaseObject(obj: unknown): obj is {
    id: string
    title: string
    editedDate: string
    status?: string
    caseMaterials?: unknown[]
    uploads?: unknown[]
    createdAt?: string
    updatedAt?: string
} {
    const record = obj as Record<string, unknown>
    return (
        obj !== null &&
        obj !== undefined &&
        typeof obj === "object" &&
        "id" in obj &&
        typeof record.id === "string" &&
        "title" in obj &&
        typeof record.title === "string" &&
        "editedDate" in obj &&
        typeof record.editedDate === "string"
    )
}

export function isCaseMaterialObject(obj: unknown): obj is {
    id: string
    type: string
    title: string
    description?: string
    files?: File[]
    aiProcessing?: boolean
    status?: string
    createdAt: string
    updatedAt: string
    caseId: string
} {
    const record = obj as Record<string, unknown>
    return (
        obj !== null &&
        obj !== undefined &&
        typeof obj === "object" &&
        "id" in obj &&
        typeof record.id === "string" &&
        "type" in obj &&
        typeof record.type === "string" &&
        "title" in obj &&
        typeof record.title === "string" &&
        "createdAt" in obj &&
        typeof record.createdAt === "string" &&
        "updatedAt" in obj &&
        typeof record.updatedAt === "string" &&
        "caseId" in obj &&
        typeof record.caseId === "string"
    )
}

export function isUploadedFileObject(obj: unknown): obj is {
    id: string
    name: string
    size: number
    type: string
    uploadedAt: string
    status: string
    url?: string
    error?: string
} {
    const record = obj as Record<string, unknown>
    return (
        obj !== null &&
        obj !== undefined &&
        typeof obj === "object" &&
        "id" in obj &&
        typeof record.id === "string" &&
        "name" in obj &&
        typeof record.name === "string" &&
        "size" in obj &&
        typeof record.size === "number" &&
        "type" in obj &&
        typeof record.type === "string" &&
        "uploadedAt" in obj &&
        typeof record.uploadedAt === "string" &&
        "status" in obj &&
        typeof record.status === "string"
    )
}

// Safe JSON parsing with validation
export function safeParseJSON<T>(json: string, validator?: (obj: unknown) => obj is T): T | null {
    try {
        const parsed = JSON.parse(json)
        if (validator && !validator(parsed)) {
            console.warn("Parsed JSON failed validation:", parsed)
            return null
        }
        return parsed
    } catch (error) {
        console.warn("Failed to parse JSON:", error)
        return null
    }
}

// Error handling utilities
export function createErrorResponse(message: string, status = 400): Response {
    return new Response(JSON.stringify({ error: message }), {
        status,
        headers: { "Content-Type": "application/json" },
    })
}

// ============================================================================
// PROFILE VALIDATION
// ============================================================================

/**
 * Validates a profile name field (firstName or lastName)
 */
export function validateProfileName(name: string): ValidationResult {
    const errors: string[] = []

    const sanitized = sanitizeString(name)

    if (!sanitized.trim()) {
        errors.push("Name is required")
    } else if (sanitized.length > 50) {
        errors.push("Name cannot exceed 50 characters")
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

/**
 * Validates a profile occupation field
 */
export function validateProfileOccupation(occupation: string): ValidationResult {
    const errors: string[] = []

    const sanitized = sanitizeString(occupation)

    if (sanitized.length > 100) {
        errors.push("Occupation cannot exceed 100 characters")
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

/**
 * Validates a profile firm name field
 */
export function validateProfileCompanyName(companyName: string): ValidationResult {
    const errors: string[] = []

    const sanitized = sanitizeString(companyName)

    if (sanitized.length > 200) {
        errors.push("Company name cannot exceed 200 characters")
    }

    return {
        isValid: errors.length === 0,
        errors,
    }
}

// Deprecated: Use validateProfileCompanyName instead
export function validateProfileFirmName(firmName: string): ValidationResult {
    return validateProfileCompanyName(firmName)
}

/**
 * Validates complete profile settings
 */
export function validateProfileSettings(settings: {
    firstName: string
    lastName: string
    occupation?: string
    firmName?: string
}): { isValid: boolean; errors: Record<string, string[]> } {
    const errors: Record<string, string[]> = {}

    const firstNameValidation = validateProfileName(settings.firstName)
    if (!firstNameValidation.isValid) {
        errors.firstName = firstNameValidation.errors
    }

    const lastNameValidation = validateProfileName(settings.lastName)
    if (!lastNameValidation.isValid) {
        errors.lastName = lastNameValidation.errors
    }

    if (settings.occupation !== undefined) {
        const occupationValidation = validateProfileOccupation(settings.occupation)
        if (!occupationValidation.isValid) {
            errors.occupation = occupationValidation.errors
        }
    }

    if (settings.firmName !== undefined) {
        const firmNameValidation = validateProfileFirmName(settings.firmName)
        if (!firmNameValidation.isValid) {
            errors.firmName = firmNameValidation.errors
        }
    }

    return {
        isValid: Object.keys(errors).length === 0,
        errors,
    }
}

export function extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
        return error.message
    }
    if (typeof error === "string") {
        return error
    }
    if (error && typeof error === "object" && "message" in error) {
        const errorObj = error as { message: unknown }
        return String(errorObj.message)
    }
    return "An unknown error occurred"
}

/**
 * Handle 401 Unauthorized responses by clearing auth data and redirecting
 */
export function handle401Error(): never {
    // TODO: Implement token refresh retry mechanism
    // Attempt to refresh token before throwing error
    console.warn("Authentication error (401). Attempting token refresh...")
    // Placeholder for token refresh logic
    // If refresh fails or is not possible, then throw error
    throw new Error("Authentication error. Please log in again.")
}

/**
 * Check if we're in development mode where API calls should be skipped
 */
export function isDevelopmentMode(apiUrl: string, isProduction: boolean): boolean {
    return apiUrl === "/api/jc" || !isProduction
}

/**
 * Convert technical error messages to user-friendly messages for API responses
 */
export function makeErrorUserFriendly(errorMessage: string): string {
    // Map of technical errors to user-friendly messages
    const errorMap: Record<string, string> = {
        "No relevant documents found":
            "I couldn't find any relevant documents to answer your question. Please upload some case documents first, or try rephrasing your question.",
        "session_id is required":
            "Your session has expired. Please refresh the page and try again.",
        "Invalid session_id": "Your session is invalid. Please refresh the page and try again.",
        "query is required": "Please enter a question or prompt.",
        "mode is required": "Unable to determine query mode. Please try again.",
        "Authentication required": "Please sign in to continue.",
        "Invalid token": "Your session has expired. Please sign in again.",
    }

    // Check if we have a direct match
    if (errorMap[errorMessage]) {
        return errorMap[errorMessage]
    }

    // Check if the error message contains any of the keys
    for (const [key, value] of Object.entries(errorMap)) {
        if (errorMessage.toLowerCase().includes(key.toLowerCase())) {
            return value
        }
    }

    // If no match found, return the original message but make it more readable
    return errorMessage
}
