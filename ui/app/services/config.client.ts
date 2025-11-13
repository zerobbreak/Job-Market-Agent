// Extend window interface to include our runtime config
declare global {
    interface Window {
        __env__?: {
            VITE_OAUTH_PROVIDER_URL?: string
            VITE_JOB_MARKET_API_URL?: string
            VITE_SESSION_SECRET?: string
            VITE_MODE?: string
        }
    }
}

/**
 * Get configuration value with fallback to build-time env vars
 * This allows the app to work both in dev (using Vite env) and production (using runtime config)
 */
export function getEnv(key: keyof NonNullable<Window["__env__"]>): string | undefined {
    // In production (Docker), use window.__env__ injected at runtime
    if (typeof window !== "undefined" && window.__env__) {
        return window.__env__[key]
    }

    // In development, use Vite's import.meta.env
    return import.meta.env[key]
}

export const config = {
    get oauthProviderUrl(): string {
        return getEnv("VITE_OAUTH_PROVIDER_URL") || "http://localhost:8083"
    },
    get apiUrl(): string {
        const envUrl = getEnv("VITE_JOB_MARKET_API_URL")

        // If environment URL is set, use it
        if (envUrl) {
            return envUrl
        }

        return this.isProduction ? "http://localhost:8000/job-market/api/v1" : "/api/job-market"
    },
    get apiBaseUrl(): string {
        return getEnv("VITE_JOB_MARKET_API_URL") || "http://localhost:8000/job-market/api/v1"
    },
    get sessionSecret(): string {
        return getEnv("VITE_SESSION_SECRET") || "development-secret-change-in-production"
    },
    get isProduction(): boolean {
        return getEnv("VITE_MODE") === "production"
    },
} as const
