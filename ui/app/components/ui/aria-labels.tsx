// ARIA Labels and Accessibility Utilities

export const ariaLabels = {
    // Navigation
    mainNavigation: "Main navigation",
    userMenu: "User account menu",
    sidebarToggle: "Toggle sidebar",
    aiPanelToggle: "Toggle AI assistant panel",

    // Actions
    createCase: "Create new case",
    createCaseMaterial: "Create new case material",
    uploadFiles: "Upload files",
    downloadDocument: "Download document",
    copyText: "Copy text to clipboard",
    exportData: "Export data",

    // Forms
    caseTitle: "Case title input",
    caseMaterialType: "Case material type selection",
    searchInput: "Search input",
    messageInput: "Message input",

    // Status
    loading: "Loading content",
    processing: "Processing request",
    completed: "Operation completed",
    error: "Error occurred",

    // File operations
    fileUpload: "File upload area",
    fileList: "List of uploaded files",
    fileStatus: "File processing status",

    // AI Features
    aiAssistant: "AI legal assistant",
    aiAnalysis: "AI analysis results",
    aiSuggestion: "AI suggestion",

    // Case material types
    factsCaseMaterial: "Facts and evidence case material",
    researchCaseMaterial: "Legal research case material",
    draftingCaseMaterial: "Document drafting case material",
} as const

export const keyboardShortcuts = {
    // Navigation
    toggleSidebar: "Ctrl+B",
    toggleAIPanel: "Ctrl+A",
    newCase: "Ctrl+N",
    search: "Ctrl+K",

    // Actions
    save: "Ctrl+S",
    copy: "Ctrl+C",
    paste: "Ctrl+V",
    undo: "Ctrl+Z",
    redo: "Ctrl+Y",
} as const

// Hook for keyboard navigation
export function useKeyboardNavigation() {
    const handleKeyDown = (event: React.KeyboardEvent) => {
        // Escape key to close modals/dropdowns
        if (event.key === "Escape") {
            // Close any open modals or dropdowns
            const activeElement = document.activeElement as HTMLElement
            if (activeElement?.blur) {
                activeElement.blur()
            }
        }

        // Enter key for buttons and links
        if (event.key === "Enter" && event.target instanceof HTMLElement) {
            if (event.target.tagName === "BUTTON" || event.target.tagName === "A") {
                event.target.click()
            }
        }
    }

    return { handleKeyDown }
}

// Component for announcing screen reader updates
export function ScreenReaderAnnouncement({
    message,
    priority = "polite",
}: {
    message: string
    priority?: "polite" | "assertive"
}) {
    return (
        <div aria-live={priority} aria-atomic="true" className="sr-only">
            {message}
        </div>
    )
}

// Skip to main content link
export function SkipToMainContent({ targetId = "main-content" }: { targetId?: string }) {
    return (
        <a
            href={`#${targetId}`}
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-[#4b92ff] text-white px-4 py-2 rounded-lg z-50"
        >
            Skip to main content
        </a>
    )
}
