/**
 * Authentication Service for Attica Backend
 *
 * Backend Configuration:
 * - Access Token Lifetime: 300 seconds (5 minutes)
 * - Refresh Token Lifetime: 7200 seconds (2 hours)
 * - Algorithm: RS256 (RSA + SHA256)
 * - Header Format: JWT (not Bearer)
 * - Token Rotation: Enabled (new refresh token on each refresh)
 * - Blacklist: Disabled (old refresh tokens remain valid until expiry)
 * - CSRF Protection: Disabled (using JWT tokens for security)
 *
 * Endpoints:
 * - POST /auth/token/          - Login (get tokens)
 * - POST /auth/token/refresh/  - Refresh access token
 * - POST /auth/token/revoke/   - Logout (revoke refresh token)
 *
 * Strategy:
 * - Access tokens are decoded locally to check expiry (no verify endpoint)
 * - Tokens are proactively refreshed 60 seconds before expiry
 * - Refresh token rotation: server may return new refresh token on refresh
 * - Authorization header uses "JWT" prefix (not "Bearer")
 * - No CSRF tokens needed (CSRF middleware disabled on backend)
 * - No cookies needed (tokens passed in headers/body only)
 */
import { createCookieSessionStorage, redirect } from "react-router"
import type {
    AuthenticatedUser,
    AuthProviderError,
    AuthSessionData,
    RegisterOptions,
    RegisterResult,
    RequireUserOptionalResult,
    RequireUserOptions,
    RequireUserResult,
    SignInOptions,
    SignInResult,
    TokenPair,
} from "@/types/auth.types"
import { makeErrorUserFriendly } from "~/utils/validation"
import { config } from "./config.client"

const AUTH_SESSION_KEY = "auth"
// Refresh 60 seconds before expiry (access tokens last 5 minutes)
const TOKEN_REFRESH_BUFFER_MS = 60 * 1000
const DEFAULT_LOGIN_REDIRECT = "/login"

const IS_DEV_AUTH = true

function base64UrlEncode(input: string | Record<string, unknown>): string {
    const text = typeof input === "string" ? input : JSON.stringify(input)
    const encoder = new TextEncoder()
    const bytes = encoder.encode(text)
    let binary = ""
    bytes.forEach((byte) => {
        binary += String.fromCharCode(byte)
    })
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "")
}

function createMockToken(email: string, lifetimeSeconds: number): string {
    const issuedAt = Math.floor(Date.now() / 1000)
    const header = base64UrlEncode({ alg: "HS256", typ: "JWT" })
    const payload = base64UrlEncode({ email, iat: issuedAt, exp: issuedAt + lifetimeSeconds })
    const signature = base64UrlEncode(`${email}.${issuedAt}.${Math.random().toString(36).slice(2)}`)
    return `${header}.${payload}.${signature}`
}

function createMockTokenPair(email: string): TokenPair {
    return {
        access: createMockToken(email, 60 * 60),
        refresh: createMockToken(email, 60 * 60 * 4),
    }
}

function capitalizeWord(value: string | undefined): string {
    if (!value) return "Demo"
    return value.charAt(0).toUpperCase() + value.slice(1)
}

function createMockUser(email: string): AuthenticatedUser {
    const [localPart] = email.split("@")
    const parts = localPart?.split(/[._-]+/) ?? []
    const firstName = capitalizeWord(parts[0] || "Demo")
    const lastName = capitalizeWord(parts[1] || "Candidate")

    return {
        id: Number(`${Date.now()}`.slice(-6)),
        email,
        first_name: firstName,
        last_name: lastName,
        is_active: true,
        user_permissions: ["jobs:read", "jobs:write", "settings:update"],
    }
}

function isMockToken(token: string | undefined): boolean {
    if (!token) return false
    const parts = token.split(".")
    if (parts.length !== 3) return false
    try {
        const payload = JSON.parse(base64urlDecode(parts[1]))
        return typeof payload?.email === "string"
    } catch {
        return false
    }
}

const DEFAULT_MOCK_PASSWORD = "jobmarket-demo"
const DEFAULT_MOCK_USER_EMAIL = "demo@jobmarketagent.ai"

type MockAuthRecord = {
    password: string
    user: AuthenticatedUser
}

const mockAuthUsers = new Map<string, MockAuthRecord>()

function ensureMockUserRecord(email: string, password?: string): MockAuthRecord {
    const normalizedEmail = email.trim().toLowerCase()
    const existing = mockAuthUsers.get(normalizedEmail)

    if (existing) {
        if (password) {
            existing.password = password
        }
        return existing
    }

    const record: MockAuthRecord = {
        password: password ?? DEFAULT_MOCK_PASSWORD,
        user: createMockUser(normalizedEmail),
    }

    mockAuthUsers.set(normalizedEmail, record)
    return record
}

ensureMockUserRecord(DEFAULT_MOCK_USER_EMAIL, DEFAULT_MOCK_PASSWORD)

function extractEmailFromMockToken(token: string | undefined): string | null {
    if (!token) return null
    const parts = token.split(".")
    if (parts.length !== 3) return null
    try {
        const payload = JSON.parse(base64urlDecode(parts[1])) as { email?: string }
        return typeof payload.email === "string" ? payload.email : null
    } catch {
        return null
    }
}

class AuthServiceError extends Error {
    status?: number
    data?: unknown

    constructor(message: string, status?: number, data?: unknown) {
        super(message)
        this.name = "AuthServiceError"
        this.status = status
        this.data = data
    }
}

export const sessionStorage = createCookieSessionStorage({
    cookie: {
        name: "__session",
        httpOnly: true,
        path: "/",
        sameSite: "lax",
        secrets: [config.sessionSecret || "fallback-secret-change-in-production"],
        secure: config.isProduction,
        maxAge: 60 * 60 * 24 * 30,
    },
})

type AuthSession = Awaited<ReturnType<typeof sessionStorage.getSession>>

export async function signIn(request: Request, credentials: SignInOptions): Promise<SignInResult> {
    const session = await sessionStorage.getSession(request.headers.get("cookie"))

    const tokenPair = await obtainTokens(credentials.email, credentials.password)
    let user: AuthenticatedUser

    if (IS_DEV_AUTH && isMockToken(tokenPair.access)) {
        console.info("[Auth] Development mode: using mock user profile for login")
        user = createMockUser(credentials.email)
    } else {
        try {
            user = await fetchCurrentUser(tokenPair.access, credentials.email)
        } catch (error) {
            if (IS_DEV_AUTH) {
                console.warn("[Auth] Falling back to mock user after fetch failure", error)
                user = createMockUser(credentials.email)
            } else {
                throw error
            }
        }
    }
    const { issuedAt, expiresAt } = extractTokenTimestamps(tokenPair.access)

    const authData: AuthSessionData = {
        user,
        accessToken: tokenPair.access,
        refreshToken: tokenPair.refresh,
        issuedAt,
        expiresAt,
    }

    const returnTo = session.get("returnTo")
    session.unset("returnTo")
    session.set(AUTH_SESSION_KEY, authData)

    const headers = {
        "Set-Cookie": await sessionStorage.commitSession(session),
    }

    return {
        user,
        headers,
        returnTo: typeof returnTo === "string" ? returnTo : undefined,
        accessToken: tokenPair.access,
        refreshToken: tokenPair.refresh,
        issuedAt,
        expiresAt,
    }
}

export async function requireUser(
    request: Request,
    options: RequireUserOptions & { throwOnInvalid: false }
): Promise<RequireUserOptionalResult>
export async function requireUser(
    request: Request,
    options?: RequireUserOptions
): Promise<RequireUserResult>
export async function requireUser(
    request: Request,
    options: RequireUserOptions = {}
): Promise<RequireUserResult | RequireUserOptionalResult> {
    const {
        redirectTo = DEFAULT_LOGIN_REDIRECT,
        returnTo,
        refresh = "auto",
        throwOnInvalid = true,
    } = options
    const sessionState = await loadAuthSession(request)

    if (!sessionState.data) {
        return handleMissingSession({
            request,
            session: sessionState.session,
            redirectTo,
            returnTo,
            throwOnInvalid,
        })
    }

    let authData = sessionState.data
    let sessionTouched = false

    if (!authData.user?.is_active) {
        return handleInvalidSession({
            request,
            session: sessionState.session,
            redirectTo,
            returnTo,
            throwOnInvalid,
        })
    }

    const expired = isExpired(authData)
    const refreshExpired = isRefreshTokenExpired(authData)

    // If refresh token is expired, can't refresh - must re-authenticate
    if (refreshExpired) {
        return handleInvalidSession({
            request,
            session: sessionState.session,
            redirectTo,
            returnTo,
            throwOnInvalid,
        })
    }

    // If access token expired but no refresh token, must re-authenticate
    if (expired && !authData.refreshToken) {
        return handleInvalidSession({
            request,
            session: sessionState.session,
            redirectTo,
            returnTo,
            throwOnInvalid,
        })
    }

    // Proactively refresh token if expired or about to expire
    if (refresh === "force" || expired || shouldRefresh(authData)) {
        const refreshed = await tryRefresh(authData)

        if (!refreshed) {
            return handleInvalidSession({
                request,
                session: sessionState.session,
                redirectTo,
                returnTo,
                throwOnInvalid,
            })
        }

        authData = refreshed
        sessionState.session.set(AUTH_SESSION_KEY, authData)
        sessionTouched = true
    }

    if (sessionTouched) {
        const headers = {
            "Set-Cookie": await sessionStorage.commitSession(sessionState.session),
        }
        return { user: authData.user, headers, accessToken: authData.accessToken }
    }

    return { user: authData.user, accessToken: authData.accessToken }
}

/**
 * Clear all authentication data from storage
 * Used when tokens are invalid, expired, or user logs out
 */
function clearAuthData(): void {
    if (typeof window !== "undefined") {
        localStorage.removeItem("auth")
        // Also clear any other auth-related data
        console.log("[Auth] Cleared all authentication data from localStorage")
    }
}

export async function signOut(
    request: Request,
    options: { redirectTo?: string; headersOnly: true }
): Promise<{ headers: Record<string, string> }>
export async function signOut(
    request: Request,
    options?: { redirectTo?: string }
): Promise<Response>
export async function signOut(
    request: Request,
    options: { redirectTo?: string; headersOnly?: boolean } = {}
): Promise<Response | { headers: Record<string, string> }> {
    const { session, data } = await loadAuthSession(request)

    // Revoke only the refresh token; most providers only accept refresh tokens for revocation
    if (data?.refreshToken) {
        await revokeToken(data.refreshToken)
    }

    session.unset(AUTH_SESSION_KEY)
    session.unset("returnTo")

    // Clear all auth data from localStorage
    clearAuthData()

    const cookie = await sessionStorage.destroySession(session)
    const headers = { "Set-Cookie": cookie }

    if (options.headersOnly) {
        return { headers }
    }

    const destination = options.redirectTo ?? "/"
    return redirect(destination, { headers })
}

export async function passwordReset(email: string, route: string): Promise<boolean> {
    const response = await callAuth<{ status: number }>("/auth/confirm-reset/", {
        method: "POST",
        body: JSON.stringify({ email, route }),
    })

    if (response.status === 204) {
        return true
    }

    return false
}

async function obtainTokens(email: string, password: string): Promise<TokenPair> {
    if (IS_DEV_AUTH) {
        return callAuth<TokenPair>("/auth/token/", {
            method: "POST",
            body: JSON.stringify({ email, password }),
        })
    }

    return callAuth<TokenPair>("/auth/token/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
    })
}

/**
 * Refresh access token using refresh token
 * Note: Backend may return a new refresh token (token rotation)
 * Always use the new refresh token if provided
 */
async function refreshTokens(refreshToken: string): Promise<TokenPair> {
    if (IS_DEV_AUTH) {
        return callAuth<TokenPair>("/auth/token/refresh/", {
            method: "POST",
            body: JSON.stringify({ refresh: refreshToken }),
        })
    }

    return callAuth<TokenPair>("/auth/token/refresh/", {
        method: "POST",
        body: JSON.stringify({ refresh: refreshToken }),
    })
}

// Removed verifyAccessToken - no longer needed as we decode JWT locally
// and refresh proactively based on expiry time

async function revokeToken(token: string): Promise<void> {
    try {
        await callAuth("/auth/token/revoke/", {
            method: "POST",
            // Send both common keys for compatibility (some backends expect `refresh`, others `refresh_token`)
            body: JSON.stringify({ refresh: token, refresh_token: token }),
        })
    } catch (error) {
        console.error("Token revocation failed", error)
    }
}

async function fetchCurrentUser(
    accessToken: string,
    fallbackEmail?: string
): Promise<AuthenticatedUser> {
    try {
        const response = await callAuth<unknown>("/auth/user/", {
            method: "GET",
            headers: {
                Authorization: `JWT ${accessToken}`,
            },
        })

        const user = normalizeUser(response)

        if (!user.is_active) {
            throw new AuthServiceError("User account is inactive", 403)
        }

        if (IS_DEV_AUTH) {
            const record = ensureMockUserRecord(user.email)
            record.user = {
                ...record.user,
                ...user,
            }
        }

        return user
    } catch (error) {
        if (IS_DEV_AUTH && fallbackEmail) {
            console.warn("[Auth] Using mock user fallback after profile fetch failure", error)
            return ensureMockUserRecord(fallbackEmail).user
        }
        throw error
    }
}

// Add debouncing for token refresh to prevent race conditions
let refreshTimeoutId: NodeJS.Timeout | null = null
const REFRESH_DEBOUNCE_MS = 1000 // 1 second debounce

/**
 * Attempt to refresh access token using refresh token
 *
 * Token Rotation: Backend may return new refresh token on refresh.
 * We use the new refresh token if provided, otherwise keep the old one.
 * This handles both rotation-enabled and rotation-disabled backends.
 *
 * @returns Updated auth data with new tokens, or null if refresh fails
 */
async function tryRefresh(authData: AuthSessionData): Promise<AuthSessionData | null> {
    if (!authData.refreshToken) {
        return null
    }

    // Debounce refresh attempts to prevent race conditions
    if (refreshTimeoutId) {
        clearTimeout(refreshTimeoutId)
    }

    // Store the refresh token in a local variable to avoid non-null assertion
    const refreshToken = authData.refreshToken

    return new Promise((resolve) => {
        refreshTimeoutId = setTimeout(async () => {
            try {
                const tokenPair = await refreshTokens(refreshToken)
                let refreshedUser: AuthenticatedUser

                if (IS_DEV_AUTH && isMockToken(tokenPair.access)) {
                    const tokenEmail =
                        extractEmailFromMockToken(tokenPair.access) || authData.user?.email || DEFAULT_MOCK_USER_EMAIL
                    refreshedUser = ensureMockUserRecord(tokenEmail).user
                } else {
                    refreshedUser = await fetchCurrentUser(
                        tokenPair.access,
                        authData.user?.email
                    )
                }
                const { issuedAt, expiresAt } = extractTokenTimestamps(tokenPair.access)

                resolve({
                    user: refreshedUser,
                    accessToken: tokenPair.access,
                    // Use new refresh token if provided (rotation), otherwise keep old one
                    refreshToken: tokenPair.refresh ?? authData.refreshToken,
                    issuedAt,
                    expiresAt,
                })
            } catch (error) {
                if (
                    error instanceof AuthServiceError &&
                    (error.status === 401 || error.status === 403)
                ) {
                    // Token refresh failed with unauthorized
                    // Use exponential backoff to prevent infinite retry loops
                    const RETRY_DELAY_MS = 30 * 1000 // 30 seconds
                    const now = Date.now()
                    const timeSinceIssued = authData.issuedAt
                        ? now - authData.issuedAt
                        : Number.POSITIVE_INFINITY

                    // Only clear auth data if tokens are old enough to avoid immediate logout loops
                    if (timeSinceIssued > RETRY_DELAY_MS) {
                        console.error(
                            "[Auth] Token refresh failed with 401/403 - clearing auth data"
                        )
                        clearAuthData()
                    } else {
                        console.warn(
                            "[Auth] Token refresh failed for recent tokens - will retry later"
                        )
                    }
                    resolve(null)
                } else if (IS_DEV_AUTH) {
                    console.warn(
                        "[Auth] Development mode: refresh failed, keeping existing session",
                        error
                    )
                    resolve(authData)
                } else {
                    console.warn("[Auth] Token refresh failed", error)
                    resolve(null)
                }
            }
        }, REFRESH_DEBOUNCE_MS)
    })
}

/**
 * Check if token should be refreshed proactively
 * Refreshes 60 seconds before expiry to avoid race conditions
 *
 * Access tokens last 5 minutes, so we refresh at the 4-minute mark
 */
function shouldRefresh(data: AuthSessionData): boolean {
    if (!data.refreshToken || !data.expiresAt) {
        return false
    }

    return data.expiresAt - TOKEN_REFRESH_BUFFER_MS <= Date.now()
}

/**
 * Check if token is already expired
 * If we can't determine expiry, treat as expired for security
 */
function isExpired(data: AuthSessionData): boolean {
    if (!data.expiresAt) {
        // No expiry time means we can't validate - treat as expired
        return true
    }

    return data.expiresAt <= Date.now()
}

/**
 * Check if refresh token is expired (2 hour lifetime)
 * This prevents using stale sessions that haven't been used in over 2 hours
 */
function isRefreshTokenExpired(data: AuthSessionData): boolean {
    if (!data.issuedAt || !data.refreshToken) {
        return true
    }

    const REFRESH_TOKEN_LIFETIME_MS = 7200 * 1000 // 2 hours in milliseconds
    const refreshTokenExpiryTime = data.issuedAt + REFRESH_TOKEN_LIFETIME_MS

    return refreshTokenExpiryTime <= Date.now()
}

/**
 * Browser-compatible base64url decode
 * Converts base64url to base64 and decodes it
 */
function base64urlDecode(base64url: string): string {
    // Convert base64url to base64
    let base64 = base64url.replace(/-/g, "+").replace(/_/g, "/")

    // Add padding if needed
    const padding = base64.length % 4
    if (padding) {
        base64 += "=".repeat(4 - padding)
    }

    // Decode base64 to string
    try {
        // atob() decodes base64 to binary string
        const binaryString = atob(base64)

        // Convert binary string to UTF-8
        const bytes = new Uint8Array(binaryString.length)
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i)
        }

        // Decode UTF-8 bytes to string
        return new TextDecoder().decode(bytes)
    } catch (error) {
        console.error("Failed to decode base64url:", error)
        throw error
    }
}

/**
 * Decode JWT token and extract timestamps
 * JWT tokens contain exp (expiry) and iat (issued at) claims in seconds since epoch
 */
function extractTokenTimestamps(token: string): {
    issuedAt: number
    expiresAt?: number
} {
    const parts = token.split(".")
    if (parts.length !== 3) {
        console.warn("Invalid JWT format: expected 3 parts")
        return { issuedAt: Date.now() }
    }

    try {
        // JWT payload is base64url encoded - decode it using browser-compatible method
        const payloadJson = base64urlDecode(parts[1])
        const payload = JSON.parse(payloadJson) as {
            exp?: number
            iat?: number
            user_id?: number
            username?: string
            email?: string
        }

        const issuedAt = typeof payload.iat === "number" ? payload.iat * 1000 : Date.now()
        const expiresAt = typeof payload.exp === "number" ? payload.exp * 1000 : undefined

        return { issuedAt, expiresAt }
    } catch (error) {
        console.warn("Failed to decode JWT token:", error)
        return { issuedAt: Date.now() }
    }
}

// CSRF functions removed - CSRF middleware disabled on backend
// If CSRF is re-enabled, these functions can be restored:
//
// function getCsrfToken(): string | null {
//   if (typeof document === "undefined") return null;
//   const cookies = document.cookie.split(";");
//   for (const cookie of cookies) {
//     const [name, value] = cookie.trim().split("=");
//     if (name === "csrftoken") return value;
//   }
//   return null;
// }
//
// async function ensureCsrfToken(): Promise<void> {
//   ... CSRF token fetching logic ...
// }

async function callAuth<T>(path: string, init: RequestInit): Promise<T> {
    return handleMockAuthRequest(path, init) as T
}

function parseRequestBody(init: RequestInit): Record<string, unknown> {
    const { body } = init
    if (!body) return {}

    if (typeof body === "string") {
        if (!body.trim()) return {}
        try {
            return JSON.parse(body)
        } catch (error) {
            console.warn("[Auth] Failed to parse request body:", error)
            return {}
        }
    }

    if (body instanceof URLSearchParams) {
        return Object.fromEntries(body.entries())
    }

    if (body instanceof FormData) {
        return Object.fromEntries(body.entries())
    }

    return {}
}

async function handleMockAuthRequest(path: string, init: RequestInit): Promise<unknown> {
    const method = (init.method ?? "GET").toUpperCase()
    const headers = new Headers(init.headers)
    const body = parseRequestBody(init)

    switch (path) {
        case "/auth/token/": {
            const email = String(body.email ?? "").trim().toLowerCase()
            const password = String(body.password ?? "")

            if (!email || !password) {
                throw new AuthServiceError("Email and password are required", 400)
            }

            const record = ensureMockUserRecord(email, password)

            if (record.password && record.password !== password) {
                throw new AuthServiceError("Invalid email or password", 401, {
                    detail: "invalid_credentials",
                })
            }

            return createMockTokenPair(record.user.email)
        }

        case "/auth/token/refresh/": {
            const refreshToken = String(body.refresh ?? body.refresh_token ?? "")
            const email = extractEmailFromMockToken(refreshToken) || DEFAULT_MOCK_USER_EMAIL
            const record = ensureMockUserRecord(email)
            return createMockTokenPair(record.user.email)
        }

        case "/auth/token/revoke/": {
            return { status: 204 }
        }

        case "/auth/user/": {
            const authHeader = headers.get("Authorization") || ""
            const token = authHeader.replace(/^JWT\s+/i, "").trim()
            const email = extractEmailFromMockToken(token) || DEFAULT_MOCK_USER_EMAIL
            const record = ensureMockUserRecord(email)
            return record.user
        }

        case "/auth/confirm-reset/": {
            return { status: 204 }
        }

        default: {
            throw new AuthServiceError(`Unsupported auth endpoint: ${path}`, 404)
        }
    }
}

function extractErrorMessage(data: unknown): string | undefined {
    if (!data || typeof data !== "object") {
        return undefined
    }

    const { detail, message, non_field_errors: nonFieldErrors } = data as AuthProviderError

    if (typeof detail === "string" && detail.trim().length > 0) {
        return detail
    }

    if (typeof message === "string" && message.trim().length > 0) {
        return message
    }

    if (Array.isArray(nonFieldErrors) && nonFieldErrors.length > 0) {
        return nonFieldErrors.join(" ")
    }

    return undefined
}

function normalizeUser(payload: unknown): AuthenticatedUser {
    const user = Array.isArray((payload as { results?: unknown[] }).results)
        ? ((payload as { results: unknown[] }).results[0] as AuthenticatedUser | undefined)
        : (payload as AuthenticatedUser | undefined)

    if (!user) {
        const userFriendlyMessage = makeErrorUserFriendly("Auth provider did not return user data")
        throw new AuthServiceError(userFriendlyMessage, 500, payload)
    }

    if (
        typeof user.id !== "number" ||
        typeof user.email !== "string" ||
        typeof user.first_name !== "string" ||
        typeof user.last_name !== "string" ||
        typeof user.is_active !== "boolean"
    ) {
        const userFriendlyMessage = makeErrorUserFriendly(
            "Received malformed user profile from auth provider"
        )
        throw new AuthServiceError(userFriendlyMessage, 500, payload)
    }

    return {
        id: user.id,
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
        is_active: user.is_active,
        user_permissions: user.user_permissions ?? [],
    }
}

async function loadAuthSession(
    request: Request
): Promise<{ session: AuthSession; data?: AuthSessionData }> {
    const session = await sessionStorage.getSession(request.headers.get("cookie"))
    let data = session.get(AUTH_SESSION_KEY) as AuthSessionData | undefined

    // For SPA, also check localStorage if session storage doesn't have data
    if (!data && typeof window !== "undefined") {
        const storedAuth = localStorage.getItem("auth")
        if (storedAuth) {
            try {
                data = JSON.parse(storedAuth)
            } catch (error) {
                console.error("Failed to parse stored auth data:", error)
                localStorage.removeItem("auth")
            }
        }
    }

    return { session, data }
}

type SessionHandlerArgs = {
    request: Request
    session: AuthSession
    redirectTo: string
    returnTo?: string
    throwOnInvalid: boolean
}

function deriveReturnTo(request: Request, explicit?: string): string {
    if (explicit) {
        return explicit
    }

    const url = new URL(request.url)
    return `${url.pathname}${url.search}`
}

async function handleMissingSession(args: SessionHandlerArgs): Promise<RequireUserOptionalResult> {
    const { request, session, redirectTo, returnTo: explicitReturnTo, throwOnInvalid } = args

    if (!throwOnInvalid) {
        return { user: null }
    }

    session.set("returnTo", deriveReturnTo(request, explicitReturnTo))
    const headers = {
        "Set-Cookie": await sessionStorage.commitSession(session),
    }

    throw redirect(redirectTo, { headers })
}

async function handleInvalidSession(args: SessionHandlerArgs): Promise<RequireUserOptionalResult> {
    const { request, session, redirectTo, returnTo: explicitReturnTo, throwOnInvalid } = args

    // Clear session storage
    session.unset(AUTH_SESSION_KEY)
    session.set("returnTo", deriveReturnTo(request, explicitReturnTo))

    // Clear all auth data from localStorage
    clearAuthData()

    const headers = {
        "Set-Cookie": await sessionStorage.commitSession(session),
    }

    if (!throwOnInvalid) {
        return { user: null, headers }
    }

    throw redirect(redirectTo, { headers })
}

// Replace localStorage with a more secure storage mechanism
function _secureStore(key: string, value: unknown) {
    if (value) {
        // TODO: Implement proper encryption using a library like crypto-js
        // For now, using base64 as a placeholder, but this MUST be replaced with secure encryption in production
        const encryptedValue = btoa(JSON.stringify(value))
        // Use global sessionStorage instead of React Router's sessionStorage
        globalThis.sessionStorage.setItem(key, encryptedValue)
    } else {
        const stored = globalThis.sessionStorage.getItem(key)
        if (stored) {
            try {
                // TODO: Implement proper decryption using a library like crypto-js
                return JSON.parse(atob(stored))
            } catch (e) {
                console.error("Failed to decrypt stored data", e)
                globalThis.sessionStorage.removeItem(key)
                return null
            }
        }
        return null
    }
}

export async function register(credentials: RegisterOptions): Promise<RegisterResult> {
    const email = credentials.email.toLowerCase()
    const password = credentials.password ?? DEFAULT_MOCK_PASSWORD
    const record = ensureMockUserRecord(email, password)
    record.user = {
        ...record.user,
        email,
        first_name: credentials.first_name ?? record.user.first_name,
        last_name: credentials.last_name ?? record.user.last_name,
    }

    return {
        message: "User registered successfully (mock mode)",
        user_id: record.user.id.toString(),
    }
}
