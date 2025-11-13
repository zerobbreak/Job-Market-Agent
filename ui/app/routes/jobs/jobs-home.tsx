// import { TokenRefresh } from "~/components/shared/token-refresh";

import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"
import { JobCard } from "~/components/ui/job-card"
import { CreateJobModal } from "~/components/ui/create-job-modal"
import { FilterSelect } from "~/components/ui/filter-select"
import { SearchBar } from "~/components/ui/search-bar"
import { requireUser } from "~/services/auth.client"
import { deleteCase as apiDeleteCase, getCases } from "~/services/job.client"
import { useCases } from "~/services/state/state.client" // New local store hook
import type { Route } from "./+types/jobs-home"

// Mock job discovery results
interface JobDiscoveryResult {
    id: string
    title: string
    company: string
    location: string
    salary?: string
    platform: string
    postedDate: string
    description: string
    tags: string[]
}

const mockJobResults: JobDiscoveryResult[] = [
    {
        id: "job-1",
        title: "Senior Software Engineer",
        company: "TechCorp",
        location: "Mountain View, CA",
        salary: "$150k - $220k",
        platform: "LinkedIn",
        postedDate: "2 days ago",
        description: "Join our team building next-gen AI applications...",
        tags: ["React", "TypeScript", "Python", "AWS"]
    },
    {
        id: "job-2",
        title: "Full Stack Developer",
        company: "StartupX",
        location: "San Francisco, CA",
        salary: "$120k - $160k",
        platform: "Indeed",
        postedDate: "1 day ago",
        description: "Looking for a passionate developer to join our growing team...",
        tags: ["JavaScript", "Node.js", "PostgreSQL", "Docker"]
    },
    {
        id: "job-3",
        title: "DevOps Engineer",
        company: "CloudTech",
        location: "Austin, TX",
        salary: "$130k - $180k",
        platform: "Glassdoor",
        postedDate: "3 days ago",
        description: "Manage our cloud infrastructure and deployment pipelines...",
        tags: ["Kubernetes", "AWS", "Terraform", "Jenkins"]
    }
]

export function meta({}: Route.MetaArgs) {
    return [
        { title: "Jobs Index" },
        { name: "description", content: "Job Market Agent - Jobs Index" },
    ]
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
    const result = await requireUser(request)

    // Only fetch jobs from API if not using mock data
    // Mock data is initialized in the store automatically in development
    const useMockData =
        import.meta.env.VITE_USE_MOCK_DATA === "true" ||
        (import.meta.env.DEV && import.meta.env.VITE_USE_MOCK_DATA !== "false")

    if (!useMockData) {
        // In production or when mock data is disabled, fetch from API
        await getCases(result.accessToken)
    }

    return {
        user: result.user,
        accessToken: result.accessToken,
        // Cases data is managed by the LocalStore and useCases hook
    }
}

export default function JobsHome({ loaderData }: Route.ComponentProps) {
    const { user, accessToken } = loaderData
    const _navigate = useNavigate()
    const [searchParams] = useSearchParams()

    // Use the new local store hook
    const { cases, addCase } = useCases()

    // Check if user explicitly wants workspace view (bypass single job redirect)
    const _forceWorkspace = searchParams.get("workspace") === "true"

    // Removed single job redirect - users stay on workspace page

    // Check if there are no jobs for empty state
    const hasCases = cases.length > 0

    // Filter state for applications
    const [searchTerm, setSearchTerm] = useState("")
    const [sortBy, setSortBy] = useState("Newest first")
    const [creatorFilter, setCreatorFilter] = useState("All creators")

    // Job discovery state
    const [jobSearchTerm, setJobSearchTerm] = useState("")
    const [jobSearchResults, setJobSearchResults] = useState<JobDiscoveryResult[]>([])
    const [isSearching, setIsSearching] = useState(false)
    const [activeTab, setActiveTab] = useState<"applications" | "discovery">("applications")

    // Modal state
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

    // Filter and sort jobs based on search term, creator filter, and sort option
    const filteredAndSortedCases = cases
        .filter((caseItem) => {
            // Search filter
            const matchesSearch =
                caseItem.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                caseItem.id.toLowerCase().includes(searchTerm.toLowerCase())

            // Creator filter (for now, just check if it's not filtering)
            const matchesCreator = creatorFilter === "All creators" || caseItem.id.includes("user") // This would be replaced with actual user filtering

            return matchesSearch && matchesCreator
        })
        .sort((a, b) => {
            switch (sortBy) {
                case "Newest first":
                    return new Date(b.editedDate).getTime() - new Date(a.editedDate).getTime()
                case "Oldest first":
                    return new Date(a.editedDate).getTime() - new Date(b.editedDate).getTime()
                case "A-Z":
                    return a.title.localeCompare(b.title)
                case "Z-A":
                    return b.title.localeCompare(a.title)
                default:
                    return 0
            }
        })

    // Handle job creation - add the new job to the store
    const handleJobCreated = async (jobId: string, jobTitle: string) => {
        const timestamp = new Date().toISOString()

        const newJob = {
            id: jobId,
            title: jobTitle,
            status: "active" as const,
            createdAt: timestamp,
            updatedAt: timestamp,
            editedDate: timestamp,
            description: "",
            jobMaterials: [],
            uploads: [],
            sessions_count: 0,
            documents_count: 0,
        }

        addCase(newJob)
    }

    // Handle job discovery search
    const handleJobSearch = async (searchQuery: string) => {
        if (!searchQuery.trim()) {
            setJobSearchResults([])
            return
        }

        setIsSearching(true)
        // Simulate API call delay
        setTimeout(() => {
            // Filter mock results based on search query
            const filtered = mockJobResults.filter(job =>
                job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                job.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
                job.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
            )
            setJobSearchResults(filtered)
            setIsSearching(false)
        }, 800) // Simulate network delay
    }

    // Handle creating application from discovered job
    const handleCreateFromJob = (job: JobDiscoveryResult) => {
        const timestamp = new Date().toISOString()
        const newJob = {
            id: `app-${Date.now()}`,
            title: `${job.title} @ ${job.company}`,
            status: "active" as const,
            createdAt: timestamp,
            updatedAt: timestamp,
            editedDate: timestamp,
            description: job.description,
            jobMaterials: [],
            uploads: [],
            sessions_count: 0,
            documents_count: 0,
        }

        addCase(newJob)
        setActiveTab("applications") // Switch to applications tab
    }

    // Handle job deletion
    const handleJobDelete = async (jobId: string) => {
        if (
            !window.confirm(
                "Are you sure you want to delete this job? This action cannot be undone."
            )
        ) {
            return
        }

        try {
            // Delete via API (also updates the store)
            await apiDeleteCase(jobId, accessToken || "")
        } catch (error) {
            console.error("Failed to delete job:", error)
            alert(
                error instanceof Error ? error.message : "Failed to delete job. Please try again."
            )
        }
    }

    return (
        <div className="min-h-screen bg-[#fcfbf8]">
            {/* <TokenRefresh needsRefresh={loaderData.needsRefresh} /> */}

            {/* Workspace Header */}
            <div className="bg-white border-b border-[#edebe5] px-6 py-4">
                <div className="flex items-center justify-between max-w-7xl mx-auto">
                    <div>
                        <h1 className="penpot-heading-large text-[#151515]">
                            {user.first_name} {user.last_name}'s Workspace
                        </h1>
                        <p className="text-[#7a7a7a] mt-1">Manage your job applications and discover new opportunities</p>
                    </div>
                    <button
                        type="button"
                        onClick={() => setIsCreateModalOpen(true)}
                        className="penpot-button-primary"
                    >
                        New Job Application
                    </button>
                </div>
            </div>

            {/* Three-Panel Workspace Layout */}
            <div className="max-w-7xl mx-auto px-6 py-6">
                <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">

                    {/* Left Panel - My Job Applications */}
                    <div className="col-span-3 bg-white rounded-lg border border-[#edebe5] p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="penpot-heading-medium text-[#151515]">My Applications</h2>
                            <span className="text-sm text-[#7a7a7a] bg-[#f7f4ed] px-2 py-1 rounded">
                                {cases.length}
                            </span>
                        </div>

                        {/* Tab Switcher */}
                        <div className="flex gap-1 mb-4 p-1 bg-[#f7f4ed] rounded-lg">
                            <button
                                type="button"
                                onClick={() => setActiveTab("applications")}
                                className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                                    activeTab === "applications"
                                        ? "bg-white text-[#151515] shadow-sm"
                                        : "text-[#7a7a7a] hover:text-[#151515]"
                                }`}
                            >
                                Applications
                            </button>
                            <button
                                type="button"
                                onClick={() => setActiveTab("discovery")}
                                className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                                    activeTab === "discovery"
                                        ? "bg-white text-[#151515] shadow-sm"
                                        : "text-[#7a7a7a] hover:text-[#151515]"
                                }`}
                            >
                                Discovery
                            </button>
                        </div>

                        {/* Application Filters */}
                        <div className="space-y-3 mb-4">
                            <SearchBar
                                placeholder="Search applications"
                                value={searchTerm}
                                onChange={setSearchTerm}
                                className="text-sm"
                            />
                            <FilterSelect
                                options={["All creators", "My jobs", "Shared with me"]}
                                value={creatorFilter}
                                onChange={setCreatorFilter}
                                className="text-sm"
                            />
                        </div>

                        {/* Job Applications List */}
                        <div className="space-y-3 overflow-y-auto max-h-[400px]">
                            {hasCases ? (
                                filteredAndSortedCases.map((caseItem) => (
                                    <div
                                        key={caseItem.id}
                                        className="p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors cursor-pointer border border-transparent hover:border-[#edebe5]"
                                        onClick={() => window.location.href = `/jobs/${caseItem.id}`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1 min-w-0">
                                                <h3 className="font-medium text-[#151515] truncate text-sm">
                                                    {caseItem.title}
                                                </h3>
                                                <p className="text-xs text-[#7a7a7a] mt-1">
                                                    {new Date(caseItem.editedDate).toLocaleDateString()}
                                                </p>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <span className={`px-2 py-1 rounded text-xs ${
                                                        caseItem.status === 'active' ? 'bg-green-100 text-green-700' :
                                                        caseItem.status === 'researching' ? 'bg-blue-100 text-blue-700' :
                                                        'bg-gray-100 text-gray-700'
                                                    }`}>
                                                        {caseItem.status || 'active'}
                                                    </span>
                                                </div>
                                            </div>
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    handleJobDelete(caseItem.id)
                                                }}
                                                className="text-[#7a7a7a] hover:text-red-600 p-1"
                                                title="Delete application"
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-8">
                                    <div className="w-12 h-12 mx-auto mb-3 text-[#7a7a7a]">
                                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                    </div>
                                    <p className="text-sm text-[#7a7a7a]">No applications yet</p>
                                    <button
                                        type="button"
                                        onClick={() => setIsCreateModalOpen(true)}
                                        className="text-sm text-[#4b92ff] hover:text-[#3a7be0] mt-2"
                                    >
                                        Create your first application
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Main Content Area - Job Discovery or Application Details */}
                    <div className="col-span-6 bg-white rounded-lg border border-[#edebe5] p-6">
                        {activeTab === "applications" ? (
                            /* Application Management View */
                            <div>
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="penpot-heading-medium text-[#151515]">Job Applications</h2>
                                    <div className="flex items-center gap-3">
                                        <FilterSelect
                                            options={["Newest first", "Oldest first", "A-Z", "Z-A"]}
                                            value={sortBy}
                                            onChange={setSortBy}
                                            className="text-sm"
                                        />
                                    </div>
                                </div>

                                {hasCases ? (
                                    <div className="grid grid-cols-1 gap-4">
                                        {filteredAndSortedCases.map((caseItem) => (
                                            <div
                                                key={caseItem.id}
                                                className="p-4 border border-[#edebe5] rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                                                onClick={() => window.location.href = `/jobs/${caseItem.id}`}
                                            >
                                                <div className="flex items-center justify-between">
                                                    <div className="flex-1">
                                                        <h3 className="font-medium text-[#151515] mb-1">{caseItem.title}</h3>
                                                        <p className="text-sm text-[#7a7a7a]">
                                                            Last edited {new Date(caseItem.editedDate).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                    <div className="flex items-center gap-3">
                                                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                                            caseItem.status === 'active' ? 'bg-green-100 text-green-700' :
                                                            caseItem.status === 'researching' ? 'bg-blue-100 text-blue-700' :
                                                            'bg-gray-100 text-gray-700'
                                                        }`}>
                                                            {caseItem.status || 'active'}
                                                        </span>
                                                        <button
                                                            type="button"
                                                            onClick={(e) => {
                                                                e.stopPropagation()
                                                                handleJobDelete(caseItem.id)
                                                            }}
                                                            className="text-[#7a7a7a] hover:text-red-600 p-2"
                                                        >
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                            </svg>
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    /* Empty State for Applications */
                                    <div className="text-center py-16">
                                        <div className="w-16 h-16 mx-auto mb-6 text-[#7a7a7a]">
                                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                        </div>
                                        <h3 className="penpot-heading-medium mb-4 text-[#151515]">No Job Applications Yet</h3>
                                        <p className="penpot-body-large text-[#7a7a7a] mb-6 max-w-md mx-auto">
                                            Start your job search journey by creating your first application or discovering jobs across multiple platforms.
                                        </p>
                                        <div className="flex justify-center gap-4">
                                            <button
                                                type="button"
                                                onClick={() => setActiveTab("discovery")}
                                                className="penpot-button-primary"
                                            >
                                                Discover Jobs
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => setIsCreateModalOpen(true)}
                                                className="penpot-button-secondary"
                                            >
                                                Create Application
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            /* Job Discovery View */
                            <div>
                                <div className="mb-6">
                                    <h2 className="penpot-heading-medium text-[#151515] mb-2">Job Discovery</h2>
                                    <p className="text-[#7a7a7a]">Search across 20+ job platforms simultaneously</p>
                                </div>

                                {/* Universal Job Search */}
                                <div className="mb-6">
                                    <div className="relative">
                                        <SearchBar
                                            placeholder="Search for jobs, companies, or skills..."
                                            value={jobSearchTerm}
                                            onChange={(value) => {
                                                setJobSearchTerm(value)
                                                handleJobSearch(value)
                                            }}
                                            className="text-base"
                                        />
                                        {isSearching && (
                                            <div className="absolute right-3 top-3">
                                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[#4b92ff]"></div>
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex flex-wrap gap-2 mt-3">
                                        {["LinkedIn", "Indeed", "Glassdoor", "Monster", "Dice"].map(platform => (
                                            <span key={platform} className="px-3 py-1 bg-[#f7f4ed] text-[#7a7a7a] rounded-full text-xs">
                                                {platform}
                                            </span>
                                        ))}
                                        <span className="px-3 py-1 bg-[#e3f2fd] text-[#4b92ff] rounded-full text-xs">
                                            +15 more
                                        </span>
                                    </div>
                                </div>

                                {/* Search Results */}
                                {jobSearchResults.length > 0 ? (
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm text-[#7a7a7a]">
                                                Found {jobSearchResults.length} jobs
                                            </p>
                                        </div>

                                        {jobSearchResults.map((job) => (
                                            <div key={job.id} className="p-4 border border-[#edebe5] rounded-lg hover:shadow-sm transition-shadow">
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <h3 className="font-medium text-[#151515]">{job.title}</h3>
                                                            <span className="px-2 py-1 bg-[#f7f4ed] text-[#7a7a7a] rounded text-xs">
                                                                {job.platform}
                                                            </span>
                                                        </div>
                                                        <p className="text-[#151515] font-medium mb-1">{job.company}</p>
                                                        <div className="flex items-center gap-4 text-sm text-[#7a7a7a] mb-2">
                                                            <span>📍 {job.location}</span>
                                                            {job.salary && <span>💰 {job.salary}</span>}
                                                            <span>🕒 {job.postedDate}</span>
                                                        </div>
                                                        <p className="text-sm text-[#7a7a7a] mb-3 line-clamp-2">
                                                            {job.description}
                                                        </p>
                                                        <div className="flex flex-wrap gap-2">
                                                            {job.tags.slice(0, 4).map(tag => (
                                                                <span key={tag} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">
                                                                    {tag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                    <div className="flex flex-col gap-2 ml-4">
                                                        <button
                                                            type="button"
                                                            onClick={() => handleCreateFromJob(job)}
                                                            className="px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] text-sm font-medium"
                                                        >
                                                            Apply
                                                        </button>
                                                        <button
                                                            type="button"
                                                            className="px-4 py-2 bg-white border border-[#edebe5] text-[#7a7a7a] rounded-lg hover:bg-[#f7f4ed] text-sm"
                                                        >
                                                            Save
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : jobSearchTerm && !isSearching ? (
                                    <div className="text-center py-16">
                                        <div className="w-16 h-16 mx-auto mb-6 text-[#7a7a7a]">
                                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                            </svg>
                                        </div>
                                        <h3 className="penpot-heading-medium mb-4 text-[#151515]">No Jobs Found</h3>
                                        <p className="penpot-body-large text-[#7a7a7a] mb-6">
                                            Try adjusting your search terms or filters to find more opportunities.
                                        </p>
                                        <button
                                            type="button"
                                            onClick={() => setJobSearchTerm("")}
                                            className="penpot-button-secondary"
                                        >
                                            Clear Search
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-center py-16">
                                        <div className="w-16 h-16 mx-auto mb-6 text-[#7a7a7a]">
                                            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                            </svg>
                                        </div>
                                        <h3 className="penpot-heading-medium mb-4 text-[#151515]">Discover Your Next Opportunity</h3>
                                        <p className="penpot-body-large text-[#7a7a7a] mb-6">
                                            Search across LinkedIn, Indeed, Glassdoor, and 18+ other platforms simultaneously.
                                        </p>
                                        <div className="max-w-md mx-auto">
                                            <SearchBar
                                                placeholder="Try 'Senior Software Engineer' or 'React Developer'"
                                                value={jobSearchTerm}
                                                onChange={(value) => {
                                                    setJobSearchTerm(value)
                                                    handleJobSearch(value)
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Right Panel - AI Assistant & Quick Actions */}
                    <div className="col-span-3 space-y-6">
                        {/* AI Assistant */}
                        <div className="bg-white rounded-lg border border-[#edebe5] p-4">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="w-8 h-8 bg-[#4b92ff] rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold text-sm">AI</span>
                                </div>
                                <div>
                                    <h3 className="font-medium text-[#151515]">AI Assistant</h3>
                                    <p className="text-xs text-[#7a7a7a]">Here to help</p>
                                </div>
                            </div>

                            <div className="space-y-3">
                                {activeTab === "applications" ? (
                                    <>
                                        <p className="text-sm text-[#7a7a7a]">
                                            I see you have {cases.length} active job applications.
                                            {cases.length > 0 && " Would you like help optimizing your approach for any of them?"}
                                        </p>
                                        <div className="space-y-2">
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                💼 Review application progress
                                            </button>
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                📝 Generate cover letter template
                                            </button>
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                🎯 Practice interview questions
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <p className="text-sm text-[#7a7a7a]">
                                            Searching for new opportunities? I can help refine your search and improve your applications.
                                        </p>
                                        <div className="space-y-2">
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                🎯 Improve job search strategy
                                            </button>
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                📊 Analyze market trends
                                            </button>
                                            <button type="button" className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm">
                                                💰 Negotiate better offers
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Quick Actions */}
                        <div className="bg-white rounded-lg border border-[#edebe5] p-4">
                            <h3 className="font-medium text-[#151515] mb-4">Quick Actions</h3>
                            <div className="space-y-2">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(true)}
                                    className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm flex items-center gap-2"
                                >
                                    ➕ New Application
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setActiveTab("discovery")}
                                    className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm flex items-center gap-2"
                                >
                                    🔍 Discover Jobs
                                </button>
                                <Link
                                    to="/learn"
                                    className="w-full text-left p-3 bg-[#f7f4ed] rounded-lg hover:bg-[#edebe5] transition-colors text-sm flex items-center gap-2 block"
                                >
                                    📚 Learn Best Practices
                                </Link>
                            </div>
                        </div>

                        {/* Progress Summary */}
                        {hasCases && (
                            <div className="bg-white rounded-lg border border-[#edebe5] p-4">
                                <h3 className="font-medium text-[#151515] mb-4">Application Progress</h3>
                                <div className="space-y-3">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#7a7a7a]">Active Applications</span>
                                        <span className="font-medium">{cases.filter(c => c.status === 'active').length}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#7a7a7a]">Interviewing</span>
                                        <span className="font-medium">{cases.filter(c => c.status === 'interviewing').length}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-[#7a7a7a]">Success Rate</span>
                                        <span className="font-medium text-green-600">
                                            {cases.length > 0 ? Math.round((cases.filter(c => c.status === 'offer' || c.status === 'accepted').length / cases.length) * 100) : 0}%
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Create Job Modal */}
            <CreateJobModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onCaseCreated={handleJobCreated}
                accessToken={accessToken}
            />
        </div>
    )
}
