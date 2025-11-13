import { useCallback, useEffect, useState } from "react"
import { useNavigate } from "react-router"
import type { AuthenticatedUser } from "../../@types/auth.types"

/**
 * Authentication state
 */
interface AuthState {
    user: AuthenticatedUser | null
    loading: boolean
    error: Error | null
}

/**
 * Custom hook for managing authentication state
 * Provides convenient access to user authentication status and methods
 *
 * @returns Authentication state and methods
 *
 * @example
 * ```tsx
 * const { user, loading, logout } = useAuth();
 *
 * if (loading) return <Spinner />;
 * if (!user) return <LoginPrompt />;
 *
 * return <Dashboard user={user} onLogout={logout} />;
 * ```
 */
export function useAuth() {
    const navigate = useNavigate()
    const [authState, setAuthState] = useState<AuthState>({
        user: null,
        loading: true,
        error: null,
    })

    // Load user from localStorage on mount
    useEffect(() => {
        const loadUser = () => {
            try {
                const storedAuth = localStorage.getItem("auth")
                if (storedAuth) {
                    const authData = JSON.parse(storedAuth)
                    if (authData.user) {
                        setAuthState({
                            user: authData.user,
                            loading: false,
                            error: null,
                        })
                        return
                    }
                }
                // No valid auth data found
                setAuthState({
                    user: null,
                    loading: false,
                    error: null,
                })
            } catch (error) {
                setAuthState({
                    user: null,
                    loading: false,
                    error:
                        error instanceof Error
                            ? error
                            : new Error("Failed to load authentication data"),
                })
            }
        }

        loadUser()
    }, [])

    // Logout function
    const logout = useCallback(async () => {
        try {
            setAuthState((prev) => ({ ...prev, loading: true }))

            // Clear auth state immediately for better UX
            setAuthState({
                user: null,
                loading: false,
                error: null,
            })

            // Navigate to login (the auth service handles the actual logout)
            navigate("/login")
        } catch (error) {
            setAuthState({
                user: null,
                loading: false,
                error: error instanceof Error ? error : new Error("Logout failed"),
            })
        }
    }, [navigate])

    // Refresh user data (reload from localStorage)
    const refreshUser = useCallback(() => {
        try {
            const storedAuth = localStorage.getItem("auth")
            if (storedAuth) {
                const authData = JSON.parse(storedAuth)
                if (authData.user) {
                    setAuthState({
                        user: authData.user,
                        loading: false,
                        error: null,
                    })
                    return
                }
            }
            // No valid auth data found
            setAuthState({
                user: null,
                loading: false,
                error: null,
            })
        } catch (error) {
            setAuthState({
                user: null,
                loading: false,
                error: error instanceof Error ? error : new Error("Failed to refresh user data"),
            })
        }
    }, [])

    return {
        user: authState.user,
        loading: authState.loading,
        error: authState.error,
        isAuthenticated: !!authState.user,
        logout,
        refreshUser,
    }
}
