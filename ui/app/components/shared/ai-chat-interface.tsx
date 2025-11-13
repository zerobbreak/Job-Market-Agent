import { ChevronRightIcon, PaperAirplaneIcon, SparklesIcon } from "@heroicons/react/24/outline"
import clsx from "clsx"
import { useState } from "react"
import type { SimpleMessage } from "../../../@types/chat.types"

interface AIChatInterfaceProps {
    onToggle: () => void
}

export default function AIChatInterface({ onToggle }: AIChatInterfaceProps) {
    const [messages, setMessages] = useState<SimpleMessage[]>([
        {
            id: "1",
            content: "Hello! I'm your AI legal assistant. How can I help you with your case today?",
            sender: "ai",
            timestamp: new Date(),
        },
    ])
    const [inputMessage, setInputMessage] = useState("")
    const [isLoading, setIsLoading] = useState(false)

    const sendMessage = async () => {
        if (!inputMessage.trim()) return

        const userMessage: SimpleMessage = {
            id: Date.now().toString(),
            content: inputMessage,
            sender: "user",
            timestamp: new Date(),
        }

        setMessages((prev) => [...prev, userMessage])
        setInputMessage("")
        setIsLoading(true)

        // Simulate AI response
        setTimeout(() => {
            const aiMessage: SimpleMessage = {
                id: (Date.now() + 1).toString(),
                content:
                    "I understand your question. Let me analyze this for you and provide relevant legal insights based on your case context.",
                sender: "ai",
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, aiMessage])
            setIsLoading(false)
        }, 1500)
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center gap-2">
                    <SparklesIcon className="size-5 text-indigo-600 dark:text-indigo-400" />
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        AI Assistant
                    </h2>
                </div>
                <button
                    type="button"
                    onClick={onToggle}
                    className="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label="Close AI Assistant"
                >
                    <ChevronRightIcon className="size-5" />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={clsx(
                            "flex",
                            message.sender === "user" ? "justify-end" : "justify-start"
                        )}
                    >
                        <div
                            className={clsx(
                                "max-w-sm rounded-lg px-3 py-2 text-sm",
                                message.sender === "user"
                                    ? "bg-indigo-600 text-white"
                                    : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white"
                            )}
                        >
                            <p>{message.content}</p>
                            <p
                                className={clsx(
                                    "text-xs mt-1",
                                    message.sender === "user"
                                        ? "text-indigo-200"
                                        : "text-gray-500 dark:text-gray-400"
                                )}
                            >
                                {message.timestamp.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </p>
                        </div>
                    </div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-3 py-2 text-sm">
                            <div className="flex items-center gap-1">
                                <div className="flex gap-1">
                                    <div className="size-2 bg-gray-400 rounded-full animate-pulse" />
                                    <div className="size-2 bg-gray-400 rounded-full animate-pulse delay-75" />
                                    <div className="size-2 bg-gray-400 rounded-full animate-pulse delay-150" />
                                </div>
                                <span className="text-gray-500 dark:text-gray-400 ml-2">
                                    AI is thinking...
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input area */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                <div className="flex gap-2">
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Type your message..."
                        className="flex-1 resize-none rounded-md border border-gray-300 dark:border-gray-600 px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        rows={2}
                        disabled={isLoading}
                    />
                    <button
                        type="button"
                        onClick={sendMessage}
                        disabled={!inputMessage.trim() || isLoading}
                        className="px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                        aria-label="Send message"
                    >
                        <PaperAirplaneIcon className="size-4" />
                    </button>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    Press Enter to send, Shift+Enter for new line
                </p>
            </div>
        </div>
    )
}
