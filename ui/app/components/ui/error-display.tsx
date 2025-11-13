import { ArrowPathIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline"

interface ErrorDisplayProps {
    error: Error | string
    onRetry?: () => void
    title?: string
    className?: string
}

export function ErrorDisplay({
    error,
    onRetry,
    title = "Something went wrong",
    className = "",
}: ErrorDisplayProps) {
    const errorMessage = typeof error === "string" ? error : error.message

    return (
        <div className={`penpot-card p-6 text-center ${className}`}>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />
            </div>

            <h3 className="penpot-heading-medium mb-2 text-[#151515]">{title}</h3>

            <p className="penpot-body-large text-[#7a7a7a] mb-6">{errorMessage}</p>

            {onRetry && (
                <button
                    type="button"
                    onClick={onRetry}
                    className="penpot-button-primary flex items-center gap-2 mx-auto"
                >
                    <ArrowPathIcon className="w-4 h-4" />
                    Try Again
                </button>
            )}
        </div>
    )
}

interface LoadingDisplayProps {
    message?: string
    className?: string
}

export function LoadingDisplay({ message = "Loading...", className = "" }: LoadingDisplayProps) {
    return (
        <div className={`penpot-card p-6 text-center ${className}`}>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="loading-spinner" />
            </div>

            <h3 className="penpot-heading-medium mb-2 text-[#151515]">{message}</h3>

            <p className="penpot-body-large text-[#7a7a7a]">
                Please wait while we process your request...
            </p>
        </div>
    )
}

interface EmptyStateDisplayProps {
    title: string
    description: string
    action?: {
        label: string
        onClick: () => void
    }
    icon?: React.ReactNode
    className?: string
}

export function EmptyStateDisplay({
    title,
    description,
    action,
    icon,
    className = "",
}: EmptyStateDisplayProps) {
    return (
        <div className={`penpot-card p-12 text-center ${className}`}>
            {icon && (
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    {icon}
                </div>
            )}

            <h3 className="penpot-heading-medium mb-4 text-[#151515]">{title}</h3>

            <p className="penpot-body-large text-[#7a7a7a] mb-6 max-w-md mx-auto">{description}</p>

            {action && (
                <button type="button" onClick={action.onClick} className="penpot-button-primary">
                    {action.label}
                </button>
            )}
        </div>
    )
}
