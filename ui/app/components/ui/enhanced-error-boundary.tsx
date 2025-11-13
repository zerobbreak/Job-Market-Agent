import { Component, type ReactNode } from "react"
import { isRouteErrorResponse } from "react-router"
import { logger } from "~/utils/logger"
import { Button } from "./button"

interface EnhancedErrorBoundaryState {
    hasError: boolean
    error?: Error
    errorId: string
    retryCount: number
    lastErrorTime?: Date
}

interface EnhancedErrorBoundaryProps {
    children: ReactNode
    fallback?: ReactNode
    maxRetries?: number
    retryDelay?: number
    onError?: (error: Error, errorInfo: unknown) => void
    onRetry?: () => void
    showTechnicalDetails?: boolean
    context?: string
}

export class EnhancedErrorBoundary extends Component<
    EnhancedErrorBoundaryProps,
    EnhancedErrorBoundaryState
> {
    private retryTimeoutId?: NodeJS.Timeout

    constructor(props: EnhancedErrorBoundaryProps) {
        super(props)
        this.state = {
            hasError: false,
            errorId: "",
            retryCount: 0,
        }
    }

    static getDerivedStateFromError(error: Error): Partial<EnhancedErrorBoundaryState> {
        // Generate unique error ID for tracking
        const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

        return {
            hasError: true,
            error,
            errorId,
            lastErrorTime: new Date(),
        }
    }

    componentDidCatch(error: Error, errorInfo: unknown) {
        const { context, onError, maxRetries = 3 } = this.props
        const { errorId, retryCount } = this.state

        // Log error with context
        logger.error(`ErrorBoundary caught error in ${context || "unknown context"}`, error, {
            errorId,
            retryCount,
            component: context,
            userAgent: navigator.userAgent,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            errorInfo,
        })

        // Call custom error handler if provided
        onError?.(error, errorInfo)

        // Auto-retry for certain types of errors if within retry limit
        if (this.shouldAutoRetry(error) && retryCount < maxRetries) {
            this.scheduleRetry()
        }
    }

    componentWillUnmount() {
        if (this.retryTimeoutId) {
            clearTimeout(this.retryTimeoutId)
        }
    }

    private shouldAutoRetry(error: Error): boolean {
        // Auto-retry for network errors, timeouts, and temporary failures
        const retryableErrors = [
            "NetworkError",
            "TimeoutError",
            "TypeError: Failed to fetch",
            "TypeError: Network request failed",
        ]

        return retryableErrors.some(
            (retryableError) =>
                error.message.includes(retryableError) || error.name.includes(retryableError)
        )
    }

    private scheduleRetry() {
        const { retryDelay = 2000 } = this.props

        this.retryTimeoutId = setTimeout(() => {
            logger.info("Attempting error recovery", {
                errorId: this.state.errorId,
                retryCount: this.state.retryCount + 1,
            })

            this.setState((prevState) => ({
                hasError: false,
                error: undefined,
                retryCount: prevState.retryCount + 1,
            }))

            this.props.onRetry?.()
        }, retryDelay)
    }

    private handleManualRetry = () => {
        logger.info("Manual error recovery initiated", {
            errorId: this.state.errorId,
            retryCount: this.state.retryCount + 1,
        })

        this.setState((prevState) => ({
            hasError: false,
            error: undefined,
            retryCount: prevState.retryCount + 1,
        }))

        this.props.onRetry?.()
    }

    private handleReportError = () => {
        const { error, errorId } = this.state

        // In a real app, this would send error report to monitoring service
        const errorReport = {
            errorId,
            message: error?.message,
            stack: error?.stack,
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString(),
            retryCount: this.state.retryCount,
        }

        logger.info("Error report generated", { errorReport })

        // Copy error details to clipboard for manual reporting
        navigator.clipboard
            .writeText(JSON.stringify(errorReport, null, 2))
            .then(() => {
                alert("Error details copied to clipboard. Please include this in your bug report.")
            })
            .catch(() => {
                alert(
                    "Error details generated. Please check the console for details to include in your bug report."
                )
                console.log("Error Report:", errorReport)
            })
    }

    render() {
        const { hasError, error, errorId, retryCount } = this.state
        const { fallback, showTechnicalDetails = import.meta.env.DEV } = this.props

        if (!hasError) {
            return this.props.children
        }

        // Use custom fallback if provided
        if (fallback) {
            return fallback
        }

        // Route error response handling
        if (error && isRouteErrorResponse(error)) {
            return (
                <div className="min-h-screen bg-[#fcfbf8] flex items-center justify-center p-4">
                    <div className="penpot-card p-8 max-w-md w-full text-center">
                        <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <svg
                                className="w-8 h-8 text-orange-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                                />
                            </svg>
                        </div>

                        <div className="mb-4">
                            <span className="penpot-caption font-medium text-orange-800">
                                Route Error {error.status}
                            </span>
                        </div>

                        <h1 className="penpot-heading-large mb-4 text-[#151515]">
                            {error.status === 404 ? "Page Not Found" : "Route Error"}
                        </h1>

                        <p className="penpot-body-large text-[#7a7a7a] mb-8">
                            {error.status === 404
                                ? "Sorry, we couldn't find the page you're looking for."
                                : error.statusText || "An unexpected routing error occurred."}
                        </p>

                        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
                            <Button onClick={() => (window.location.href = "/")}>Go Home</Button>
                            <Button color="white" onClick={() => window.history.back()}>
                                Go Back
                            </Button>
                        </div>

                        <div className="text-xs text-[#7a7a7a]">Error ID: {errorId}</div>
                    </div>
                </div>
            )
        }

        // Generic error handling
        return (
            <div className="min-h-screen bg-[#fcfbf8] flex items-center justify-center p-4">
                <div className="penpot-card p-8 max-w-lg w-full text-center">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg
                            className="w-8 h-8 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                            />
                        </svg>
                    </div>

                    <h1 className="penpot-heading-large mb-4 text-[#151515]">
                        Something went wrong
                    </h1>

                    <p className="penpot-body-large text-[#7a7a7a] mb-6">
                        An unexpected error occurred. We've logged this error for investigation.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
                        <Button onClick={this.handleManualRetry}>Try Again</Button>
                        <Button color="white" onClick={() => window.location.reload()}>
                            Refresh Page
                        </Button>
                        <Button color="white" onClick={this.handleReportError}>
                            Report Error
                        </Button>
                    </div>

                    <div className="text-xs text-[#7a7a7a] space-y-1">
                        <div>Error ID: {errorId}</div>
                        <div>Retry attempts: {retryCount}</div>
                    </div>

                    {showTechnicalDetails && error && (
                        <details className="mt-6 text-left">
                            <summary className="penpot-body-medium font-medium cursor-pointer mb-2">
                                Technical Details (Development Only)
                            </summary>
                            <div className="space-y-4">
                                <div>
                                    <h4 className="font-medium text-sm mb-1">Error Message:</h4>
                                    <pre className="text-xs bg-red-50 p-2 rounded border overflow-x-auto">
                                        {error.message}
                                    </pre>
                                </div>
                                {error.stack && (
                                    <div>
                                        <h4 className="font-medium text-sm mb-1">Stack Trace:</h4>
                                        <pre className="text-xs bg-gray-50 p-2 rounded border overflow-x-auto max-h-40">
                                            {error.stack}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </details>
                    )}
                </div>
            </div>
        )
    }
}

// Hook for functional components to use error boundary behavior
export function useErrorHandler() {
    return (error: Error, errorInfo?: unknown) => {
        logger.error("Error caught by useErrorHandler", error, {
            errorInfo,
            component: "useErrorHandler",
        })
    }
}
