import { useId, useState } from "react"
import { useLocation, useNavigate } from "react-router"
import type { Job, JobMaterial } from "../../../@types/job.types"

interface JobSidebarProps {
    jobId?: string
    jobData?: Job
    jobMaterials?: JobMaterial[]
    onJobMaterialCreate?: () => void
    onNewJobMaterial?: () => void
}

export function JobSidebar({
    jobId,
    jobData: _jobData,
    jobMaterials = [],
    onJobMaterialCreate: _onJobMaterialCreate,
    onNewJobMaterial: _onNewJobMaterial,
}: JobSidebarProps) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true)
    const location = useLocation()
    const navigate = useNavigate()
    const expandTitleId = useId()
    const collapseTitleId = useId()

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen)
    }

    // Dynamic sidebar navigation based on job materials
    const sidebarItems = [
        // Add all job materials dynamically
        ...jobMaterials.map((jobMaterial) => ({
            label: jobMaterial.title,
            href: `/jobs/${jobId}/job-materials/${jobMaterial.id}`,
            current: location.pathname === `/jobs/${jobId}/job-materials/${jobMaterial.id}`,
            type: jobMaterial.type,
            status: jobMaterial.status,
            jobMaterial: jobMaterial,
        })),
    ]

    // Handle navigation - use proper routing for all links
    const handleNavigation = (href: string) => {
        navigate(href)
    }

    if (!isSidebarOpen) {
        return (
            <div className="hidden md:flex relative flex flex-col items-center justify-start pt-4 bg-[#f7f4ed] border-r border-[#edebe5] w-12 lg:w-16 h-screen">
                <button
                    type="button"
                    onClick={toggleSidebar}
                    className="p-2 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                    aria-label="Expand Sidebar"
                >
                    <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-labelledby={expandTitleId}
                    >
                        <title id={expandTitleId}>Expand sidebar</title>
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                        />
                    </svg>
                </button>
            </div>
        )
    }

    return (
        <div className="hidden md:flex w-[180px] lg:w-[280px] bg-[#f7f4ed] border-r border-[#edebe5] flex-col h-screen">
            {/* Sidebar Header */}
            <div className="flex items-center justify-end px-4 py-4">
                {/* Collapse Button */}
                <button
                    type="button"
                    onClick={toggleSidebar}
                    className="p-1 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                    aria-label="Collapse Sidebar"
                >
                    <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        role="img"
                        aria-labelledby={collapseTitleId}
                    >
                        <title id={collapseTitleId}>Collapse sidebar</title>
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 19l-7-7 7-7"
                        />
                    </svg>
                </button>
            </div>

            {/* New Job Material Button */}
            <button
                type="button"
                onClick={() => navigate(`/jobs/${jobId}/new-job-material`)}
                className="flex items-center gap-2 px-4 py-2 bg-[#f7f4ed] border-none rounded-lg text-sm font-medium cursor-pointer mb-8 hover:bg-[#edebe5] transition-colors w-full justify-start"
            >
                <span className="text-sm">+</span>
                <span>New Job Material</span>
            </button>

            {/* Job Materials List - Design Style */}
            <div className="flex-1 overflow-y-auto">
                {/* Today Group */}
                <div className="mb-3">
                    <div className="text-sm text-[#7a7a7a] px-4 pb-2">Job Materials</div>
                    {sidebarItems.map((item, index) => (
                        <button
                            type="button"
                            key={`${item.href}-${index}`}
                            onClick={() => handleNavigation(item.href)}
                            className={`w-full px-4 py-3 rounded-lg text-sm font-medium cursor-pointer mb-2 transition-colors min-h-[48px] flex items-center ${
                                item.current
                                    ? "bg-white shadow-[0px_1px_2px_0px_rgba(211,207,193,0.8)]"
                                    : "hover:bg-white"
                            }`}
                        >
                            <div className="flex items-center justify-between w-full">
                                <span className="truncate flex-1 text-left leading-tight">
                                    {item.label}
                                </span>
                                {"status" in item && item.status && (
                                    <div
                                        className={`w-2 h-2 rounded-full ml-2 flex-shrink-0 ${
                                            item.status === "processing"
                                                ? "bg-yellow-400"
                                                : item.status === "completed"
                                                  ? "bg-green-400"
                                                  : item.status === "error"
                                                    ? "bg-red-400"
                                                    : "bg-gray-400"
                                        }`}
                                    />
                                )}
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Workspace Section - Design Style */}
            <div className="px-4 py-2 bg-[#f7f4ee] border border-[#edebe5] rounded-lg flex items-center justify-between text-sm font-medium cursor-pointer">
                <button
                    type="button"
                    onClick={() => navigate("/jobs")}
                    className="flex-1 text-left hover:bg-transparent"
                >
                    <span>Workspace</span>
                </button>
                <span>→</span>
            </div>

            {/* Upload Icon - Bottom Right of Expanded Sidebar */}
            <button
                type="button"
                onClick={() => navigate(`/jobs/${jobId}`)}
                className="absolute bottom-6 right-4 p-3 bg-[#4b92ff] text-white rounded-full shadow-lg hover:bg-[#3a7be0] transition-colors"
                title="Upload Files"
            >
                <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    role="img"
                    aria-label="Upload"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                </svg>
            </button>
        </div>
    )
}
