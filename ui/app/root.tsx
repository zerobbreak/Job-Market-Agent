"use client"

import type React from "react"

import {
    isRouteErrorResponse,
    Link,
    Links,
    Meta,
    Outlet,
    redirect,
    Scripts,
    ScrollRestoration,
    useLoaderData,
} from "react-router"

import type { Route } from "./+types/root"
import "./app.css"
import AppShell from "./components/shared/app-shell"
import { requireUser } from "./services/auth.client"

export const links: Route.LinksFunction = () => [
    { rel: "preconnect", href: "https://fonts.googleapis.com" },
    {
        rel: "preconnect",
        href: "https://fonts.gstatic.com",
        crossOrigin: "anonymous",
    },
    {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
    },
]

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
    try {
        // Get current URL to check if we're on a public page
        const url = new URL(request.url)
        const publicPaths = [
            "/",
            "/learn",
            "/login",
            "/register",
            "/activate",
            "/forgot-password",
            "/logout",
            "/refresh",
        ]
        const isPublicPage = publicPaths.includes(url.pathname)

        // For public pages, check auth but don't redirect
        if (isPublicPage) {
            try {
                const result = await requireUser(request, { throwOnInvalid: false })

                // If user is authenticated and landed on an entry page, redirect to jobs
                const entryRedirectPaths = new Set([
                    "/",
                    "/login",
                    "/register",
                    "/activate",
                    "/forgot-password",
                ])
                if (result.user && entryRedirectPaths.has(url.pathname)) {
                    throw redirect("/jobs")
                }

                // If no user found, make sure localStorage is also cleared
                // Note: localStorage clearing will happen on the client side via clearAuthData()
                // We don't need to do it here as the client will handle auth state synchronization

                return { user: result.user || null }
            } catch (error) {
                // If there's any error on public pages, clear auth data and return no user
                console.warn("[Root] Error loading user on public page:", error)
                // Note: localStorage clearing will happen on the client side via clearAuthData()
                // We don't need to do it here as the client will handle auth state synchronization
                return { user: null }
            }
        }

        // For protected pages, validate and refresh token on page load
        // This ensures tokens are checked/refreshed on every page refresh
        // If refresh fails (expired tokens), user will be redirected to login
        const result = await requireUser(request, {
            refresh: "auto", // Automatically refresh if token expired or about to expire
            throwOnInvalid: true, // Redirect to login if tokens invalid or refresh fails
            redirectTo: "/", // Redirect to home page instead of /login
        })

        return { user: result.user }
    } catch (error) {
        // Check if this is a redirect response (which is expected behavior)
        if (
            error &&
            typeof error === "object" &&
            "status" in error &&
            (error as { status?: number }).status === 302
        ) {
            // This is a redirect response from requireUser - let it bubble up
            throw error as Response
        }

        // For any other errors, log and redirect to home
        console.error("[Root] Unexpected error in clientLoader:", error)

        // Note: localStorage clearing will happen on the client side via clearAuthData()
        // We don't need to do it here as the client will handle auth state synchronization

        // Redirect to home page to avoid infinite loops
        throw redirect("/")
    }
}

export function Layout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en">
            <head>
                <meta charSet="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <Meta />
                <Links />
            </head>
            <body>
                <div id="root">{children}</div>
                <ScrollRestoration />
                <Scripts />
            </body>
        </html>
    )
}

export default function App() {
    const loaderData = useLoaderData<typeof clientLoader>()
    const user = loaderData?.user ?? null

    return (
        <AppShell user={user}>
            <Outlet />
        </AppShell>
    )
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
    let message = "Oops!"
    let details = "An unexpected error occurred."
    let stack: string | undefined
    let statusCode = "500"

    if (isRouteErrorResponse(error)) {
        statusCode = error.status.toString()
        message = error.status === 404 ? "Page Not Found" : "Error"
        details =
            error.status === 404
                ? "Sorry, we couldn't find the page you're looking for."
                : error.statusText || details
    } else if (import.meta.env.DEV && error && error instanceof Error) {
        details = error.message
        stack = error.stack
    }

    return (
        <main className="min-h-screen bg-[#fcfbf8] flex items-center justify-center p-4">
            <div className="penpot-card p-8 max-w-md w-full text-center">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg
                        className="w-8 h-8 text-red-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-label="Error"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                        />
                    </svg>
                </div>

                <div className="ai-error mb-4">
                    <span className="penpot-caption font-medium text-red-800">
                        Error {statusCode}
                    </span>
                </div>

                <h1 className="penpot-heading-large mb-4 text-[#151515]">{message}</h1>

                <p className="penpot-body-large text-[#7a7a7a] mb-8">{details}</p>

                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Link to="/" className="penpot-button-primary">
                        Go back home
                    </Link>
                    <button
                        type="button"
                        onClick={() => window.history.back()}
                        className="penpot-button-secondary"
                    >
                        Go back
                    </button>
                </div>

                {import.meta.env.DEV && stack && (
                    <details className="mt-8 text-left">
                        <summary className="penpot-body-medium font-medium cursor-pointer mb-2">
                            Technical Details
                        </summary>
                        <pre className="w-full p-4 overflow-x-auto bg-[#f7f4ed] rounded-lg text-xs">
                            <code>{stack}</code>
                        </pre>
                    </details>
                )}
            </div>
        </main>
    )
}

// Custom Error Boundary Component
