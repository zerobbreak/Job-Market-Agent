/**
 * Application Constants
 *
 * Centralized configuration and constants to avoid magic numbers
 * and provide consistent values across the application.
 */

// ============================================================================
// FILE UPLOAD CONSTANTS
// ============================================================================

export const FILE_UPLOAD = {
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_TYPES: [
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
    ] as const,
    MAX_FILENAME_LENGTH: 255,
    CHUNK_SIZE: 1024 * 1024, // 1MB chunks for large uploads
} as const

// ============================================================================
// UI CONSTANTS
// ============================================================================

export const UI = {
    // Timing
    DEBOUNCE_MS: 300,
    ANIMATION_DURATION: 200,
    TOAST_DURATION: 5000,
    SEARCH_BLUR_DELAY_MS: 200,

    // Layout
    MIN_CONTENT_HEIGHT: 600,
    SIDEBAR_WIDTH: 256,
    MOBILE_BREAKPOINT: 768,

    // Search & Pagination
    MAX_SEARCH_RESULTS: 10,
    ITEMS_PER_PAGE: 20,
    MAX_PAGES_SHOWN: 5,

    // Z-index layers
    Z_INDEX: {
        DROPDOWN: 1000,
        MODAL: 1050,
        TOOLTIP: 1070,
        POPOVER: 1080,
    },

    // Colors (using CSS custom properties for theme consistency)
    COLORS: {
        PRIMARY: "#4b92ff",
        SECONDARY: "#7a7a7a",
        SUCCESS: "#10b981",
        WARNING: "#f59e0b",
        ERROR: "#ef4444",
        BACKGROUND: "#fcfbf8",
        BORDER: "#edebe5",
    },
} as const

// ============================================================================
// AUTHENTICATION CONSTANTS
// ============================================================================

export const AUTH = {
    SESSION_KEY: "auth",
    TOKEN_REFRESH_BUFFER_MS: 60 * 1000, // 1 minute
    REFRESH_DEBOUNCE_MS: 1000, // 1 second
    REFRESH_TOKEN_LIFETIME_MS: 7200 * 1000, // 2 hours
    DEFAULT_LOGIN_REDIRECT: "/login",
    MAX_LOGIN_ATTEMPTS: 5,
    LOCKOUT_DURATION_MS: 15 * 60 * 1000, // 15 minutes
} as const

// ============================================================================
// API CONSTANTS
// ============================================================================

export const API = {
    BASE_URL: "/api/job-market",
    TIMEOUT_MS: 30000, // 30 seconds
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY_MS: 1000,
    ENDPOINTS: {
        AUTH: "/auth",
        JOBS: "/jobs",
        CHAT: "/chat",
        FILES: "/files",
        SETTINGS: "/settings",
        LEARN: "/learn",
    } as const,
} as const

// ============================================================================
// VALIDATION CONSTANTS
// ============================================================================

export const VALIDATION = {
    // String lengths
    MIN_PASSWORD_LENGTH: 8,
    MAX_PASSWORD_LENGTH: 128,
    MAX_EMAIL_LENGTH: 254,
    MAX_NAME_LENGTH: 50,
    MAX_OCCUPATION_LENGTH: 100,
    MAX_COMPANY_NAME_LENGTH: 200,
    MAX_JOB_TITLE_LENGTH: 150,

    // File validation
    MAX_FILENAME_LENGTH: 255,

    // Regular expressions
    EMAIL_REGEX:
        /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/,
    PASSWORD_REGEX: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,

    // Rate limiting
    MAX_REQUESTS_PER_MINUTE: 60,
    MAX_FILE_UPLOADS_PER_HOUR: 100,
} as const

// ============================================================================
// STORAGE CONSTANTS
// ============================================================================

export const STORAGE = {
    // localStorage keys
    AUTH_KEY: "auth",
    SETTINGS_KEY: "user_settings",
    THEME_KEY: "theme",
    LANGUAGE_KEY: "language",

    // Cache durations (in milliseconds)
    CACHE_DURATION: {
        SHORT: 5 * 60 * 1000, // 5 minutes
        MEDIUM: 30 * 60 * 1000, // 30 minutes
        LONG: 24 * 60 * 60 * 1000, // 24 hours
    },

    // Storage limits
    MAX_CACHE_SIZE: 50 * 1024 * 1024, // 50MB
    MAX_LOCAL_STORAGE_SIZE: 10 * 1024 * 1024, // 10MB
} as const

// ============================================================================
// FEATURE FLAGS & CONFIGURATION
// ============================================================================

export const FEATURES = {
    ENABLE_DEBUG_LOGGING: import.meta.env?.DEV ?? false,
    ENABLE_PERFORMANCE_MONITORING: import.meta.env?.PROD ?? false,
    ENABLE_ERROR_REPORTING: import.meta.env?.PROD ?? false,
    ENABLE_ANALYTICS: import.meta.env?.PROD ?? false,
    ENABLE_OFFLINE_MODE: false, // Future feature
    ENABLE_BETA_FEATURES: import.meta.env?.VITE_ENABLE_BETA === "true",
} as const

// ============================================================================
// EXTERNAL SERVICE CONSTANTS
// ============================================================================

export const EXTERNAL = {
    // Third-party API timeouts
    OPENAI_TIMEOUT: 60000, // 1 minute
    STRIPE_TIMEOUT: 30000, // 30 seconds

    // External service limits
    MAX_AI_REQUESTS_PER_HOUR: 1000,
    MAX_EMAILS_PER_DAY: 100,
} as const

// ============================================================================
// TYPE CONSTANTS (for runtime type checking)
// ============================================================================

export const TYPES = {
    MIME_TYPES: {
        PDF: "application/pdf",
        DOC: "application/msword",
        DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        XLS: "application/vnd.ms-excel",
        XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        PPT: "application/vnd.ms-powerpoint",
        PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        TXT: "text/plain",
        CSV: "text/csv",
        JPEG: "image/jpeg",
        PNG: "image/png",
        GIF: "image/gif",
        BMP: "image/bmp",
        TIFF: "image/tiff",
    } as const,

    FILE_EXTENSIONS: {
        PDF: ".pdf",
        DOC: ".doc",
        DOCX: ".docx",
        XLS: ".xls",
        XLSX: ".xlsx",
        PPT: ".ppt",
        PPTX: ".pptx",
        TXT: ".txt",
        CSV: ".csv",
        JPEG: ".jpg",
        PNG: ".png",
        GIF: ".gif",
        BMP: ".bmp",
        TIFF: ".tiff",
    } as const,
} as const
