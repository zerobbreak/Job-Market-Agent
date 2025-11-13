import { useState } from "react"
import { Outlet, useNavigate, useParams } from "react-router"
import { JobSidebar } from "~/components/shared/job-sidebar"
import { AIChatPanel } from "~/components/ui/ai-chat-panel"
import { ErrorBoundary } from "~/components/ui/error-boundary"
import { requireUser } from "~/services/auth.client"
import { getJob } from "~/services/job.client"
import { useCaseData } from "~/services/state/state.client"
import type { Route } from "./+types/job-layout"

export function meta({}: Route.MetaArgs) {
    return [
        { title: "Job Details" },
        { name: "description", content: "Job Market Agent - Job Details" },
    ]
}

export async function clientLoader({ request, params }: Route.ClientLoaderArgs) {
    const result = await requireUser(request)

    // Fetch the specific case data
    const caseData = await getJob(params.jobId)

    if (!caseData) {
        throw new Response("Case not found", { status: 404 })
    }

    return {
        user: result.user,
        accessToken: result.accessToken,
        caseData,
    }
}

export default function CaseLayout({
    loaderData,
    children,
}: Route.ComponentProps & { children?: React.ReactNode }) {
    // Get caseId from URL params using useParams hook
    const params = useParams()
    const navigate = useNavigate()
    const caseId = params.caseId // Get caseId from route params

    const { caseData, accessToken } = loaderData
    // Use global store instead of local state - call hooks unconditionally
    const { caseMaterials, uploads } = useCaseData(caseId || "")
    const [isAIPanelOpen, setIsAIPanelOpen] = useState(true)

    // Early return if no caseId (shouldn't happen with proper routing)
    if (!caseId) {
        return (
            <div className="min-h-screen bg-white flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-xl font-medium text-red-600 mb-2">Invalid Case</h2>
                    <p className="text-gray-600">No case ID provided in the URL.</p>
                </div>
            </div>
        )
    }

    const toggleAIPanel = () => {
        setIsAIPanelOpen(!isAIPanelOpen)
    }

    return (
        <ErrorBoundary
            fallback={
                <div className="min-h-screen flex items-center justify-center bg-[#fcfbf8]">
                    <div className="text-center">
                        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg
                                className="w-8 h-8 text-red-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Error icon"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                                />
                            </svg>
                        </div>
                        <h2 className="penpot-heading-medium mb-2">Something went wrong</h2>
                        <p className="penpot-body-medium text-[#7a7a7a] mb-4">
                            We encountered an error loading this case. Please try refreshing the
                            page.
                        </p>
                        <button
                            type="button"
                            onClick={() => window.location.reload()}
                            className="penpot-button-primary"
                        >
                            Refresh Page
                        </button>
                    </div>
                </div>
            }
        >
            <div className="flex h-screen bg-[#fcfbf8] overflow-hidden">
                {/* Left Sidebar - Using Shared Component */}
                <JobSidebar jobId={caseId} jobData={caseData} jobMaterials={caseMaterials} />

                {/* Mobile Navigation Header - Shows when sidebar is hidden */}
                <div className="md:hidden bg-white border-b border-[#edebe5] px-4 py-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <button
                                type="button"
                                onClick={() => navigate(`/cases/${caseId}`)}
                                className="p-2 text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] rounded-lg transition-colors"
                            >
                                <svg
                                    className="w-5 h-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    role="img"
                                    aria-label="Back"
                                >
                                    <title>Back</title>
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M15 19l-7-7 7-7"
                                    />
                                </svg>
                            </button>
                            <div>
                                <h1 className="penpot-body-medium font-medium truncate">
                                    {caseData?.title || "Case"}
                                </h1>
                                <p className="penpot-caption text-[#7a7a7a]">Case ID: {caseId}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={() => {
                                    window.location.href = "/cases"
                                }}
                                className="p-2 text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] rounded-lg transition-colors"
                                title="Back to Cases"
                            >
                                <svg
                                    className="w-5 h-5"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    role="img"
                                    aria-label="Cases"
                                >
                                    <title>Back to Cases</title>
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"
                                    />
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M8 5a2 2 0 012-2h4a2 2 0 012 2v0"
                                    />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Main Content Area - Always present and expands when panels collapse */}
                <div className="flex-1 flex flex-col min-w-0">
                    {/* Case Header - Always visible */}
                    <div className="border-b border-[#edebe5] px-6 lg:px-[60px] py-6">
                        <div className="text-[16px] font-semibold mb-2">
                            {caseData?.title || "Loading..."}
                        </div>
                        <div className="text-[12px] text-[#7a7a7a]">
                            Last updated{" "}
                            {new Date(caseData?.updatedAt || Date.now()).toLocaleDateString()}
                        </div>
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 overflow-y-auto px-6 lg:px-[60px] py-6 lg:py-10 relative">
                        {/* Page Content - Dynamic case material content */}
                        <ErrorBoundary
                            fallback={
                                <div className="min-h-96 flex items-center justify-center">
                                    <div className="text-center">
                                        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
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
                                        <h3 className="penpot-heading-medium mb-2 text-[#151515]">
                                            Content Error
                                        </h3>
                                        <p className="penpot-body-medium text-[#7a7a7a] mb-4">
                                            There was an error loading this case content. Please try
                                            refreshing the page.
                                        </p>
                                        <button
                                            type="button"
                                            onClick={() => window.location.reload()}
                                            className="penpot-button-primary"
                                        >
                                            Refresh Page
                                        </button>
                                    </div>
                                </div>
                            }
                        >
                            <Outlet />
                            {children}
                        </ErrorBoundary>
                    </div>
                </div>

                {/* AI Panel - Collapsible */}
                {isAIPanelOpen ? (
                    <div className="w-56 lg:w-96 h-screen">
                        <AIChatPanel
                            isOpen={isAIPanelOpen}
                            onToggle={toggleAIPanel}
                            caseId={caseId}
                            availableContexts={[
                                "Facts",
                                "Research",
                                "Drafting",
                                "Evidence",
                                "Notes",
                                "Custom",
                            ]}
                            availableCasefiles={
                                uploads
                                    ? ([
                                          ...new Set(
                                              uploads.map((file) => file.name || "Unknown file")
                                          ),
                                      ] as string[])
                                    : []
                            }
                            accessToken={accessToken}
                        />
                    </div>
                ) : (
                    /* Collapsed AI Panel */
                    <div className="hidden md:flex flex-col items-center justify-start pt-4 bg-[#f7f4ed] border-l border-[#edebe5] w-12 lg:w-16 h-screen">
                        <button
                            type="button"
                            onClick={toggleAIPanel}
                            className="p-2 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                            aria-label="Expand AI Assistant"
                        >
                            <svg
                                className="w-5 h-5"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Expand AI"
                            >
                                <title>Expand AI Assistant</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M15 19l-7-7 7-7"
                                />
                            </svg>
                        </button>
                    </div>
                )}
            </div>
        </ErrorBoundary>
    )
}
