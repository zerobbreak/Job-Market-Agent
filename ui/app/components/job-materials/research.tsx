import {
    MagnifyingGlassIcon,
    BuildingOfficeIcon,
    BriefcaseIcon,
    CurrencyDollarIcon,
    CpuChipIcon,
    GlobeAltIcon,
    NewspaperIcon,
    ChartBarIcon,
    BookmarkIcon,
    StarIcon,
    ArrowTopRightOnSquareIcon,
    EyeIcon,
    DocumentTextIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState } from "react"

interface ResearchItem {
    id: string
    type: 'company' | 'role' | 'industry' | 'salary'
    title: string
    company?: string
    content: string
    source?: string
    url?: string
    tags: string[]
    savedAt: Date
    isBookmarked: boolean
}

interface CompanyProfile {
    name: string
    industry: string
    size: string
    founded: string
    mission: string
    culture: string[]
    recentNews: string[]
    competitors: string[]
    salaryRange?: {
        min: number
        max: number
        currency: string
    }
}

function Research(_props: any) {
    const [searchQuery, setSearchQuery] = useState('')
    const [selectedCategory, setSelectedCategory] = useState<string>('all')
    const [selectedResearch, setSelectedResearch] = useState<ResearchItem | null>(null)
    const [isResearching, setIsResearching] = useState(false)
    const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null)

    const [savedResearch] = useState<ResearchItem[]>([
        {
            id: '1',
            type: 'company',
            title: 'TechCorp Company Overview',
            company: 'TechCorp',
            content: 'TechCorp is a leading technology company specializing in AI-driven solutions. Founded in 2015, they have grown to 500+ employees and focus on innovative software development.',
            source: 'Company Website',
            tags: ['techcorp', 'company-overview', 'ai'],
            savedAt: new Date('2024-01-15'),
            isBookmarked: true
        },
        {
            id: '2',
            type: 'salary',
            title: 'Frontend Developer Salary Ranges',
            content: 'Entry-level: $70k-$90k, Mid-level: $90k-$130k, Senior: $130k-$180k. Based on SF Bay Area market rates.',
            source: 'Glassdoor',
            tags: ['salary', 'frontend', 'bay-area'],
            savedAt: new Date('2024-01-10'),
            isBookmarked: false
        }
    ])

    const researchCategories = [
        { value: 'all', label: 'All Research', icon: DocumentTextIcon },
        { value: 'company', label: 'Companies', icon: BuildingOfficeIcon },
        { value: 'role', label: 'Roles', icon: BriefcaseIcon },
        { value: 'salary', label: 'Salaries', icon: CurrencyDollarIcon },
        { value: 'industry', label: 'Industry', icon: ChartBarIcon }
    ]

    const filteredResearch = savedResearch.filter(item => {
        const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             item.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             item.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))

        const matchesCategory = selectedCategory === 'all' || item.type === selectedCategory

        return matchesSearch && matchesCategory
    })

    const handleResearch = useCallback(async () => {
        if (!searchQuery.trim()) return

        setIsResearching(true)
        // Simulate research API call
        setTimeout(() => {
            const mockProfile: CompanyProfile = {
                name: 'TechCorp',
                industry: 'Technology',
                size: '500-1000 employees',
                founded: '2015',
                mission: 'To democratize AI technology and make it accessible to businesses of all sizes.',
                culture: ['Innovation', 'Collaboration', 'Work-Life Balance', 'Continuous Learning'],
                recentNews: [
                    'Launched new AI platform for small businesses',
                    'Raised $50M in Series C funding',
                    'Opened new office in Austin, TX'
                ],
                competitors: ['DataTech', 'AISolutions', 'SmartAI'],
                salaryRange: {
                    min: 80000,
                    max: 180000,
                    currency: 'USD'
                }
            }
            setCompanyProfile(mockProfile)
            setIsResearching(false)
        }, 2500)
    }, [searchQuery])

    const getCategoryIcon = (type: ResearchItem['type']) => {
        switch (type) {
            case 'company': return BuildingOfficeIcon
            case 'role': return BriefcaseIcon
            case 'salary': return CurrencyDollarIcon
            case 'industry': return ChartBarIcon
            default: return DocumentTextIcon
        }
    }

    const getCategoryColor = (type: ResearchItem['type']) => {
        switch (type) {
            case 'company': return 'text-blue-600 bg-blue-100'
            case 'role': return 'text-green-600 bg-green-100'
            case 'salary': return 'text-yellow-600 bg-yellow-100'
            case 'industry': return 'text-purple-600 bg-purple-100'
            default: return 'text-gray-600 bg-gray-100'
        }
    }

    const toggleBookmark = useCallback((itemId: string) => {
        // In a real app, this would update the database
        console.log('Toggling bookmark for:', itemId)
    }, [])

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">Research Hub</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        Comprehensive research tools for companies, roles, and market intelligence
                    </p>
                </div>
            </div>

            {/* Research Input */}
            <div className="penpot-card p-6">
                <div className="flex gap-4">
                    <div className="flex-1 relative">
                        <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-3 text-[#7a7a7a]" />
                        <input
                            type="text"
                            placeholder="Research companies, roles, or topics..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 penpot-input"
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handleResearch()
                                }
                            }}
                        />
                    </div>
                    <button
                        onClick={handleResearch}
                        disabled={!searchQuery.trim() || isResearching}
                        className="flex items-center gap-2 px-6 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] disabled:opacity-50"
                    >
                        <CpuChipIcon className={`w-4 h-4 ${isResearching ? "animate-spin" : ""}`} />
                        {isResearching ? "Researching..." : "Research"}
                    </button>
                </div>

                <div className="flex gap-2 mt-4">
                    {researchCategories.map(category => {
                        const Icon = category.icon
                        return (
                            <button
                                key={category.value}
                                onClick={() => setSelectedCategory(category.value)}
                                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    selectedCategory === category.value
                                        ? 'bg-[#4b92ff] text-white'
                                        : 'bg-white border border-[#edebe5] text-[#7a7a7a] hover:bg-gray-50'
                                }`}
                            >
                                <Icon className="w-4 h-4" />
                                {category.label}
                            </button>
                        )
                    })}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Research Results */}
                <div className="lg:col-span-1">
                    <div className="penpot-card p-6">
                        <h4 className="text-lg font-semibold mb-4">Saved Research ({filteredResearch.length})</h4>
                        <div className="space-y-3 max-h-96 overflow-y-auto">
                            {filteredResearch.map(item => {
                                const CategoryIcon = getCategoryIcon(item.type)
                                return (
                                    <div
                                        key={item.id}
                                        onClick={() => setSelectedResearch(item)}
                                        className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                                            selectedResearch?.id === item.id
                                                ? 'border-[#4b92ff] bg-blue-50'
                                                : 'border-[#edebe5] hover:border-[#4b92ff] hover:bg-gray-50'
                                        }`}
                                    >
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className={`p-1.5 rounded ${getCategoryColor(item.type)}`}>
                                                    <CategoryIcon className="w-3 h-3" />
                                                </div>
                                                <h5 className="font-medium text-sm line-clamp-2">{item.title}</h5>
                                            </div>
                                            <button
                                                onClick={() => toggleBookmark(item.id)}
                                                className={`p-1 rounded hover:bg-gray-100 ${
                                                    item.isBookmarked ? 'text-yellow-500' : 'text-gray-400'
                                                }`}
                                            >
                                                <BookmarkIcon className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <p className="text-xs text-[#7a7a7a] mb-2">
                                            {item.company && `${item.company} • `}
                                            {item.savedAt.toLocaleDateString()}
                                        </p>
                                        <p className="text-xs text-[#7a7a7a] line-clamp-2">{item.content}</p>
                                        {item.tags.length > 0 && (
                                            <div className="flex gap-1 mt-2">
                                                {item.tags.slice(0, 2).map(tag => (
                                                    <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                                                        {tag}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )
                            })}
                            {filteredResearch.length === 0 && (
                                <div className="text-center py-8 text-[#7a7a7a]">
                                    <DocumentTextIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No research found</p>
                                    <p className="text-sm">Try searching for companies or roles</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Research Details */}
                <div className="lg:col-span-2">
                    {companyProfile ? (
                        <div className="space-y-6">
                            {/* Company Profile */}
                            <div className="penpot-card p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                            <BuildingOfficeIcon className="w-6 h-6 text-blue-600" />
                                        </div>
                                        <div>
                                            <h4 className="text-xl font-semibold">{companyProfile.name}</h4>
                                            <p className="text-[#7a7a7a]">{companyProfile.industry} • {companyProfile.size}</p>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button className="p-2 hover:bg-gray-100 rounded">
                                            <BookmarkIcon className="w-5 h-5" />
                                        </button>
                                        <button className="p-2 hover:bg-gray-100 rounded">
                                            <ArrowTopRightOnSquareIcon className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div>
                                        <span className="text-sm font-medium text-[#7a7a7a]">Founded</span>
                                        <p className="font-semibold">{companyProfile.founded}</p>
                                    </div>
                                    <div>
                                        <span className="text-sm font-medium text-[#7a7a7a]">Salary Range</span>
                                        <p className="font-semibold">
                                            {companyProfile.salaryRange ?
                                                `$${companyProfile.salaryRange.min.toLocaleString()} - $${companyProfile.salaryRange.max.toLocaleString()}` :
                                                'Not available'
                                            }
                                        </p>
                                    </div>
                                </div>

                                <div className="mb-6">
                                    <h5 className="font-semibold mb-2">Mission</h5>
                                    <p className="text-[#7a7a7a]">{companyProfile.mission}</p>
                                </div>

                                <div className="mb-6">
                                    <h5 className="font-semibold mb-2">Culture & Values</h5>
                                    <div className="flex flex-wrap gap-2">
                                        {companyProfile.culture.map(value => (
                                            <span key={value} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                                                {value}
                                            </span>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <h5 className="font-semibold mb-2">Competitors</h5>
                                    <div className="flex flex-wrap gap-2">
                                        {companyProfile.competitors.map(competitor => (
                                            <span key={competitor} className="px-3 py-1 bg-orange-100 text-orange-800 rounded text-sm">
                                                {competitor}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Recent News */}
                            <div className="penpot-card p-6">
                                <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <NewspaperIcon className="w-5 h-5" />
                                    Recent News & Updates
                                </h4>
                                <div className="space-y-3">
                                    {companyProfile.recentNews.map((news, index) => (
                                        <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                            <p className="text-sm text-[#7a7a7a]">{news}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Job Opportunities */}
                            <div className="penpot-card p-6">
                                <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <BriefcaseIcon className="w-5 h-5" />
                                    Current Openings
                                </h4>
                                <div className="space-y-3">
                                    {[
                                        { title: 'Senior Frontend Developer', location: 'Remote', type: 'Full-time' },
                                        { title: 'Product Manager', location: 'San Francisco', type: 'Full-time' },
                                        { title: 'DevOps Engineer', location: 'Austin', type: 'Full-time' }
                                    ].map((job, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 border border-[#edebe5] rounded-lg">
                                            <div>
                                                <h5 className="font-medium">{job.title}</h5>
                                                <p className="text-sm text-[#7a7a7a]">{job.location} • {job.type}</p>
                                            </div>
                                            <button className="px-3 py-1 bg-[#4b92ff] text-white rounded hover:bg-[#3a7be0] text-sm">
                                                View Details
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : selectedResearch ? (
                        <div className="penpot-card p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    {(() => {
                                        const CategoryIcon = getCategoryIcon(selectedResearch.type)
                                        return (
                                            <div className={`p-2 rounded-lg ${getCategoryColor(selectedResearch.type)}`}>
                                                <CategoryIcon className="w-5 h-5" />
                                            </div>
                                        )
                                    })()}
                                    <div>
                                        <h4 className="text-lg font-semibold">{selectedResearch.title}</h4>
                                        <p className="text-sm text-[#7a7a7a]">
                                            {selectedResearch.source} • {selectedResearch.savedAt.toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button className="p-2 hover:bg-gray-100 rounded">
                                        <EyeIcon className="w-5 h-5" />
                                    </button>
                                    <button className="p-2 hover:bg-gray-100 rounded">
                                        <BookmarkIcon className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>

                            <div className="bg-gray-50 border border-[#edebe5] rounded-lg p-4 mb-4">
                                <p className="whitespace-pre-wrap">{selectedResearch.content}</p>
                            </div>

                            {selectedResearch.tags.length > 0 && (
                                <div className="flex gap-2 mb-4">
                                    {selectedResearch.tags.map(tag => (
                                        <span key={tag} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            )}

                            {selectedResearch.url && (
                                <a
                                    href={selectedResearch.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0]"
                                >
                                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                                    View Source
                                </a>
                            )}
                        </div>
                    ) : (
                        <div className="penpot-card p-6 flex items-center justify-center h-64">
                            <div className="text-center text-[#7a7a7a]">
                                <GlobeAltIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                                <h4 className="text-lg font-semibold mb-2">Research Companies & Roles</h4>
                                <p>Enter a company name or job title to start researching</p>
                                <div className="mt-4 text-sm">
                                    <p className="font-medium mb-2">Quick Research Ideas:</p>
                                    <div className="flex flex-wrap gap-2 justify-center">
                                        <button className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm">
                                            TechCorp
                                        </button>
                                        <button className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm">
                                            Frontend Developer Salary
                                        </button>
                                        <button className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm">
                                            AI Industry Trends
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Research Insights */}
            <div className="penpot-card p-6 bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
                <div className="flex items-center gap-3">
                    <ChartBarIcon className="w-6 h-6 text-purple-600" />
                    <div>
                        <h4 className="font-semibold text-purple-900">AI Research Assistant</h4>
                        <p className="text-sm text-purple-700">
                            Get AI-powered insights on company culture, market positioning, and industry trends.
                        </p>
                    </div>
                    <button className="ml-auto px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                        Generate Insights
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Research
