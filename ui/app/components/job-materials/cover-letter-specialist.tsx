import {
    ArrowPathIcon,
    DocumentTextIcon,
    CloudArrowUpIcon,
    CpuChipIcon,
    EyeIcon,
    ArrowDownTrayIcon,
    BuildingOfficeIcon,
    UserIcon,
    PencilIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState } from "react"

interface CoverLetterSpecialistProps {
    // This component will be used for cover letter generation functionality
}

function CoverLetterSpecialist(_props: CoverLetterSpecialistProps) {
    const [cvFile, setCvFile] = useState<File | null>(null)
    const [jobDescription, setJobDescription] = useState("")
    const [companyName, setCompanyName] = useState("")
    const [contactPerson, setContactPerson] = useState("")
    const [tone, setTone] = useState("formal")
    const [keyPoints, setKeyPoints] = useState("")
    const [length, setLength] = useState("medium")
    const [isGenerating, setIsGenerating] = useState(false)
    const [generatedLetter, setGeneratedLetter] = useState("")
    const [showPreview, setShowPreview] = useState(false)

    // Simulate cover letter generation
    const handleGenerate = useCallback(async () => {
        setIsGenerating(true)
        // Simulate API call
        setTimeout(() => {
            const mockLetter = `[Your Name]
[Your Address]
[City, State, ZIP Code]
[Email Address]
[Phone Number]
[Date]

${contactPerson || "Hiring Manager"}
${companyName || "[Company Name]"}
[Company Address]
[City, State, ZIP Code]

Dear ${contactPerson || "Hiring Manager"},

I am writing to express my strong interest in the [Job Title] position at ${companyName || "[Company Name]"}, as advertised. With my background in software development and passion for creating innovative solutions, I am excited about the opportunity to contribute to your team's success.

In my current role as a Full-Stack Developer, I have successfully led the development of scalable web applications serving over 10,000 users. My expertise in React, Node.js, and cloud technologies has enabled me to deliver high-performance solutions that drive business growth and enhance user experience.

What particularly attracts me to ${companyName || "[Company Name]"} is your commitment to [specific company value or project mentioned in job description]. I am eager to bring my skills in [relevant skills] to contribute to [specific goal or project].

I would welcome the opportunity to discuss how my background and enthusiasm align with ${companyName || "[Company Name]"}'s needs. Thank you for considering my application.

Sincerely,
[Your Name]`
            setGeneratedLetter(mockLetter)
            setIsGenerating(false)
        }, 2500)
    }, [contactPerson, companyName])

    const letterLengths = {
        short: "250 words",
        medium: "350 words",
        long: "450 words"
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">Cover Letter Specialist - Personalized Cover Letters</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        AI-powered personalized cover letter generation
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleGenerate}
                        disabled={isGenerating || !jobDescription}
                        className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <CpuChipIcon className={`w-4 h-4 ${isGenerating ? "animate-spin" : ""}`} />
                        {isGenerating ? "Generating..." : "Generate Letter"}
                    </button>
                </div>
            </div>

            {/* Input Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* CV/Profile Section */}
                <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <UserIcon className="w-5 h-5" />
                        CV/Profile
                    </h4>
                    <div className="space-y-4">
                        <div className="border-2 border-dashed border-[#edebe5] rounded-lg p-6 text-center">
                            {cvFile ? (
                                <div className="space-y-2">
                                    <DocumentTextIcon className="w-8 h-8 text-[#4b92ff] mx-auto" />
                                    <p className="font-medium">{cvFile.name}</p>
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
                                    <p className="text-sm text-[#7a7a7a]">Or link to saved profile</p>
                                    <input
                                        type="file"
                                        accept=".pdf,.doc,.docx"
                                        onChange={(e) => setCvFile(e.target.files?.[0] || null)}
                                        className="hidden"
                                        id="cover-letter-cv-upload"
                                    />
                                    <label
                                        htmlFor="cover-letter-cv-upload"
                                        className="inline-block px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] cursor-pointer"
                    >
                                        Choose File
                                    </label>
                                </div>
                            )}
                        </div>
                        <button className="w-full px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                            Link to Saved Profile
                    </button>
                    </div>
                </div>

                {/* Job Details */}
                <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <BuildingOfficeIcon className="w-5 h-5" />
                        Job Details
                    </h4>
                    <div className="space-y-4">
                        <div>
                            <label className="block font-medium mb-2">Job Description</label>
                            <textarea
                                value={jobDescription}
                                onChange={(e) => setJobDescription(e.target.value)}
                                placeholder="Paste job description or URL..."
                                className="w-full h-24 penpot-input resize-none"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block font-medium mb-2">Company Name</label>
                                <input
                                    type="text"
                                    value={companyName}
                                    onChange={(e) => setCompanyName(e.target.value)}
                                    placeholder="Company name"
                                    className="w-full penpot-input"
                                />
                            </div>
                            <div>
                                <label className="block font-medium mb-2">Contact Person (Optional)</label>
                                <input
                                    type="text"
                                    value={contactPerson}
                                    onChange={(e) => setContactPerson(e.target.value)}
                                    placeholder="Hiring manager name"
                                    className="w-full penpot-input"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Configuration */}
            <div className="penpot-card p-6">
                <h4 className="text-lg font-semibold mb-4">Letter Configuration</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <label className="block font-medium mb-2">Tone</label>
                        <select
                            value={tone}
                            onChange={(e) => setTone(e.target.value)}
                            className="w-full penpot-input"
                        >
                            <option value="formal">Formal</option>
                            <option value="casual">Casual</option>
                            <option value="confident">Confident</option>
                        </select>
                    </div>
                    <div>
                        <label className="block font-medium mb-2">Length</label>
                        <select
                            value={length}
                            onChange={(e) => setLength(e.target.value)}
                            className="w-full penpot-input"
                        >
                            <option value="short">Short ({letterLengths.short})</option>
                            <option value="medium">Medium ({letterLengths.medium})</option>
                            <option value="long">Long ({letterLengths.long})</option>
                        </select>
                    </div>
                    <div>
                        <label className="block font-medium mb-2">Key Points to Highlight</label>
                        <textarea
                            value={keyPoints}
                            onChange={(e) => setKeyPoints(e.target.value)}
                            placeholder="Specific achievements or experiences to emphasize..."
                            className="w-full h-20 penpot-input resize-none"
                        />
                    </div>
                </div>
            </div>

            {/* Generated Letter */}
            {generatedLetter && (
                <div className="penpot-card p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold">Generated Cover Letter</h4>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setShowPreview(!showPreview)}
                                className="flex items-center gap-2 px-3 py-1 bg-[#4b92ff] text-white rounded hover:bg-[#3a7be0] text-sm"
                            >
                                <EyeIcon className="w-4 h-4" />
                                {showPreview ? "Hide" : "Preview"}
                            </button>
                            <button className="flex items-center gap-2 px-3 py-1 bg-[#10b981] text-white rounded hover:bg-[#059669] text-sm">
                                <PencilIcon className="w-4 h-4" />
                                Edit
                            </button>
                        </div>
                    </div>

                    {showPreview ? (
                        <div className="bg-white border border-[#edebe5] rounded p-6 font-serif text-sm leading-relaxed">
                            <pre className="whitespace-pre-wrap font-sans">{generatedLetter}</pre>
                    </div>
                ) : (
                        <div className="bg-gray-50 border border-[#edebe5] rounded p-4">
                            <p className="text-[#7a7a7a] text-center">
                                Click "Preview" to see the formatted cover letter
                            </p>
                        </div>
                    )}

                    {/* Customization Panel */}
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="text-center">
                            <h5 className="font-medium mb-2">Opening Variations</h5>
                            <div className="space-y-2">
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Standard Introduction
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Referral Introduction
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Enthusiastic Opening
                                </button>
                            </div>
                        </div>
                        <div className="text-center">
                            <h5 className="font-medium mb-2">Body Options</h5>
                            <div className="space-y-2">
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Achievement Focus
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Skills Emphasis
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Cultural Fit
                                </button>
                            </div>
                        </div>
                        <div className="text-center">
                            <h5 className="font-medium mb-2">Closing Styles</h5>
                            <div className="space-y-2">
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Call to Action
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Professional Close
                                </button>
                                <button className="block w-full px-3 py-2 bg-white border border-[#edebe5] rounded text-sm hover:bg-gray-50">
                                    Enthusiastic Sign-off
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 mt-6">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download PDF
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#f59e0b] text-white rounded-lg hover:bg-[#d97706]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download Word
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#6b7280] text-white rounded-lg hover:bg-[#4b5563]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Copy to Clipboard
                        </button>
                    </div>
                    </div>
                )}
        </div>
    )
}

export default CoverLetterSpecialist
