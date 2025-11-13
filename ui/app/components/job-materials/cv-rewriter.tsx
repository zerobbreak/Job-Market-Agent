import {
    ArrowPathIcon,
    DocumentTextIcon,
    CloudArrowUpIcon,
    CpuChipIcon,
    CheckCircleIcon,
    EyeIcon,
    ArrowDownTrayIcon,
    ChartBarIcon,
    PencilIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState } from "react"

interface CVRewriterProps {
    // This component will be used for CV rewriting functionality
}

function CVRewriter(_props: CVRewriterProps) {
    const [cvFile, setCvFile] = useState<File | null>(null)
    const [targetJob, setTargetJob] = useState("")
    const [tone, setTone] = useState("professional")
    const [focusAreas, setFocusAreas] = useState<string[]>(["experience", "skills"])
    const [experienceLevel, setExperienceLevel] = useState("junior")
    const [isRewriting, setIsRewriting] = useState(false)
    const [rewriteResults, setRewriteResults] = useState<any>(null)
    const [showComparison, setShowComparison] = useState(false)

    // Simulate CV rewriting
    const handleRewrite = useCallback(async () => {
        setIsRewriting(true)
        // Simulate API call
        setTimeout(() => {
            const mockResults = {
                original: `# John Doe
## Professional Summary
I am a software developer with experience in web development.

## Experience
- Software Developer at Tech Corp (2020-Present)
  - Developed web applications using JavaScript
  - Worked on team projects

## Skills
- JavaScript
- HTML
- CSS`,

                enhanced: `# John Doe
## Professional Summary
Results-driven Software Developer with 4+ years of experience building scalable web applications and leading cross-functional development teams. Proven track record of delivering high-performance solutions that drive business growth and user satisfaction.

## Experience
- **Senior Software Developer** at Tech Corp (2020-Present)
  - Architected and developed full-stack web applications serving 100K+ users, improving performance by 40%
  - Led a team of 5 developers in implementing microservices architecture, reducing deployment time by 60%
  - Collaborated with product managers and designers to deliver 15+ major features on tight deadlines

## Skills
- **Programming Languages**: JavaScript (ES6+), TypeScript, Python, SQL
- **Frontend Technologies**: React, Vue.js, HTML5, CSS3, Sass
- **Backend Technologies**: Node.js, Express.js, REST APIs, GraphQL
- **Tools & Platforms**: Git, Docker, AWS, Jenkins, Agile/Scrum methodologies`,

                metrics: {
                    wordCount: { original: 45, enhanced: 98 },
                    readability: { original: 65, enhanced: 78 },
                    keywordDensity: { original: 12, enhanced: 28 }
                },

                improvements: [
                    "Enhanced professional summary with quantifiable achievements",
                    "Restructured experience section with action verbs and metrics",
                    "Expanded skills section with categorized competencies",
                    "Improved overall readability and ATS compatibility"
                ]
            }
            setRewriteResults(mockResults)
            setIsRewriting(false)
        }, 3000)
    }, [])

    const toggleFocusArea = (area: string) => {
        setFocusAreas(prev =>
            prev.includes(area)
                ? prev.filter(a => a !== area)
                : [...prev, area]
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">CV Rewriter - Content Enhancement</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        AI-powered CV enhancement and content optimization
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleRewrite}
                        disabled={isRewriting || !cvFile}
                        className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <CpuChipIcon className={`w-4 h-4 ${isRewriting ? "animate-spin" : ""}`} />
                        {isRewriting ? "Enhancing..." : "Rewrite CV"}
                    </button>
                </div>
            </div>

            {/* Input Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* CV Upload */}
                <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <DocumentTextIcon className="w-5 h-5" />
                        CV File
                    </h4>
                    <div className="border-2 border-dashed border-[#edebe5] rounded-lg p-6 text-center">
                        {cvFile ? (
                            <div className="space-y-2">
                                <DocumentTextIcon className="w-8 h-8 text-[#4b92ff] mx-auto" />
                                <p className="font-medium">{cvFile.name}</p>
                                <p className="text-sm text-[#7a7a7a]">
                                    {(cvFile.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                                <button
                                    onClick={() => setCvFile(null)}
                                    className="text-sm text-red-600 hover:text-red-700"
                                >
                                    Remove
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <CloudArrowUpIcon className="w-8 h-8 text-[#7a7a7a] mx-auto" />
                                <p className="font-medium">Upload your CV</p>
                                <p className="text-sm text-[#7a7a7a]">PDF, DOC, or DOCX format</p>
                                <input
                                    type="file"
                                    accept=".pdf,.doc,.docx"
                                    onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                                    className="hidden"
                                    id="cv-rewriter-upload"
                                />
                                <label
                                    htmlFor="cv-rewriter-upload"
                                    className="inline-block px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] cursor-pointer"
                                >
                                    Choose File
                                </label>
                            </div>
                        )}
                    </div>
                </div>

                {/* Configuration */}
            <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4">Enhancement Settings</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="block font-medium mb-2">Target Job/Role</label>
                            <input
                                type="text"
                                value={targetJob}
                                onChange={(e) => setTargetJob(e.target.value)}
                                placeholder="e.g., Frontend Developer, Product Manager"
                                className="w-full penpot-input"
                            />
                        </div>

                        <div>
                            <label className="block font-medium mb-2">Tone</label>
                            <select
                                value={tone}
                                onChange={(e) => setTone(e.target.value)}
                                className="w-full penpot-input"
                            >
                                <option value="professional">Professional</option>
                                <option value="creative">Creative</option>
                                <option value="concise">Concise</option>
                            </select>
                        </div>

                        <div>
                            <label className="block font-medium mb-2">Focus Areas</label>
                            <div className="grid grid-cols-2 gap-2">
                                {["experience", "skills", "education", "projects"].map(area => (
                                    <label key={area} className="flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={focusAreas.includes(area)}
                                            onChange={() => toggleFocusArea(area)}
                                            className="rounded"
                                        />
                                        <span className="capitalize text-sm">{area}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="block font-medium mb-2">Experience Level</label>
                            <select
                                value={experienceLevel}
                                onChange={(e) => setExperienceLevel(e.target.value)}
                                className="w-full penpot-input"
                            >
                                <option value="junior">Junior (0-3 years)</option>
                                <option value="mid">Mid-level (3-5 years)</option>
                                <option value="senior">Senior (5+ years)</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            {/* Results Section */}
            {rewriteResults && (
                <div className="space-y-6">
                    {/* Metrics Overview */}
                    <div className="penpot-card p-6">
                        <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                            <ChartBarIcon className="w-5 h-5" />
                            Enhancement Metrics
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-[#4b92ff]">
                                    {rewriteResults.metrics.wordCount.enhanced}
                                </div>
                                <div className="text-sm text-[#7a7a7a]">
                                    Word Count ({rewriteResults.metrics.wordCount.original} → {rewriteResults.metrics.wordCount.enhanced})
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-[#10b981]">
                                    {rewriteResults.metrics.readability.enhanced}%
                                </div>
                                <div className="text-sm text-[#7a7a7a]">
                                    Readability Score ({rewriteResults.metrics.readability.original}% → {rewriteResults.metrics.readability.enhanced}%)
                                </div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-[#f59e0b]">
                                    {rewriteResults.metrics.keywordDensity.enhanced}%
                                </div>
                                <div className="text-sm text-[#7a7a7a]">
                                    Keyword Density ({rewriteResults.metrics.keywordDensity.original}% → {rewriteResults.metrics.keywordDensity.enhanced}%)
                                </div>
                            </div>
                        </div>
                        </div>

                    {/* Comparison View */}
                    <div className="penpot-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold">Before/After Comparison</h4>
                            <button
                                onClick={() => setShowComparison(!showComparison)}
                                className="flex items-center gap-2 px-3 py-1 bg-[#4b92ff] text-white rounded hover:bg-[#3a7be0] text-sm"
                            >
                                <EyeIcon className="w-4 h-4" />
                                {showComparison ? "Hide" : "Show"} Comparison
                            </button>
                        </div>

                        {showComparison && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div>
                                    <h5 className="font-semibold mb-3 text-red-600">Original CV</h5>
                                    <div className="bg-red-50 border border-red-200 rounded p-4 max-h-96 overflow-y-auto">
                                        <pre className="text-sm whitespace-pre-wrap font-mono">
                                            {rewriteResults.original}
                                        </pre>
                                    </div>
                                </div>
                                <div>
                                    <h5 className="font-semibold mb-3 text-green-600">Enhanced CV</h5>
                                    <div className="bg-green-50 border border-green-200 rounded p-4 max-h-96 overflow-y-auto">
                                        <pre className="text-sm whitespace-pre-wrap font-mono">
                                            {rewriteResults.enhanced}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Improvements List */}
                        <div className="mt-6">
                            <h5 className="font-semibold mb-3">Key Improvements Made</h5>
                            <div className="space-y-2">
                                {rewriteResults.improvements.map((improvement: string, index: number) => (
                                    <div key={index} className="flex items-center gap-2">
                                        <CheckCircleIcon className="w-4 h-4 text-green-600 flex-shrink-0" />
                                        <span className="text-sm">{improvement}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0]">
                            <PencilIcon className="w-4 h-4" />
                            Edit Content
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download Enhanced CV
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#f59e0b] text-white rounded-lg hover:bg-[#d97706]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Export Changes Report
                        </button>
            </div>
                </div>
            )}
        </div>
    )
}

export default CVRewriter
