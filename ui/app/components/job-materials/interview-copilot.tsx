import {
    ArrowPathIcon,
    CpuChipIcon,
    ChatBubbleLeftRightIcon,
    ClockIcon,
    LightBulbIcon,
    CheckCircleIcon,
    PaperAirplaneIcon,
    MicrophoneIcon,
    StopIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useState, useRef, useEffect } from "react"

interface InterviewCopilotProps {
    // This component will be used for real-time interview assistance
}

interface Message {
    id: string
    type: 'question' | 'suggestion' | 'analysis'
    content: string
    timestamp: Date
}

function InterviewCopilot(_props: InterviewCopilotProps) {
    const [jobTitle, setJobTitle] = useState("")
    const [companyName, setCompanyName] = useState("")
    const [interviewType, setInterviewType] = useState("phone")
    const [interviewRound, setInterviewRound] = useState("first")
    const [currentQuestion, setCurrentQuestion] = useState("")
    const [messages, setMessages] = useState<Message[]>([])
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [isRecording, setIsRecording] = useState(false)
    const [responseTime, setResponseTime] = useState(0)
    const [timerActive, setTimerActive] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Timer for response time tracking
    useEffect(() => {
        let interval: NodeJS.Timeout
        if (timerActive) {
            interval = setInterval(() => {
                setResponseTime(prev => prev + 1)
            }, 1000)
        }
        return () => clearInterval(interval)
    }, [timerActive])

    // Auto-scroll to bottom of messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60)
        const secs = seconds % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const getQuestionType = (question: string) => {
        const lowerQuestion = question.toLowerCase()
        if (lowerQuestion.includes('why') || lowerQuestion.includes('how') || lowerQuestion.includes('what') || lowerQuestion.includes('when')) {
            return 'Behavioral'
        }
        if (lowerQuestion.includes('technical') || lowerQuestion.includes('code') || lowerQuestion.includes('system')) {
            return 'Technical'
        }
        if (lowerQuestion.includes('team') || lowerQuestion.includes('culture') || lowerQuestion.includes('company')) {
            return 'Cultural'
        }
        return 'General'
    }

    // Simulate AI analysis of interview question
    const handleAnalyzeQuestion = useCallback(async () => {
        if (!currentQuestion.trim()) return

        setIsAnalyzing(true)
        setTimerActive(true)
        setResponseTime(0)

        // Add the question to messages
        const questionMessage: Message = {
            id: Date.now().toString(),
            type: 'question',
            content: currentQuestion,
            timestamp: new Date()
        }
        setMessages(prev => [...prev, questionMessage])

        // Simulate AI analysis
        setTimeout(() => {
            const questionType = getQuestionType(currentQuestion)
            const suggestions = [
                {
                    type: 'analysis' as const,
                    content: `**Question Type**: ${questionType}\n\n**STAR Framework**:\n- **Situation**: Set the context\n- **Task**: Describe your responsibility\n- **Action**: Explain what you did\n- **Result**: Share the outcome with metrics`
                },
                {
                    type: 'suggestion' as const,
                    content: `**Key Talking Points**:\n• Highlight relevant experience from your background\n• Use specific examples with measurable results\n• Connect your skills to the company's needs\n• Show enthusiasm for the role and company`
                },
                {
                    type: 'suggestion' as const,
                    content: `**Confidence Boosters**:\n• Take a deep breath before responding\n• Speak slowly and clearly\n• Make eye contact (if video interview)\n• Smile and show enthusiasm`
                }
            ]

            const analysisMessages: Message[] = suggestions.map((suggestion, index) => ({
                id: `${Date.now()}-${index}`,
                type: suggestion.type,
                content: suggestion.content,
                timestamp: new Date()
            }))

            setMessages(prev => [...prev, ...analysisMessages])
            setIsAnalyzing(false)
            setCurrentQuestion("")
        }, 2000)
    }, [currentQuestion])

    const startRecording = () => {
        setIsRecording(true)
        // In a real app, this would start audio recording
    }

    const stopRecording = () => {
        setIsRecording(false)
        // In a real app, this would process the audio and convert to text
    }

    const resetTimer = () => {
        setResponseTime(0)
        setTimerActive(false)
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="penpot-heading-medium">Interview Copilot - Real-time Interview Assistance</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mt-1">
                        AI-powered real-time guidance during job interviews
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-3 py-1 bg-[#f59e0b] text-white rounded text-sm">
                        <ClockIcon className="w-4 h-4" />
                        {formatTime(responseTime)}
                    </div>
                    <button
                        onClick={resetTimer}
                        className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
                    >
                        Reset Timer
                    </button>
                </div>
            </div>

            {/* Interview Context Setup */}
            <div className="penpot-card p-6">
                <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <ChatBubbleLeftRightIcon className="w-5 h-5" />
                    Interview Context
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <label className="block font-medium mb-2">Job Title</label>
                        <input
                            type="text"
                            value={jobTitle}
                            onChange={(e) => setJobTitle(e.target.value)}
                            placeholder="e.g., Frontend Developer"
                            className="w-full penpot-input"
                        />
                    </div>
                    <div>
                        <label className="block font-medium mb-2">Company</label>
                        <input
                            type="text"
                            value={companyName}
                            onChange={(e) => setCompanyName(e.target.value)}
                            placeholder="e.g., Tech Corp"
                            className="w-full penpot-input"
                        />
                    </div>
                    <div>
                        <label className="block font-medium mb-2">Interview Type</label>
                        <select
                            value={interviewType}
                            onChange={(e) => setInterviewType(e.target.value)}
                            className="w-full penpot-input"
                        >
                            <option value="phone">Phone</option>
                            <option value="video">Video</option>
                            <option value="in-person">In-person</option>
                        </select>
                    </div>
                    <div>
                        <label className="block font-medium mb-2">Round</label>
                        <select
                            value={interviewRound}
                            onChange={(e) => setInterviewRound(e.target.value)}
                            className="w-full penpot-input"
                        >
                            <option value="first">First Round</option>
                            <option value="second">Second Round</option>
                            <option value="final">Final Round</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Chat Interface */}
            <div className="penpot-card p-6">
                <h4 className="text-lg font-semibold mb-4">Live Interview Assistant</h4>

                {/* Messages Area */}
                <div className="bg-gray-50 border border-[#edebe5] rounded-lg p-4 mb-4 max-h-96 overflow-y-auto">
                    {messages.length === 0 ? (
                        <div className="text-center text-[#7a7a7a] py-8">
                            <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                            <p>Enter interview questions to get real-time AI guidance</p>
                        </div>
                    ) : (
                    <div className="space-y-4">
                            {messages.map((message) => (
                                <div key={message.id} className="flex gap-3">
                                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                                        message.type === 'question'
                                            ? 'bg-[#4b92ff] text-white'
                                            : message.type === 'analysis'
                                            ? 'bg-[#10b981] text-white'
                                            : 'bg-[#f59e0b] text-white'
                                    }`}>
                                        {message.type === 'question' ? (
                                            <ChatBubbleLeftRightIcon className="w-4 h-4" />
                                        ) : message.type === 'analysis' ? (
                                            <CpuChipIcon className="w-4 h-4" />
                                        ) : (
                                            <LightBulbIcon className="w-4 h-4" />
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <div className="bg-white border border-[#edebe5] rounded-lg p-3">
                                            <div className="text-sm text-[#7a7a7a] mb-1">
                                                {message.type === 'question' ? 'Your Question' : message.type === 'analysis' ? 'Question Analysis' : 'AI Suggestion'}
                                            </div>
                                            <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {isAnalyzing && (
                                <div className="flex gap-3">
                                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4b92ff] flex items-center justify-center">
                                        <CpuChipIcon className="w-4 h-4 animate-spin text-white" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="bg-white border border-[#edebe5] rounded-lg p-3">
                                            <div className="text-sm text-[#7a7a7a]">AI is analyzing your question...</div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="flex gap-3">
                    <div className="flex-1">
                        <textarea
                            value={currentQuestion}
                            onChange={(e) => setCurrentQuestion(e.target.value)}
                            placeholder="Type or paste the interviewer's question here..."
                            className="w-full penpot-input resize-none"
                            rows={3}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault()
                                    handleAnalyzeQuestion()
                                }
                            }}
                        />
                    </div>
                    <div className="flex flex-col gap-2">
                            <button
                            onClick={handleAnalyzeQuestion}
                            disabled={!currentQuestion.trim() || isAnalyzing}
                            className="px-4 py-2 bg-[#4b92ff] text-white rounded-lg hover:bg-[#3a7be0] disabled:opacity-50 flex items-center gap-2"
                            >
                            <PaperAirplaneIcon className="w-4 h-4" />
                            Analyze
                            </button>
                            <button
                            onClick={isRecording ? stopRecording : startRecording}
                            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                                isRecording
                                    ? 'bg-red-600 text-white hover:bg-red-700'
                                    : 'bg-[#10b981] text-white hover:bg-[#059669]'
                            }`}
                        >
                            {isRecording ? (
                                <>
                                    <StopIcon className="w-4 h-4" />
                                    Stop
                                </>
                            ) : (
                                <>
                                    <MicrophoneIcon className="w-4 h-4" />
                                    Record
                                </>
                            )}
                            </button>
                        </div>
                    </div>
            </div>

            {/* Follow-up Suggestions */}
            {messages.length > 0 && (
                <div className="penpot-card p-6">
                    <h4 className="text-lg font-semibold mb-4">Follow-up Suggestions</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h5 className="font-medium text-blue-800 mb-2">Technical Questions</h5>
                            <ul className="text-sm text-blue-700 space-y-1">
                                <li>• "Can you walk me through your development process?"</li>
                                <li>• "How do you handle code reviews?"</li>
                                <li>• "Describe a challenging bug you solved"</li>
                            </ul>
                        </div>
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <h5 className="font-medium text-green-800 mb-2">Behavioral Questions</h5>
                            <ul className="text-sm text-green-700 space-y-1">
                                <li>• "Tell me about a time you failed"</li>
                                <li>• "How do you handle tight deadlines?"</li>
                                <li>• "Describe your ideal work environment"</li>
                                        </ul>
                        </div>
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <h5 className="font-medium text-purple-800 mb-2">Company Questions</h5>
                            <ul className="text-sm text-purple-700 space-y-1">
                                <li>• "What interests you about our company?"</li>
                                <li>• "Where do you see yourself in 5 years?"</li>
                                <li>• "Do you have any questions for me?"</li>
                            </ul>
                            </div>
                    </div>
                    </div>
                )}
        </div>
    )
}

export default InterviewCopilot
