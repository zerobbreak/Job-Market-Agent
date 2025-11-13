export interface AuthenticatedUser {
    id: number
    email: string
    first_name: string
    last_name: string
    is_active: boolean
    user_permissions?: string[]
}

export interface AuthSessionData {
    user: AuthenticatedUser
    accessToken: string
    refreshToken?: string
    issuedAt: number
    expiresAt?: number
}

export interface SignInResult {
    user: AuthenticatedUser
    headers: Record<string, string>
    returnTo?: string
    accessToken: string
    refreshToken?: string
    issuedAt: number
    expiresAt?: number
}

export interface RequireUserResult {
    user: AuthenticatedUser
    headers?: Record<string, string>
    accessToken?: string
}

export interface RequireUserOptionalResult {
    user: AuthenticatedUser | null
    headers?: Record<string, string>
}

export interface RequireUserOptions {
    redirectTo?: string
    returnTo?: string
    refresh?: "auto" | "force"
    throwOnInvalid?: boolean
}

export interface SignInOptions {
    email: string
    password: string
}

export interface RegisterOptions {
    username: string
    first_name?: string
    last_name?: string
    email: string
    password: string
    route?: string
}

export interface RegisterResult {
    message: string
    user_id: string
}

export interface RegisterError {
    username?: string[]
    email?: string[]
    password?: string[]
    first_name?: string[]
    last_name?: string[]
    route?: string[]
    error?: string
}

export interface TokenPair {
    access: string
    refresh?: string
}

export interface AuthProviderError {
    detail?: string
    message?: string
    non_field_errors?: string[]
}
