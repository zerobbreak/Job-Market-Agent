import {
    ArrowPathIcon,
    DocumentTextIcon,
    CloudArrowUpIcon,
    CpuChipIcon,
    CheckCircleIcon,
    XCircleIcon,
    ExclamationTriangleIcon,
    EyeIcon,
    ArrowDownTrayIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useEffect, useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface ATSOptimizerProps {
    // This component will be used for ATS optimization functionality
}

function ATSOptimizer(_props: ATSOptimizerProps) {
    const [cvFile, setCvFile] = useState<File | null>(null)
    const [jobDescription, setJobDescription] = useState("")
    const [atsSystem, setAtsSystem] = useState("general")
    const [optimizationLevel, setOptimizationLevel] = useState(2) // 1-3 scale
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [atsScore, setAtsScore] = useState(0)
    const [analysisResults, setAnalysisResults] = useState<any>(null)

    // Simulate ATS analysis
    const handleAnalyze = useCallback(async () => {
        setIsAnalyzing(true)
        // Simulate API call
        setTimeout(() => {
            const mockResults = {
                score: Math.floor(Math.random() * 40) + 60, // 60-100 range
                keywords: {
                    matched: ["JavaScript", "React", "TypeScript", "Node.js"],
                    missing: ["Python", "AWS", "Docker", "Kubernetes"],
                    suggested: ["REST APIs", "Git", "Agile"]
                },
                compliance: [
                    { item: "File format", status: "pass", message: "PDF format detected" },
                    { item: "Contact info", status: "pass", message: "Email and phone found" },
                    { item: "Keyword density", status: "warning", message: "Consider adding more technical terms" },
                    { item: "File size", status: "pass", message: "Under 5MB limit" },
                    { item: "Readable text", status: "pass", message: "Text layers detected" }
                ]
            }
            setAtsScore(mockResults.score)
            setAnalysisResults(mockResults)
            setIsAnalyzing(false)
        }, 2000)
    }, [])

    const getScoreColor = (score: number) => {
        if (score >= 80) return "text-green-600"
        if (score >= 60) return "text-yellow-600"
        return "text-red-600"
    }

    const getScoreGrade = (score: number) => {
        if (score >= 90) return "A"
        if (score >= 80) return "B"
        if (score >= 70) return "C"
        if (score >= 60) return "D"
        return "F"
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">ATS Optimizer - CV Optimization</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        AI-powered CV optimization for Applicant Tracking Systems
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleAnalyze}
                        disabled={isAnalyzing || !cvFile}
                        className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <CpuChipIcon className={`w-4 h-4 ${isAnalyzing ? "animate-spin" : ""}`} />
                        {isAnalyzing ? "Analyzing..." : "Analyze CV"}
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
                                    id="cv-upload"
                                />
                                <label
                                    htmlFor="cv-upload"
                                    className="inline-block px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] cursor-pointer"
                        >
                                    Choose File
                                </label>
                            </div>
                    )}
                </div>
            </div>

                {/* Job Description */}
            <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4">Job Description</h4>
                    <div className="space-y-4">
                            <textarea
                            value={jobDescription}
                            onChange={(e) => setJobDescription(e.target.value)}
                            placeholder="Paste job description here, or provide a URL..."
                            className="w-full h-32 penpot-input resize-none"
                            />
                        <div className="flex gap-2">
                            <input
                                type="url"
                                placeholder="Or enter job posting URL"
                                className="flex-1 penpot-input"
                            />
                            <button className="px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                                Scrape
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* ATS Configuration */}
            <div className="penpot-card p-6">
                <h4 className="text-lg font-semibold mb-4">ATS Configuration</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block font-medium mb-2">ATS System</label>
                        <select
                            value={atsSystem}
                            onChange={(e) => setAtsSystem(e.target.value)}
                            className="w-full penpot-input"
                        >
                            <option value="general">General ATS</option>
                            <option value="greenhouse">Greenhouse</option>
                            <option value="workday">Workday</option>
                            <option value="taleo">Taleo</option>
                            <option value="icims">iCIMS</option>
                        </select>
                    </div>
                    <div>
                        <label className="block font-medium mb-2">
                            Optimization Level: {optimizationLevel === 1 ? "Conservative" : optimizationLevel === 2 ? "Moderate" : "Aggressive"}
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="3"
                            value={optimizationLevel}
                            onChange={(e) => setOptimizationLevel(Number(e.target.value))}
                            className="w-full"
                        />
                        <div className="flex justify-between text-xs text-[#7a7a7a] mt-1">
                            <span>Conservative</span>
                            <span>Moderate</span>
                            <span>Aggressive</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Results Section */}
            {analysisResults && (
                <div className="space-y-6">
                    {/* ATS Score */}
                    <div className="penpot-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold">ATS Compatibility Score</h4>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <div className={`text-3xl font-bold ${getScoreColor(atsScore)}`}>
                                        {atsScore}/100
                                    </div>
                                    <div className="text-sm text-[#7a7a7a]">
                                        Grade: {getScoreGrade(atsScore)}
                                    </div>
                                </div>
                                <div className="relative w-16 h-16">
                                    <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                                        <path
                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke="#eee"
                                            strokeWidth="2"
                                        />
                                        <path
                                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                            fill="none"
                                            stroke={atsScore >= 80 ? "#10b981" : atsScore >= 60 ? "#f59e0b" : "#ef4444"}
                                            strokeWidth="2"
                                            strokeDasharray={`${atsScore}, 100`}
                                        />
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Keyword Analysis */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="penpot-card p-6">
                            <h5 className="font-semibold mb-3 flex items-center gap-2 text-green-600">
                                <CheckCircleIcon className="w-4 h-4" />
                                Matched Keywords ({analysisResults.keywords.matched.length})
                            </h5>
                            <div className="space-y-1">
                                {analysisResults.keywords.matched.map((keyword: string, index: number) => (
                                    <span key={index} className="inline-block bg-green-100 text-green-800 px-2 py-1 rounded text-sm mr-1 mb-1">
                                        {keyword}
                            </span>
                                ))}
                            </div>
                        </div>

                        <div className="penpot-card p-6">
                            <h5 className="font-semibold mb-3 flex items-center gap-2 text-red-600">
                                <XCircleIcon className="w-4 h-4" />
                                Missing Keywords ({analysisResults.keywords.missing.length})
                            </h5>
                            <div className="space-y-1">
                                {analysisResults.keywords.missing.map((keyword: string, index: number) => (
                                    <span key={index} className="inline-block bg-red-100 text-red-800 px-2 py-1 rounded text-sm mr-1 mb-1">
                                        {keyword}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="penpot-card p-6">
                            <h5 className="font-semibold mb-3 flex items-center gap-2 text-blue-600">
                                <ExclamationTriangleIcon className="w-4 h-4" />
                                Suggested Additions ({analysisResults.keywords.suggested.length})
                            </h5>
                            <div className="space-y-1">
                                {analysisResults.keywords.suggested.map((keyword: string, index: number) => (
                                    <span key={index} className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm mr-1 mb-1">
                                        {keyword}
                                </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Compliance Checklist */}
                    <div className="penpot-card p-6">
                        <h4 className="text-lg font-semibold mb-4">Format Compliance Checklist</h4>
                        <div className="space-y-3">
                            {analysisResults.compliance.map((item: any, index: number) => (
                                <div key={index} className="flex items-center gap-3">
                                    {item.status === "pass" ? (
                                        <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                                    ) : item.status === "warning" ? (
                                        <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 flex-shrink-0" />
                                    ) : (
                                        <XCircleIcon className="w-5 h-5 text-red-600 flex-shrink-0" />
                                    )}
                                    <div>
                                        <span className="font-medium">{item.item}</span>
                                        <span className="text-sm text-[#7a7a7a] ml-2">{item.message}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0]">
                            <EyeIcon className="w-4 h-4" />
                            Preview Optimized CV
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download PDF
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#f59e0b] text-white rounded-lg hover:bg-[#d97706]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download Word
                        </button>
                    </div>
                    </div>
                )}
        </div>
    )
}

export default ATSOptimizer
