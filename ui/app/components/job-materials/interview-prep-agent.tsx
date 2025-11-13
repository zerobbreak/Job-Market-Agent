import {
    ArrowPathIcon,
    DocumentTextIcon,
    CpuChipIcon,
    CheckCircleIcon,
    ClockIcon,
    BookOpenIcon,
    LightBulbIcon,
    PlayIcon,
    AcademicCapIcon,
    ArrowDownTrayIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState } from "react"

interface InterviewPrepAgentProps {
    // This component will be used for comprehensive interview preparation
}

interface Question {
    id: string
    category: string
    question: string
    type: 'behavioral' | 'technical' | 'situational' | 'background'
    difficulty: 'easy' | 'medium' | 'hard'
    starFramework?: string
    completed: boolean
}

function InterviewPrepAgent(_props: InterviewPrepAgentProps) {
    const [jobDescription, setJobDescription] = useState("")
    const [candidateProfile, setCandidateProfile] = useState("")
    const [interviewType, setInterviewType] = useState("mixed")
    const [timeAvailable, setTimeAvailable] = useState(4) // hours
    const [focusAreas, setFocusAreas] = useState<string[]>(["technical", "behavioral"])
    const [isGenerating, setIsGenerating] = useState(false)
    const [questions, setQuestions] = useState<Question[]>([])
    const [selectedCategory, setSelectedCategory] = useState("all")
    const [studyPlan, setStudyPlan] = useState<any>(null)

    // Simulate interview prep generation
    const handleGeneratePrep = useCallback(async () => {
        setIsGenerating(true)
        // Simulate API call
        setTimeout(() => {
            const mockQuestions: Question[] = [
                {
                    id: "1",
                    category: "Technical",
                    question: "Can you walk me through your development process?",
                    type: "technical",
                    difficulty: "medium",
                    starFramework: "Situation: Working on a web application project\nTask: Needed to implement new features\nAction: Planned development phases, wrote clean code, conducted testing\nResult: Delivered on time with 95% test coverage",
                    completed: false
                },
                {
                    id: "2",
                    category: "Behavioral",
                    question: "Tell me about a time you failed",
                    type: "behavioral",
                    difficulty: "hard",
                    starFramework: "Situation: Released a feature with a critical bug\nTask: Had to fix it quickly while maintaining user trust\nAction: Identified root cause, implemented fix, communicated transparently\nResult: Learned valuable lessons about testing and communication",
                    completed: false
                },
                {
                    id: "3",
                    category: "Technical",
                    question: "How do you handle code reviews?",
                    type: "technical",
                    difficulty: "easy",
                    starFramework: "Situation: Reviewing team member's pull request\nTask: Ensure code quality and standards\nAction: Check logic, test coverage, documentation, provide constructive feedback\nResult: Improved team code quality and knowledge sharing",
                    completed: false
                },
                {
                    id: "4",
                    category: "Company",
                    question: "What interests you about our company?",
                    type: "situational",
                    difficulty: "easy",
                    starFramework: "Research the company: mission, values, recent projects\nConnect your experience to company goals\nShow genuine interest in their work",
                    completed: false
                },
                {
                    id: "5",
                    category: "Background",
                    question: "Walk me through your resume",
                    type: "background",
                    difficulty: "medium",
                    starFramework: "Prepare 2-3 minute overview of your career\nHighlight key achievements with metrics\nConnect past experience to this role\nPrepare questions about career gaps",
                    completed: false
                }
            ]

            const mockStudyPlan = {
                timeline: [
                    { day: 1, focus: "Review job description and company research", hours: 1 },
                    { day: 2, focus: "Practice technical questions (10 questions)", hours: 2 },
                    { day: 3, focus: "Practice behavioral questions (8 questions)", hours: 2 },
                    { day: 4, focus: "Mock interview and review answers", hours: 2 },
                    { day: 5, focus: "Company-specific preparation and final review", hours: 1 }
                ],
                resources: [
                    "LeetCode - Practice coding problems",
                    "Pramp - Free mock interviews",
                    "Company's engineering blog and GitHub",
                    "Glassdoor interview reviews",
                    "LinkedIn company insights"
                ]
            }

            setQuestions(mockQuestions)
            setStudyPlan(mockStudyPlan)
            setIsGenerating(false)
        }, 3000)
    }, [])

    const toggleFocusArea = (area: string) => {
        setFocusAreas(prev =>
            prev.includes(area)
                ? prev.filter(a => a !== area)
                : [...prev, area]
        )
    }

    const toggleQuestionComplete = (questionId: string) => {
        setQuestions(prev =>
            prev.map(q =>
                q.id === questionId ? { ...q, completed: !q.completed } : q
            )
        )
    }

    const filteredQuestions = selectedCategory === "all"
        ? questions
        : questions.filter(q => q.category.toLowerCase() === selectedCategory.toLowerCase())

    const completedCount = questions.filter(q => q.completed).length
    const progressPercentage = questions.length > 0 ? (completedCount / questions.length) * 100 : 0

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">Interview Prep Agent - Comprehensive Interview Preparation</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        AI-powered interview preparation with personalized question sets and study plans
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleGeneratePrep}
                        disabled={isGenerating || !jobDescription}
                        className="flex items-center gap-2 px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <CpuChipIcon className={`w-4 h-4 ${isGenerating ? "animate-spin" : ""}`} />
                        {isGenerating ? "Generating..." : "Generate Prep Plan"}
                    </button>
                </div>
            </div>

            {/* Input Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Job Details */}
            <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <DocumentTextIcon className="w-5 h-5" />
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
                        <div>
                            <label className="block font-medium mb-2">Candidate Profile</label>
                            <input
                                type="text"
                                value={candidateProfile}
                                onChange={(e) => setCandidateProfile(e.target.value)}
                                placeholder="Link to your profile or enter details..."
                                className="w-full penpot-input"
                            />
                        </div>
                    </div>
                </div>

                {/* Configuration */}
                <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4">Preparation Settings</h4>
                    <div className="space-y-4">
                        <div>
                            <label className="block font-medium mb-2">Interview Type</label>
                            <select
                                value={interviewType}
                                onChange={(e) => setInterviewType(e.target.value)}
                                className="w-full penpot-input"
                            >
                                <option value="technical">Technical</option>
                                <option value="behavioral">Behavioral</option>
                                <option value="mixed">Mixed</option>
                            </select>
                        </div>

                        <div>
                            <label className="block font-medium mb-2">
                                Time Available: {timeAvailable} hour{timeAvailable !== 1 ? 's' : ''}
                            </label>
                            <input
                                type="range"
                                min="1"
                                max="8"
                                value={timeAvailable}
                                onChange={(e) => setTimeAvailable(Number(e.target.value))}
                                className="w-full"
                            />
                            <div className="flex justify-between text-xs text-[#7a7a7a] mt-1">
                                <span>1h</span>
                                <span>8h</span>
                            </div>
                        </div>

                        <div>
                            <label className="block font-medium mb-2">Focus Areas</label>
                            <div className="grid grid-cols-2 gap-2">
                                {["technical", "behavioral", "company", "background"].map(area => (
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
                    </div>
                </div>
            </div>

            {/* Results Section */}
            {studyPlan && (
                <div className="space-y-6">
                    {/* Progress Overview */}
                    <div className="penpot-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold">Preparation Progress</h4>
                            <div className="text-right">
                                <div className="text-2xl font-bold text-[#4b92ff]">
                                    {completedCount}/{questions.length}
                                </div>
                                <div className="text-sm text-[#7a7a7a]">
                                    {Math.round(progressPercentage)}% Complete
                                </div>
                            </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-[#4b92ff] h-2 rounded-full transition-all duration-300"
                                style={{ width: `${progressPercentage}%` }}
                            ></div>
                        </div>
                    </div>

                    {/* Question Bank */}
                    <div className="penpot-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h4 className="text-lg font-semibold flex items-center gap-2">
                                <BookOpenIcon className="w-5 h-5" />
                                Question Bank ({questions.length} questions)
                            </h4>
                            <select
                                value={selectedCategory}
                                onChange={(e) => setSelectedCategory(e.target.value)}
                                className="penpot-input"
                            >
                                <option value="all">All Categories</option>
                                <option value="technical">Technical</option>
                                <option value="behavioral">Behavioral</option>
                                <option value="company">Company</option>
                                <option value="background">Background</option>
                            </select>
                        </div>

                        <div className="space-y-4">
                            {filteredQuestions.map((question) => (
                                <div key={question.id} className="border border-[#edebe5] rounded-lg p-4">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                    question.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                                                    question.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                                    'bg-red-100 text-red-800'
                                                }`}>
                                                    {question.difficulty}
                                </span>
                                                <span className="text-sm text-[#7a7a7a]">{question.category}</span>
                                            </div>
                                            <h5 className="font-medium">{question.question}</h5>
                                        </div>
                                        <button
                                            onClick={() => toggleQuestionComplete(question.id)}
                                            className={`flex-shrink-0 w-6 h-6 rounded border-2 flex items-center justify-center ${
                                                question.completed
                                                    ? 'bg-[#4b92ff] border-[#4b92ff] text-white'
                                                    : 'border-[#edebe5]'
                                            }`}
                                        >
                                            {question.completed && <CheckCircleIcon className="w-4 h-4" />}
                                        </button>
                                    </div>

                                    {question.starFramework && (
                                        <div className="bg-blue-50 border border-blue-200 rounded p-3 mt-3">
                                            <div className="flex items-center gap-2 mb-2">
                                                <LightBulbIcon className="w-4 h-4 text-blue-600" />
                                                <span className="text-sm font-medium text-blue-800">STAR Framework</span>
                                            </div>
                                            <pre className="text-sm text-blue-700 whitespace-pre-wrap font-sans">
                                                {question.starFramework}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Study Plan */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="penpot-card p-6">
                            <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <ClockIcon className="w-5 h-5" />
                                Study Timeline
                            </h4>
                            <div className="space-y-3">
                                {studyPlan.timeline.map((day: any, index: number) => (
                                    <div key={index} className="flex items-center gap-3">
                                        <div className="flex-shrink-0 w-8 h-8 bg-[#4b92ff] text-white rounded-full flex items-center justify-center text-sm font-medium">
                                            {day.day}
                                        </div>
                                        <div className="flex-1">
                                            <div className="font-medium">{day.focus}</div>
                                            <div className="text-sm text-[#7a7a7a]">{day.hours} hour{day.hours !== 1 ? 's' : ''}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="penpot-card p-6">
                            <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <AcademicCapIcon className="w-5 h-5" />
                                Recommended Resources
                            </h4>
                            <div className="space-y-3">
                                {studyPlan.resources.map((resource: string, index: number) => (
                                    <div key={index} className="flex items-center gap-3">
                                        <PlayIcon className="w-4 h-4 text-[#4b92ff] flex-shrink-0" />
                                        <span className="text-sm">{resource}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#10b981] text-white rounded-lg hover:bg-[#059669]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Export Study Guide
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#f59e0b] text-white rounded-lg hover:bg-[#d97706]">
                            <ArrowDownTrayIcon className="w-4 h-4" />
                            Download Question Bank
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-[#6b7280] text-white rounded-lg hover:bg-[#4b5563]">
                            <PlayIcon className="w-4 h-4" />
                            Start Practice Session
                        </button>
                    </div>
                    </div>
                )}
        </div>
    )
}

export default InterviewPrepAgent
