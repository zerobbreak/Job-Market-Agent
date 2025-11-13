import type React from "react"
import { lazy, Suspense, useCallback, useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"
import type {
    ContentItem,
    LearningPage,
    LearningSearchResult,
    LearningSection,
} from "@/types/learn.types"
import { Button } from "~/components/ui/button"
import { ErrorBoundary } from "~/components/ui/error-boundary"
import { Input, InputGroup } from "~/components/ui/input"
import { Tabs, TabsList, TabsTrigger } from "~/components/ui/tabs"
import { useDebounce } from "~/hooks"

// Constants
const SEARCH_DEBOUNCE_MS = 300
const _REDIRECT_RESET_MS = 100
const SEARCH_BLUR_DELAY_MS = 200
const MAX_SEARCH_RESULTS = 10
const MIN_CONTENT_HEIGHT = 600
const MAX_CONTENT_WIDTH = "4xl"

// Content index for search functionality
const contentIndex: ContentItem[] = [
    {
        section: "using",
        page: "introduction",
        title: "Introduction",
        content:
            "Welcome to Job Market Agent - Learn how to use our AI-powered job application assistant effectively. This platform helps you discover opportunities across 20+ job platforms, optimize your CV for Applicant Tracking Systems (ATS), generate tailored cover letters, and prepare for interviews. It does not replace your personal career strategy and decision-making, but provides a powerful framework to accelerate your job search while maximizing your chances of success through data-driven optimization and intelligent automation.",
    },
    {
        section: "using",
        page: "mode-overview",
        title: "Feature overview",
        content:
            "Job Market Agent provides multiple AI-powered tools to optimize your job search. You can generate tailored CVs, cover letters, ATS optimization reports, and interview preparation materials within the same job application workflow. Available features include CV Rewriter, ATS Optimizer, Cover Letter Specialist, Interview Prep Agent, Research, and Notes for tracking your application progress.",
    },
    {
        section: "using",
        page: "document-drafting",
        title: "Application materials",
        content:
            "Job Market Agent enables the creation and download of professionally optimized application materials tailored to specific job opportunities. This includes Optimized CVs tailored to match job descriptions with appropriate keywords and formatting for maximum ATS compatibility, personalized Cover Letters, detailed ATS Reports analyzing how well your application matches job requirements, and customized Interview Prep Materials including questions, answers, and company research.",
    },
    {
        section: "using",
        page: "general-best-practices",
        title: "General best practices",
        content:
            "While Job Market Agent provides powerful AI-driven optimization, your success ultimately depends on how you use these tools. Personalize all AI-generated content to reflect your authentic voice and experiences. Use specific job descriptions when generating materials. Review and verify all company research before applications. Keep your CV and profile up-to-date. Test different versions to see what works best. Never submit AI-generated materials without thorough review and personalization. Do not exaggerate skills or experience. Avoid using generic templates without customization.",
    },
    {
        section: "using",
        page: "reporting-issues",
        title: "Reporting issues",
        content:
            "We encourage users to report any errors, optimization issues, or technical problems encountered while using Job Market Agent. Please report inaccurate ATS optimization scores, generated materials that don't match job requirements, irrelevant job search results, technical errors or bugs, and security or privacy concerns. Include the issue type, context of what feature you were using, steps to reproduce, expected vs actual result, and any screenshots or error messages.",
    },
    {
        section: "tips",
        page: "translation-guideline",
        title: "Global job search",
        content:
            "Job Market Agent supports job searches across international markets. While the platform interface is in English, we can process and optimize job applications for positions posted in various languages. Our AI can help translate and adapt your materials for international opportunities. Consider different CV formats for different regions, understand local job application conventions, be mindful of time zones, and clearly indicate work authorization status for international roles.",
    },
    {
        section: "security",
        page: "data-protection",
        title: "Data Protection",
        content:
            "Your privacy and data security are our top priorities. Job Market Agent implements industry-leading security measures including end-to-end encryption for all data transmitted using TLS 1.3, zero-knowledge architecture where sensitive documents are encrypted on your device before upload, secure storage with AES-256 encryption at rest, strict access controls for all data access, and regular security audits and penetration testing. You have full control over your data and can export, delete, or modify your information at any time.",
    },
    {
        section: "values",
        page: "our-values",
        title: "Our values",
        content:
            "Accuracy & Effectiveness: High standards for job matching accuracy, ATS optimization, and application success rates. Empowerment: Support, not replace, your career judgment and personal decision-making. Innovation: Continuous improvement of AI technology for job search and career advancement. User Success: Commitment to helping job seekers achieve better career outcomes and land their ideal roles. Transparency: Clear explanations of how our AI optimizes your applications and why specific recommendations are made.",
    },
    {
        section: "values",
        page: "mission",
        title: "Mission",
        content:
            "Democratizing access to AI-powered job search tools, helping job seekers of all backgrounds compete effectively in the modern job market by leveraging enterprise-grade optimization and automation without prohibitive costs. We believe everyone deserves equal access to the tools that maximize their career opportunities, regardless of their current employment status or resources.",
    },
    {
        section: "values",
        page: "technology",
        title: "Technology",
        content:
            "Job Market Agent uses advanced AI technologies including Claude Sonnet 4 for CV optimization, cover letter generation, and interview preparation. Multi-Platform Job Discovery automatically scrapes and aggregates jobs from 20+ platforms including LinkedIn, Indeed, and Glassdoor. ATS Optimization Engine analyzes job descriptions and optimizes CVs for maximum Applicant Tracking System compatibility. Advanced NLP performs semantic job matching and skills gap analysis. Continuous Learning regularly updates matching algorithms, ATS patterns, and optimization strategies.",
    },
    {
        section: "about",
        page: "mission",
        title: "About Job Market Agent",
        content: "Our mission is to democratize access to enterprise-grade job search optimization tools, empowering every job seeker to compete effectively in the modern job market. Our vision is a world where career opportunities are accessible to all, and where AI technology amplifies human potential rather than creating barriers. We built this because the traditional job search process is inefficient and Applicant Tracking Systems filter out qualified candidates. Job seekers struggle to stand out, while professional career coaches cost thousands of dollars. Job Market Agent levels the playing field.",
    },
    {
        section: "faq",
        page: "all",
        title: "FAQ",
        content:
            "Frequently asked questions about Job Market Agent. Can I use AI-generated materials without editing them? No, always personalize and verify AI-generated content. How many job platforms does Job Market Agent search? We aggregate jobs from 20+ platforms including LinkedIn, Indeed, Glassdoor, and specialized industry sites. Does this tool guarantee job offers? No, it optimizes your applications and maximizes your chances, but success depends on many factors. How does ATS optimization work? We analyze job descriptions to identify key requirements and optimize your CV with appropriate keywords, formatting, and structure. Is my data secure? Yes, we use encryption and zero-knowledge infrastructure. Can I customize the generated materials? Absolutely, all materials are fully editable. Which file formats are supported? PDF, DOCX, DOC, TXT, and common image formats.",
    },
]

const sections: Array<{
    id: string
    label: string
    icon: string
    pages: Array<{ id: string; label: string }>
}> = [
    {
        id: "using",
        label: "Using Job Market Agent",
        icon: "🚀",
        pages: [
            { id: "introduction", label: "Introduction" },
            { id: "mode-overview", label: "Feature overview" },
            { id: "document-drafting", label: "Application materials" },
            { id: "general-best-practices", label: "Best practices" },
            { id: "reporting-issues", label: "Report issues" },
        ],
    },
    {
        id: "tips",
        label: "Job Search Tips",
        icon: "💡",
        pages: [{ id: "translation-guideline", label: "Global job search" }],
    },
    {
        id: "security",
        label: "Security & Privacy",
        icon: "🔒",
        pages: [{ id: "data-protection", label: "Data protection" }],
    },
    {
        id: "values",
        label: "Values & Mission",
        icon: "🎯",
        pages: [
            { id: "our-values", label: "Our values" },
            { id: "mission", label: "Mission" },
            { id: "technology", label: "Technology" },
        ],
    },
    {
        id: "about",
        label: "About Us",
        icon: "ℹ️",
        pages: [{ id: "mission", label: "Our story" }],
    },
    {
        id: "faq",
        label: "FAQ",
        icon: "❓",
        pages: [{ id: "all", label: "Frequently asked questions" }],
    },
]

// Dynamic component loader
const getPageComponent = (section: string, page: string) => {
    const componentMap: Record<string, Record<string, React.ComponentType>> = {
        using: {
            introduction: lazy(() => import("./using.introduction")),
            "mode-overview": lazy(() => import("./using.mode-overview")),
            "document-drafting": lazy(() => import("./using.document-drafting")),
            "general-best-practices": lazy(() => import("./using.general-best-practices")),
            "reporting-issues": lazy(() => import("./using.reporting-issues")),
        },
        tips: {
            "translation-guideline": lazy(() => import("./tips.translation-guideline")),
        },
        security: {
            "data-protection": lazy(() => import("./security.data-protection")),
        },
        values: {
            "our-values": lazy(() => import("./values.our-values")),
            mission: lazy(() => import("./values.mission")),
            technology: lazy(() => import("./values.technology")),
        },
        about: {
            mission: lazy(() => import("./about.mission")),
        },
        faq: {
            all: lazy(() => import("./faq.all")),
        },
    }

    return componentMap[section]?.[page] || componentMap.using.introduction
}

export default function LearnLayout() {
    const params = useParams()
    const navigate = useNavigate()
    const [searchQuery, setSearchQuery] = useState("")
    const [searchResults, setSearchResults] = useState<LearningSearchResult[]>([])
    const [showSearchResults, setShowSearchResults] = useState(false)
    const [selectedTabValue, setSelectedTabValue] = useState("using")
    const [selectedPageValue, setSelectedPageValue] = useState("")

    // Use the custom debounce hook instead of manual useEffect
    const debouncedQuery = useDebounce(searchQuery, SEARCH_DEBOUNCE_MS)

    // Get section and page from URL parameters
    const currentSection = params.section || "using"
    const currentPage = params.page || "introduction"

    // Update selected tab and page values based on current route
    useEffect(() => {
        setSelectedTabValue(currentSection)
    }, [currentSection])

    useEffect(() => {
        setSelectedPageValue(currentPage)
    }, [currentPage])

    // Handle tab changes to navigate to sections
    const handleTabChange = (value: string) => {
        try {
            setSelectedTabValue(value)
            const section = sections.find((s) => s.id === value)
            if (section) {
                const defaultPage =
                    section.pages && section.pages.length > 0 ? section.pages[0].id : "introduction"
                navigate(`/learn/${section.id}/${defaultPage}`, { replace: true })
            } else {
                console.warn("Section not found:", value)
            }
        } catch (error) {
            console.error("Navigation error in handleTabChange:", error)
        }
    }

    // Handle page changes to navigate to pages within section
    const handlePageChange = (value: string) => {
        try {
            setSelectedPageValue(value)
            navigate(`/learn/${currentSection}/${value}`, { replace: true })
        } catch (error) {
            console.error("Navigation error in handlePageChange:", error)
        }
    }

    // Validate section and page
    const currentSectionData = sections.find((s) => s.id === currentSection)
    const isValidSection = !!currentSectionData
    const isValidPage = isValidSection && currentSectionData.pages.some((p) => p.id === currentPage)

    // Redirect invalid routes
    useEffect(() => {
        if (!isValidSection) {
            navigate("/learn/using/introduction", { replace: true })
        } else if (!isValidPage) {
            const defaultPage = currentSectionData.pages[0]?.id || "introduction"
            navigate(`/learn/${currentSection}/${defaultPage}`, { replace: true })
        }
    }, [isValidSection, isValidPage, currentSection, currentSectionData, navigate])

    // Search functionality - optimized for performance
    const performSearch = useCallback((query: string) => {
        try {
            if (query.trim().length === 0) {
                setSearchResults([])
                setShowSearchResults(false)
                return
            }

            const searchTerm = query.toLowerCase().trim()
            const results: LearningSearchResult[] = []

            // Single pass through content with optimized string operations
            for (const item of contentIndex) {
                try {
                    const titleLower = item.title.toLowerCase()
                    const contentLower = item.content.toLowerCase()

                    const titleIndex = titleLower.indexOf(searchTerm)
                    const contentIndexPos = contentLower.indexOf(searchTerm)

                    const titleMatch = titleIndex !== -1
                    const contentMatch = contentIndexPos !== -1

                    // Skip if no matches
                    if (!titleMatch && !contentMatch) continue

                    // Calculate relevance score with fewer operations
                    let relevanceScore = 0
                    if (titleMatch) relevanceScore += 10
                    if (contentMatch) relevanceScore += 5
                    if (titleIndex === 0) relevanceScore += 5 // Starts with search term
                    if (contentIndexPos === 0) relevanceScore += 2 // Content starts with search term

                    // Create minimal LearningPage and LearningSection objects from ContentItem
                    const mockPage: LearningPage = {
                        id: `${item.section}.${item.page}`,
                        title: item.title,
                        content: item.content,
                        section: item.section,
                        order: 0, // Not available in ContentItem
                        lastModified: new Date().toISOString(), // Default to now
                        tags: [], // Not available in ContentItem
                        difficulty: "beginner" as const, // Default
                        estimatedReadTime: Math.ceil(item.content.length / 200), // Rough estimate
                    }

                    const mockSection: LearningSection = {
                        id: item.section,
                        title: sections.find((s) => s.id === item.section)?.label || item.section,
                        description: "", // Not available
                        icon: sections.find((s) => s.id === item.section)?.icon,
                        pages: [], // Not available in this context
                        order: 0, // Not available
                    }

                    results.push({
                        page: mockPage,
                        section: mockSection,
                        relevanceScore,
                        matchedTerms: [searchTerm],
                    })

                    // Early exit if we have enough results (optimization for large datasets)
                    if (results.length >= MAX_SEARCH_RESULTS) break
                } catch (itemError) {
                    console.warn("Error processing search item:", item, itemError)
                    // Continue with other items
                }
            }

            // Sort by relevance (only the results we found)
            results.sort((a, b) => b.relevanceScore - a.relevanceScore)

            setSearchResults(results.slice(0, MAX_SEARCH_RESULTS)) // Ensure max results
            setShowSearchResults(true)
        } catch (error) {
            console.error("Search error:", error)
            setSearchResults([])
            setShowSearchResults(false)
            // Could show error message to user here
        }
    }, [])

    // Use debounced query directly for search
    useEffect(() => {
        performSearch(debouncedQuery)
    }, [debouncedQuery, performSearch])

    const handleSearchFocus = () => {
        if (debouncedQuery.trim().length > 0) {
            setShowSearchResults(true)
        }
    }

    const handleSearchBlur = () => {
        // Delay hiding to allow click on results
        setTimeout(() => setShowSearchResults(false), SEARCH_BLUR_DELAY_MS)
    }

    return (
        <div className="min-h-screen bg-[#fcfbf8]">
            {/* Header */}
            <header className="bg-white border-b border-[#edebe5] px-8 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <Tabs
                            value={selectedTabValue}
                            onValueChange={handleTabChange}
                            className="hidden md:block"
                        >
                            <TabsList>
                                {sections.map((section) => (
                                    <TabsTrigger key={section.id} value={section.id}>
                                        {section.label}
                                    </TabsTrigger>
                                ))}
                            </TabsList>
                        </Tabs>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block">
                            <InputGroup className="w-64">
                                <Input
                                    type="text"
                                    placeholder="Search documentation..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onFocus={handleSearchFocus}
                                    onBlur={handleSearchBlur}
                                />
                                <svg
                                    data-slot="icon"
                                    className="w-4 h-4"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    role="img"
                                    aria-label="Search"
                                >
                                    <title>Search</title>
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                    />
                                </svg>
                            </InputGroup>

                            {/* Search Results Dropdown */}
                            {showSearchResults && searchResults.length > 0 && (
                                <div className="absolute top-full mt-1 w-full bg-white border border-[#edebe5] rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
                                    {searchResults.map((result, index) => (
                                        <Button
                                            key={`${result.page.section}-${result.page.id}-${index}`}
                                            type="button"
                                            onClick={(event: React.MouseEvent) => {
                                                event.preventDefault()
                                                navigate(
                                                    `/learn/${result.page.section}/${result.page.id.split(".").pop()}`
                                                )
                                                setShowSearchResults(false)
                                                setSearchQuery("")
                                            }}
                                            plain
                                            className="w-full justify-start px-4 py-3 h-auto hover:bg-[#f9fafb] border-b border-[#f9fafb] last:border-b-0"
                                        >
                                            <div className="font-medium text-[#151515] text-sm">
                                                {result.page.title}
                                            </div>
                                            <div
                                                className="text-xs text-[#7a7a7a] mt-1 overflow-hidden"
                                                style={{
                                                    display: "-webkit-box",
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: "vertical",
                                                    lineHeight: "1.4em",
                                                    maxHeight: "2.8em",
                                                }}
                                            >
                                                {result.page.content.substring(0, 100)}...
                                            </div>
                                            <div className="text-xs text-[#4b92ff] mt-1 capitalize">
                                                {result.section.title}
                                            </div>
                                        </Button>
                                    ))}
                                </div>
                            )}

                            {/* No Results */}
                            {showSearchResults &&
                                searchQuery.trim().length > 0 &&
                                searchResults.length === 0 && (
                                    <div className="absolute top-full mt-1 w-full bg-white border border-[#edebe5] rounded-lg shadow-lg z-50 p-4">
                                        <div className="text-sm text-[#7a7a7a] text-center">
                                            No results found for "{searchQuery}"
                                        </div>
                                    </div>
                                )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-8 py-8">
                <div className="flex gap-8">
                    {/* Sidebar */}
                    <aside className="w-64 flex-shrink-0">
                        {currentSectionData && (
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-lg font-semibold text-[#151515] mb-4 flex items-center gap-2">
                                        <span>{currentSectionData.icon}</span>
                                        {currentSectionData.label}
                                    </h2>
                                    <nav className="space-y-2" aria-label="Page navigation">
                                        {currentSectionData.pages.map((page) => (
                                            <Button
                                                key={page.id}
                                                type="button"
                                                onClick={(event: React.MouseEvent) => {
                                                    event.preventDefault()
                                                    handlePageChange(page.id)
                                                }}
                                                plain
                                                className={`w-full justify-start px-3 py-2 text-sm font-medium h-auto transition-colors ${
                                                    selectedPageValue === page.id
                                                        ? "bg-[#dbeafe] text-[#1d4ed8] hover:bg-[#dbeafe]"
                                                        : "text-[#7a7a7a] hover:bg-[#f3f4f6] hover:text-[#151515]"
                                                }`}
                                            >
                                                {page.label}
                                            </Button>
                                        ))}
                                    </nav>
                                </div>
                            </div>
                        )}
                    </aside>

                    {/* Content Area */}
                    <main
                        className={`flex-1 min-h-[${MIN_CONTENT_HEIGHT}px] max-w-${MAX_CONTENT_WIDTH}`}
                    >
                        <ErrorBoundary>
                            <Suspense
                                fallback={
                                    <div className="flex items-center justify-center p-12">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4b92ff]" />
                                    </div>
                                }
                            >
                                {(() => {
                                    const PageComponent = getPageComponent(
                                        currentSection,
                                        currentPage
                                    )
                                    return (
                                        <PageComponent key={`${currentSection}-${currentPage}`} />
                                    )
                                })()}
                            </Suspense>
                        </ErrorBoundary>
                    </main>
                </div>
            </div>
        </div>
    )
}
