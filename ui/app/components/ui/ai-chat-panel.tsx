import {
    ChatBubbleLeftRightIcon,
    CheckCircleIcon,
    ClockIcon,
    DocumentTextIcon,
    ExclamationTriangleIcon,
    MagnifyingGlassIcon,
    PaperClipIcon,
    PlusIcon,
    SparklesIcon,
    XMarkIcon,
} from "@heroicons/react/24/outline"
import { useCallback, useEffect, useRef, useState } from "react"
import type { ConversationMessage } from "../../../@types/api.types"
import type { AIChatPanelProps, Chat, FileAttachment, Message } from "../../../@types/chat.types"
import { ErrorBoundary } from "~/components/ui/error-boundary"
import { useOnClickOutside } from "~/hooks"
import { getConversationHistory } from "~/services/chat.client"
import { chatActions } from "~/services/state/state.client"

function AIChatPanelContent({
    isOpen,
    onToggle,
    caseId,
    availableContexts = [],
    availableCasefiles = [],
    accessToken,
}: AIChatPanelProps) {
    // Initialize with a default chat for the current job
    const defaultChat: Chat = {
        id: `chat-${caseId || "unknown"}-default`,
        name: `AI Assistant - Job ${caseId || "Unknown"}`,
        mode: "ask",
        contexts: availableContexts || [],
        casefiles: availableCasefiles || [],
        messages: [
            {
                id: 1,
                type: "ai",
                content: `Hello! I'm your AI assistant for this job. I have access to ${(availableContexts || []).length} context${(availableContexts || []).length !== 1 ? "s" : ""} and ${(availableCasefiles || []).length} file${(availableCasefiles || []).length !== 1 ? "s" : ""}. How can I help you today?`,
                timestamp: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
                status: "delivered",
                metadata: {
                    model: "gpt-4",
                    processingTime: 0.5,
                    confidence: 0.95,
                },
            },
        ],
        isActive: true,
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        settings: {
            autoSave: true,
            maxTokens: 4096,
            temperature: 0.7,
        },
    }

    const [chats, setChats] = useState<Chat[]>([defaultChat])
    const [showHistoryPopup, setShowHistoryPopup] = useState(false)
    const [showSearch, _setShowSearch] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")
    const [messageSearchResults, setMessageSearchResults] = useState<number[]>([])
    const [_isLoadingChats, setIsLoadingChats] = useState(false)
    const [_conversationContext, setConversationContext] = useState<ConversationMessage[]>([])
    const [contextSummary, setContextSummary] = useState<string>("")

    const [newMessage, setNewMessage] = useState("")
    const [isTyping, setIsTyping] = useState(false)
    const [isNewChatModalOpen, setIsNewChatModalOpen] = useState(false)
    const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null)
    const [showContextMenu, setShowContextMenu] = useState(false)
    const [showSourcesMenu, setShowSourcesMenu] = useState(false)
    const [_showMessageActions, setShowMessageActions] = useState(false)

    const [newChatForm, setNewChatForm] = useState({
        name: "",
        mode: "ask" as "ask" | "write",
        selectedContexts: [] as string[],
        selectedCasefiles: [] as string[],
        tags: [] as string[],
    })

    // Refs for auto-scrolling and input focus
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLTextAreaElement>(null)

    // Update default chat when available contexts or files change
    // Use useCallback to prevent infinite re-renders
    const updateDefaultChat = useCallback(() => {
        setChats((prevChats) => {
            return prevChats.map((chat) => {
                if (chat.id === `chat-${caseId || "unknown"}-default`) {
                    return {
                        ...chat,
                        contexts: availableContexts || [],
                        casefiles: availableCasefiles || [],
                    }
                }
                return chat
            })
        })
    }, [caseId, availableContexts, availableCasefiles])

    useEffect(() => {
        updateDefaultChat()
    }, [updateDefaultChat])

    // Load chats from mock data on mount
    useEffect(() => {
        const loadChats = async () => {
            setIsLoadingChats(true)
            try {
                const getChats = await chatActions.getChats(caseId || "")
                const _mockChats = await getChats()
                // Note: skipping merging mock chats into state to avoid type collisions with Message
                // If no mock chats, keep existing chats (including default)
            } catch (error) {
                console.error("Failed to load chats:", error)
                // Keep existing chats on error
            } finally {
                setIsLoadingChats(false)
            }
        }

        loadChats()
    }, [caseId])

    // Load conversation history from backend
    useEffect(() => {
        const loadConversationHistory = async () => {
            if (!caseId || !accessToken) return

            try {
                const history = await getConversationHistory(caseId || "", accessToken)

                // Update conversation context and summary
                setConversationContext(history.conversation_context || [])
                setContextSummary(history.context_summary || "")

                // Convert backend conversation to chat messages
                if (history.conversation_context && history.conversation_context.length > 0) {
                    const convertedMessages: Message[] = history.conversation_context.map(
                        (msg, index) => ({
                            id: Date.now() + index,
                            type: msg.role === "user" ? "user" : "ai",
                            content: msg.content,
                            timestamp: new Date(msg.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                            }),
                            status: "delivered" as const,
                            metadata: msg.metadata,
                        })
                    )

                    // Update the active chat with conversation history
                    setChats((prevChats) =>
                        prevChats.map((chat) =>
                            chat.isActive ? { ...chat, messages: convertedMessages } : chat
                        )
                    )
                }
            } catch (error) {
                console.error("Failed to load conversation history:", error)
                // Don't show error to user, just log it - conversation will start fresh
            }
        }

        loadConversationHistory()
    }, [caseId, accessToken])

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }, [])

    // Focus input when panel opens
    useEffect(() => {
        if (isOpen && !isTyping) {
            inputRef.current?.focus()
        }
    }, [isOpen, isTyping])

    // Close menus when clicking outside or when sending message
    // Handle clicking outside context menu
    const contextMenuRef = useOnClickOutside<HTMLDivElement>(() => {
        setShowContextMenu(false)
    })

    // Handle clicking outside sources menu
    const sourcesMenuRef = useOnClickOutside<HTMLDivElement>(() => {
        setShowSourcesMenu(false)
    })

    // Close menus when sending message
    const handleSendMessageWrapper = async () => {
        setShowContextMenu(false)
        setShowSourcesMenu(false)
        await handleSendMessage()
    }

    const getActiveChat = useCallback(
        () => chats.find((chat) => chat.isActive) || chats[0],
        [chats]
    )

    const switchToChat = (chatId: string) => {
        setChats((prev) =>
            prev.map((chat) => ({
                ...chat,
                isActive: chat.id === chatId,
            }))
        )
        setSelectedMessageId(null)
        setShowMessageActions(false)
    }

    // After sending a message, refresh conversation from backend to persist
    const refreshConversationAfterSend = async () => {
        try {
            if (!accessToken) return
            const activeChat = getActiveChat()
            // activeChat.id should be the session id; if not, skip
            const sessionId = activeChat?.id?.toString() || ""
            if (!sessionId) return

            // Skip refresh for locally-generated session IDs (they start with "chat-")
            // These are mock/temporary sessions that don't exist on the backend
            if (sessionId.startsWith("chat-")) {
                console.log("[Chat] Skipping conversation refresh for local session:", sessionId)
                return
            }

            const history = await getConversationHistory(sessionId, accessToken)
            setConversationContext(history.conversation_context || [])
            setContextSummary(history.context_summary || "")

            if (history.conversation_context && history.conversation_context.length > 0) {
                const convertedMessages: Message[] = history.conversation_context.map(
                    (msg, index) => ({
                        id: Date.now() + index,
                        type: msg.role === "user" ? "user" : "ai",
                        content: msg.content,
                        timestamp: new Date(msg.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        }),
                        status: "delivered" as const,
                        metadata: msg.metadata,
                    })
                )

                setChats((prevChats) =>
                    prevChats.map((chat) =>
                        chat.id === activeChat.id ? { ...chat, messages: convertedMessages } : chat
                    )
                )
            }
        } catch (e) {
            // Handle 404 errors gracefully - session might not exist yet or is a local session
            if (
                e instanceof Error &&
                "status" in e &&
                (e as Error & { status?: number }).status === 404
            ) {
                console.log(
                    "[Chat] Session not found on backend (404) - conversation not persisted yet"
                )
                return
            }

            console.error("Failed to refresh conversation after send:", e)
            // Don't show error to user - this is optional persistence
        }
    }

    // Search functionality
    const searchMessages = useCallback(
        (query: string) => {
            if (!query.trim()) {
                setMessageSearchResults([])
                return
            }

            const activeChat = getActiveChat()
            const results: number[] = []

            activeChat.messages.forEach((message, _index) => {
                if (message.content.toLowerCase().includes(query.toLowerCase())) {
                    results.push(message.id)
                }
            })

            setMessageSearchResults(results)
        },
        [getActiveChat]
    )

    // Handle message reactions
    const addReaction = (messageId: number, emoji: string) => {
        setChats((prev) =>
            prev.map((chat) => {
                if (!chat.isActive) return chat

                return {
                    ...chat,
                    messages: chat.messages.map((message) => {
                        if (message.id !== messageId) return message

                        const existingReaction = message.reactions?.find((r) => r.emoji === emoji)
                        if (existingReaction) {
                            return {
                                ...message,
                                reactions: message.reactions?.map((r) =>
                                    r.emoji === emoji
                                        ? { ...r, count: r.count + 1, users: [...r.users, "user"] }
                                        : r
                                ),
                            }
                        }
                        return {
                            ...message,
                            reactions: [
                                ...(message.reactions || []),
                                { emoji, count: 1, users: ["user"] },
                            ],
                        }
                    }),
                }
            })
        )
    }

    const createNewChat = async () => {
        if (!newChatForm.name.trim() || newChatForm.selectedContexts.length === 0) return

        try {
            // Create new chat using mock API
            const create = await chatActions.createChat(
                caseId || "",
                newChatForm.name,
                newChatForm.mode,
                newChatForm.selectedContexts,
                newChatForm.selectedCasefiles
            )
            const newChat = await create(() => {})
            if (!newChat) {
                throw new Error("Failed to create chat")
            }

            // Add the new chat to existing chats and set it as active
            setChats((prevChats) => {
                // Set all existing chats as inactive
                const updatedChats = prevChats.map((chat) => ({
                    ...chat,
                    isActive: false,
                }))

                // Normalize newChat to local Chat type
                type RawMsg = {
                    id?: number | string
                    type?: string
                    content?: unknown
                    timestamp?: string
                    status?: string
                    attachments?: unknown
                    metadata?: unknown
                    reactions?: unknown
                }
                const rawMessages = (newChat as unknown as { messages?: RawMsg[] })?.messages ?? []
                const normalizedMessages: Message[] =
                    rawMessages.map((m: RawMsg, idx: number) => ({
                        id: typeof m?.id === "number" ? m.id : Date.now() + idx,
                        type: m?.type === "user" ? "user" : "ai",
                        content:
                            typeof m?.content === "string" ? m.content : String(m?.content ?? ""),
                        timestamp: m?.timestamp
                            ? m.timestamp
                            : new Date().toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                              }),
                        status: (m?.status === "sent"
                            ? "delivered"
                            : m?.status) as Message["status"],
                        attachments: (m?.attachments as FileAttachment[]) || undefined,
                        metadata: m?.metadata as Message["metadata"],
                        reactions: m?.reactions as Message["reactions"],
                    })) ?? []

                const obj = newChat as unknown as {
                    id?: string | number
                    name?: string
                    mode?: string
                    contexts?: string[]
                    casefiles?: string[]
                    createdAt?: string
                    lastActivity?: string
                    tags?: string[]
                    settings?: Chat["settings"]
                }

                const normalizedNewChat: Chat = {
                    id: String(obj?.id ?? `chat-${Date.now()}`),
                    name: String(obj?.name ?? newChatForm.name),
                    mode: obj?.mode === "write" ? "write" : "ask",
                    contexts: obj?.contexts ?? newChatForm.selectedContexts,
                    casefiles: obj?.casefiles ?? newChatForm.selectedCasefiles,
                    messages: normalizedMessages,
                    isActive: true,
                    createdAt: String(obj?.createdAt ?? new Date().toISOString()),
                    lastActivity: String(obj?.lastActivity ?? new Date().toISOString()),
                    tags: obj?.tags,
                    settings: obj?.settings ?? {
                        autoSave: true,
                        maxTokens: 4096,
                        temperature: 0.7,
                    },
                }

                return [...updatedChats, normalizedNewChat]
            })

            setIsNewChatModalOpen(false)
            setNewChatForm({
                name: "",
                mode: "ask",
                selectedContexts: [],
                selectedCasefiles: [],
                tags: [],
            })
        } catch (error) {
            console.error("Failed to create new chat:", error)
            // Fallback to local creation if API fails
            const now = new Date().toISOString()
            const fallbackChat: Chat = {
                id: `chat-${Date.now()}`,
                name: newChatForm.name,
                mode: newChatForm.mode,
                contexts: newChatForm.selectedContexts,
                casefiles: newChatForm.selectedCasefiles,
                messages: [
                    {
                        id: 1,
                        type: "ai",
                        content: `Hello! I'm ready to help you with your ${newChatForm.mode === "ask" ? "questions" : "writing"}. I have access to ${newChatForm.selectedContexts.join(", ")} ${newChatForm.selectedContexts.length === 1 ? "context" : "contexts"} and ${newChatForm.selectedCasefiles.length} ${newChatForm.selectedCasefiles.length === 1 ? "file" : "files"}.`,
                        timestamp: new Date().toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        }),
                        status: "delivered",
                        metadata: {
                            model: "gpt-4",
                            processingTime: 0.3,
                            confidence: 0.92,
                        },
                    },
                ],
                isActive: true,
                createdAt: now,
                lastActivity: now,
                tags: newChatForm.tags,
                settings: {
                    autoSave: true,
                    maxTokens: 4096,
                    temperature: 0.7,
                },
            }

            setChats((prev) =>
                prev.map((chat) => ({ ...chat, isActive: false })).concat(fallbackChat)
            )
            setIsNewChatModalOpen(false)
            setNewChatForm({
                name: "",
                mode: "ask",
                selectedContexts: [],
                selectedCasefiles: [],
                tags: [],
            })
        }
    }

    const _generateAIResponse = (
        userMessage: string,
        chatMode: "ask" | "write",
        contexts: string[],
        casefiles: string[]
    ) => {
        const lowerMessage = userMessage.toLowerCase()

        // Context-aware responses based on legal topics
        if (
            lowerMessage.includes("stark") ||
            lowerMessage.includes("rogers") ||
            lowerMessage.includes("sokovia")
        ) {
            if (chatMode === "ask") {
                return {
                    content: `Based on the job application materials, here's my analysis:\n\n**Key Application Issues:**\n• Resume optimization for ATS systems\n• Interview preparation and STAR method responses\n• Company research and cultural fit assessment\n• Salary negotiation strategies\n\n**Relevant Facts:**\n- ATS compatibility scores can vary significantly\n- Behavioral questions require structured responses\n- Company culture impacts interview success\n- Market salary ranges depend on location and experience\n\n**Recommended Actions:**\n1. **Optimize resume** for ATS systems\n2. **Practice behavioral questions** using STAR method\n3. **Research company** thoroughly before interview\n4. **Prepare salary expectations** based on market data\n\nWould you like me to elaborate on any specific aspect?`,
                    sources: ["Sokovia Accords Document", "Meeting Minutes", "Incident Reports"],
                }
            }
            return {
                content: `I'll help you draft content for the ${contexts.join(", ")} context. Based on your request to "${userMessage}", here's a suggested addition:\n\n**F-008. Compliance Efforts and Breach Analysis**\n\nFollowing the Bucharest incident, Stark engaged in multiple compliance efforts while Rogers demonstrated a pattern of disregard for established oversight mechanisms:\n\na) Stark's Compliance Actions [R1 §4.2]:\n   - Signed Sokovia Accords immediately upon presentation\n   - Attempted retroactive authorization for Avengers operations\n   - Maintained communication with UN oversight bodies\n\nb) Rogers' Breach Pattern [R4 access-log #A17]:\n   - Unauthorized departure from compound without approval\n   - Initiation of unsanctioned international operation\n   - Refusal to submit to established oversight framework\n\nc) Resulting Damages [R11 §5.1]:\n   - Property damage estimated at $2.4-3.1M\n   - Multiple injuries requiring medical intervention\n   - Compromised international diplomatic relations\n\nSources: [R1 §4.2; R4 access-log #A17; R11 §5.1]`,
                sources: ["Sokovia Accords", "Access Logs", "Damage Assessments"],
            }
        }

        // General legal responses
        if (lowerMessage.includes("contract") || lowerMessage.includes("breach")) {
            return {
                content: `Regarding contract law principles applicable here:\n\n**Contract Formation:** The Sokovia Accords constitute a valid international agreement with mutual obligations between signatories and governing bodies.\n\n**Breach Analysis:**\n• **Material Breach**: Failure to obtain required authorizations constitutes material breach\n• **Anticipatory Repudiation**: Rogers' refusal to sign indicated anticipatory breach\n• **Remedies Available**: Specific performance, damages, injunctive relief\n\n**Precedent Citations:**\n- *Smith v. Johnson* (2022): Material breach excused performance obligations\n- *Davis Corp v. Wilson LLC* (2021): Anticipatory repudiation claims\n\nWould you like me to draft specific contract language or analyze particular breach elements?`,
                sources: ["Contract Law Database", "Case Precedents"],
            }
        }

        // Default responses based on mode
        if (chatMode === "ask") {
            return {
                content: `I've analyzed your question "${userMessage}" in the context of ${contexts.join(", ")}. Based on the available job materials:\n\n**Analysis Summary:**\nThe query touches on several key job application principles. Let me break this down:\n\n1. **Application Framework**: The situation involves ${contexts.length > 1 ? "multiple application contexts" : "a specific application context"}\n2. **Key Facts**: ${casefiles.length} relevant sources are available\n3. **Applicable Strategies**: Standard application principles apply with job-specific modifications\n\n**Recommended Approach:**\n- Review the ${contexts[0]} context for foundational information\n- Cross-reference with available job files\n- Consider industry and role-specific requirements\n\nWould you like me to investigate any specific aspect in more detail?`,
                sources: contexts.map((ctx) => `${ctx} Context`).concat(casefiles.slice(0, 2)),
            }
        }
        return {
            content: `I'll help you edit the ${contexts.join(", ")} context. Based on "${userMessage}", here's a suggested addition:\n\n**AI-Generated Content Addition**\n\n[Draft content would be inserted here based on the specific context and user request. This represents how the AI would modify or add to the existing job materials.]\n\n**Rationale for Addition:**\n- Addresses the specific request in your message\n- Maintains consistency with existing job materials\n- Includes proper source citations\n- Follows professional writing conventions\n\nYou can accept, reject, or modify this suggested content before adding it to your job materials.`,
            sources: ["AI Analysis", "Context Review"],
        }
    }

    const handleAddContext = (context: string) => {
        const contextPrefix = `@${context}`
        const currentMessage = newMessage.trim()
        const newMessageText = currentMessage ? `${currentMessage} ${contextPrefix}` : contextPrefix

        setNewMessage(newMessageText)
        setShowContextMenu(false)
        inputRef.current?.focus()
    }

    const handleAddSource = (source: string) => {
        const sourceReference = `[${source}]`
        const currentMessage = newMessage.trim()
        const newMessageText = currentMessage
            ? `${currentMessage} ${sourceReference}`
            : sourceReference

        setNewMessage(newMessageText)
        setShowSourcesMenu(false)
        inputRef.current?.focus()
    }

    const handleSendMessage = async () => {
        if (!newMessage.trim() || isTyping) return
        const activeChat = getActiveChat()
        if (!activeChat) return

        const messageToSend = newMessage
        setNewMessage("")
        setIsTyping(true)

        try {
            // Determine mode based on chat mode: "ask" -> "law", "write" -> "facts"
            const apiMode = activeChat.mode === "write" ? "facts" : "law"

            // Send message using real API if accessToken is available
            const sendAction = chatActions.sendMessage(
                caseId || "",
                activeChat.id,
                messageToSend,
                apiMode,
                accessToken
            )
            const response = await sendAction(() => {})

            // Optimistic update: append user and AI messages locally
            setChats((prev) =>
                prev.map((chat) => {
                    if (chat.id !== activeChat.id) return chat
                    const userMessage: Message = {
                        id: Date.now(),
                        type: "user",
                        content: messageToSend,
                        timestamp: new Date().toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        }),
                        status: "delivered",
                    }
                    const aiMessage: Message = {
                        id: typeof response?.id === "number" ? response.id : Date.now() + 1,
                        type: "ai",
                        content:
                            response?.content ||
                            "I apologize, but I couldn't generate a response. Please try again.",
                        timestamp: new Date().toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                        }),
                        status: "delivered",
                        metadata: response?.metadata,
                    }
                    return {
                        ...chat,
                        messages: [...chat.messages, userMessage, aiMessage],
                        lastActivity: new Date().toISOString(),
                    }
                })
            )

            // Refresh persisted conversation from backend
            await refreshConversationAfterSend()
        } catch (error) {
            console.error("Failed to send message:", error)

            // Extract error message from the error object
            let errorContent =
                "Sorry, I encountered an error while processing your message. Please try again."

            if (error instanceof Error) {
                // Use the actual error message from the API (already user-friendly)
                errorContent = error.message

                // Don't add status code prefix for user-friendly messages
                // The error message from the API is already formatted nicely
            }

            // Add error message to chat
            const errorMessage: Message = {
                id: Date.now(),
                type: "ai",
                content: errorContent,
                timestamp: new Date().toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                }),
                status: "error",
                metadata: {
                    model: "error",
                    processingTime: 0,
                    confidence: 0,
                },
            }

            setChats((prev) =>
                prev.map((chat) => {
                    if (chat.id === activeChat.id) {
                        return {
                            ...chat,
                            messages: [...chat.messages, errorMessage],
                            lastActivity: new Date().toISOString(),
                        }
                    }
                    return chat
                })
            )
        } finally {
            setIsTyping(false)
        }
    }

    if (!isOpen) {
        const activeChat = getActiveChat()
        const unreadCount =
            activeChat?.messages.filter((m) => m.status === "delivered" && m.type === "ai")
                .length || 0

        return (
            <div className="hidden md:flex flex-col items-center justify-start pt-4 bg-[#f7f4ed] border-l border-[#edebe5] w-12 md:w-16">
                <div className="relative">
                    <button
                        type="button"
                        onClick={onToggle}
                        className="p-2 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors relative"
                        aria-label="Open AI Assistant"
                        title={`${activeChat?.name || "AI Assistant"} - ${activeChat?.messages.length || 0} messages`}
                    >
                        <SparklesIcon className="size-5" />
                    </button>
                    {unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium">
                            {unreadCount > 9 ? "9+" : unreadCount}
                        </span>
                    )}
                </div>
                <div className="mt-2 text-xs text-[#7a7a7a] text-center px-1">AI</div>
            </div>
        )
    }

    const activeChat = getActiveChat()

    // Safety check - don't render if no active chat
    if (!activeChat) {
        return (
            <div className="hidden md:flex flex-col bg-[#f7f4ed] border-l border-[#edebe5] w-full h-full rounded-3xl m-2 md:m-4 p-4 md:p-[20px] items-center justify-center">
                <div className="text-center text-[#7a7a7a]">
                    <div className="text-2xl mb-2">💭</div>
                    <div className="text-sm">Loading chat...</div>
                </div>
            </div>
        )
    }

    return (
        <>
            <div className="hidden md:flex flex-col bg-[#f7f4ed] border-l border-[#edebe5] w-full h-full rounded-3xl m-2 md:m-4 p-4 md:p-[20px] gap-4 md:gap-6">
                {/* Chat Header - Matching HTML Design */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-sm font-medium">
                        <span className="text-sm">✨</span>
                        <span>Ask AI</span>
                    </div>
                    <div className="flex items-center gap-1">
                        {/* Collapse Button */}
                        <button
                            type="button"
                            onClick={onToggle}
                            className="p-1 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                            aria-label="Collapse chat panel"
                            title="Collapse chat panel"
                        >
                            <svg
                                className="w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Collapse"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M15 19l-7-7 7-7"
                                />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Search Bar */}
                {showSearch && (
                    <div className="p-3 border-b border-[#edebe5] bg-white">
                        <div className="relative">
                            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 size-4 text-[#7a7a7a]" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value)
                                    searchMessages(e.target.value)
                                }}
                                placeholder="Search messages..."
                                className="w-full pl-9 pr-3 py-2 text-sm border border-[#edebe5] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4b92ff] focus:border-transparent"
                            />
                            {messageSearchResults.length > 0 && (
                                <span className="absolute right-3 top-1/2 transform -translate-y-1/2 text-xs text-[#7a7a7a]">
                                    {messageSearchResults.length} found
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Conversation Summary (if available) */}
                {contextSummary && (
                    <div className="px-4 pt-3">
                        <div className="bg-[#f7f4ee] border border-[#edebe5] rounded-lg p-3">
                            <div className="flex items-center gap-2 text-xs text-[#7a7a7a] mb-1">
                                <ChatBubbleLeftRightIcon className="size-4" />
                                <span>Conversation Summary</span>
                            </div>
                            <p className="text-sm text-[#151515] whitespace-pre-wrap">
                                {contextSummary}
                            </p>
                        </div>
                    </div>
                )}

                {/* Messages */}
                <div className="flex-1 overflow-y-auto">
                    <div className="p-4 space-y-4 min-h-full">
                        {activeChat.messages.map((message) => {
                            const isHighlighted = messageSearchResults.includes(message.id)
                            return (
                                // biome-ignore lint/a11y/useSemanticElements: Div with role="group" needed for message layout and interaction
                                <div
                                    key={message.id}
                                    className={`flex ${message.type === "user" ? "justify-end" : "justify-start"} group`}
                                    role="group"
                                    onMouseEnter={() => setSelectedMessageId(message.id)}
                                    onMouseLeave={() => setSelectedMessageId(null)}
                                    onFocus={() => setSelectedMessageId(message.id)}
                                    onBlur={() => setSelectedMessageId(null)}
                                >
                                    <div
                                        className={`max-w-[85%] ${message.type === "user" ? "order-2" : "order-1"}`}
                                    >
                                        <div
                                            className={`p-3 rounded-lg shadow-sm ${
                                                isHighlighted
                                                    ? "ring-2 ring-yellow-400 ring-opacity-50"
                                                    : ""
                                            } ${
                                                message.type === "user"
                                                    ? "bg-[#4b92ff] text-white"
                                                    : message.status === "error"
                                                      ? "bg-red-50 text-red-700 border border-red-200"
                                                      : "bg-white text-[#151515] border border-[#edebe5]"
                                            }`}
                                        >
                                            {/* Message Header */}
                                            <div
                                                key="message-header"
                                                className={`flex items-center gap-2 mb-2 ${
                                                    message.type === "user"
                                                        ? "justify-end"
                                                        : "justify-start"
                                                }`}
                                            >
                                                <div
                                                    className={`flex items-center gap-1 text-xs ${
                                                        message.type === "user"
                                                            ? "text-blue-100"
                                                            : "text-[#7a7a7a]"
                                                    }`}
                                                >
                                                    {message.type === "ai" &&
                                                        message.metadata?.model && (
                                                            <span className="font-medium">
                                                                {message.metadata.model}
                                                            </span>
                                                        )}
                                                    <ClockIcon className="size-3" />
                                                    <span>{message.timestamp}</span>
                                                </div>
                                                {message.status === "sending" && (
                                                    <div className="flex space-x-1">
                                                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                                                        <div
                                                            className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"
                                                            style={{ animationDelay: "0.1s" }}
                                                        />
                                                        <div
                                                            className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"
                                                            style={{ animationDelay: "0.2s" }}
                                                        />
                                                    </div>
                                                )}
                                                {message.status === "delivered" &&
                                                    message.type === "ai" && (
                                                        <CheckCircleIcon className="size-3 text-green-500" />
                                                    )}
                                                {message.status === "error" && (
                                                    <ExclamationTriangleIcon className="size-3 text-red-500" />
                                                )}
                                            </div>

                                            {/* Message Content */}
                                            <div
                                                key="message-content"
                                                className="prose prose-sm max-w-none"
                                            >
                                                <p
                                                    className={`text-sm whitespace-pre-line ${
                                                        message.type === "user"
                                                            ? "text-white"
                                                            : "text-[#151515]"
                                                    }`}
                                                >
                                                    {message.content}
                                                </p>
                                            </div>

                                            {/* Message Metadata */}
                                            {message.metadata && (
                                                <div
                                                    key="message-metadata"
                                                    className={`mt-2 pt-2 border-t ${
                                                        message.type === "user"
                                                            ? "border-blue-200"
                                                            : "border-[#edebe5]"
                                                    }`}
                                                >
                                                    <div className="flex items-center justify-between text-xs">
                                                        <div
                                                            className={`flex items-center gap-3 ${
                                                                message.type === "user"
                                                                    ? "text-blue-100"
                                                                    : "text-[#7a7a7a]"
                                                            }`}
                                                        >
                                                            {message.metadata.processingTime && (
                                                                <span key="processing-time">
                                                                    {
                                                                        message.metadata
                                                                            .processingTime
                                                                    }
                                                                    s
                                                                </span>
                                                            )}
                                                            {message.metadata.confidence && (
                                                                <span key="confidence">
                                                                    {Math.round(
                                                                        message.metadata
                                                                            .confidence * 100
                                                                    )}
                                                                    % confidence
                                                                </span>
                                                            )}
                                                            {message.metadata.tokens && (
                                                                <span key="tokens">
                                                                    {message.metadata.tokens} tokens
                                                                </span>
                                                            )}
                                                        </div>
                                                        {message.metadata.sources &&
                                                            message.metadata.sources.length > 0 && (
                                                                <div className="flex items-center gap-1">
                                                                    <DocumentTextIcon className="size-3" />
                                                                    <span className="truncate max-w-24">
                                                                        {message.metadata.sources
                                                                            .slice(0, 2)
                                                                            .join(", ")}
                                                                        {message.metadata.sources
                                                                            .length > 2 && "..."}
                                                                    </span>
                                                                </div>
                                                            )}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Attachments */}
                                            {message.attachments &&
                                                message.attachments.length > 0 && (
                                                    <div
                                                        key="message-attachments"
                                                        className="mt-2 space-y-1"
                                                    >
                                                        {message.attachments.map(
                                                            (attachment: FileAttachment) => (
                                                                <div
                                                                    key={attachment.id}
                                                                    className={`flex items-center gap-2 p-2 rounded text-xs ${
                                                                        message.type === "user"
                                                                            ? "bg-blue-600 text-blue-100"
                                                                            : "bg-gray-50 text-[#7a7a7a]"
                                                                    }`}
                                                                >
                                                                    <PaperClipIcon className="size-3" />
                                                                    <span className="truncate">
                                                                        {attachment.name}
                                                                    </span>
                                                                    <span>
                                                                        (
                                                                        {Math.round(
                                                                            attachment.size / 1024
                                                                        )}
                                                                        KB)
                                                                    </span>
                                                                </div>
                                                            )
                                                        )}
                                                    </div>
                                                )}
                                        </div>

                                        {/* Reactions */}
                                        {message.reactions && message.reactions.length > 0 && (
                                            <div
                                                key="message-reactions"
                                                className={`flex gap-1 mt-1 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                                            >
                                                {message.reactions.map((reaction) => (
                                                    <button
                                                        type="button"
                                                        key={reaction.emoji}
                                                        onClick={() =>
                                                            addReaction(message.id, reaction.emoji)
                                                        }
                                                        className="flex items-center gap-1 px-2 py-1 bg-white border border-[#edebe5] rounded-full text-xs hover:bg-gray-50 transition-colors"
                                                    >
                                                        <span>{reaction.emoji}</span>
                                                        <span className="text-[#7a7a7a]">
                                                            {reaction.count}
                                                        </span>
                                                    </button>
                                                ))}
                                            </div>
                                        )}

                                        {/* Message Actions */}
                                        {selectedMessageId === message.id && (
                                            <div
                                                key="message-actions"
                                                className={`flex gap-1 mt-1 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                                            >
                                                {["👍", "❤️", "😂", "😮", "😢"].map((emoji) => (
                                                    <button
                                                        type="button"
                                                        key={emoji}
                                                        onClick={() =>
                                                            addReaction(message.id, emoji)
                                                        }
                                                        className="w-8 h-8 flex items-center justify-center text-lg hover:bg-gray-100 rounded transition-colors"
                                                        title={`React with ${emoji}`}
                                                    >
                                                        {emoji}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )
                        })}

                        {/* Typing Indicator */}
                        {isTyping && (
                            <div className="flex justify-start">
                                <div className="p-3 rounded-[16px] bg-[#fcfbf8] text-[#151515] border border-[#edebe5] max-w-[360px] shadow-[0_4px_10px_rgba(211,207,193,0.1)]">
                                    <div className="flex items-center space-x-3">
                                        <div className="flex space-x-1">
                                            <div className="w-2 h-2 bg-[#4b92ff] rounded-full animate-pulse" />
                                            <div
                                                className="w-2 h-2 bg-[#4b92ff] rounded-full animate-pulse"
                                                style={{ animationDelay: "0.2s" }}
                                            />
                                            <div
                                                className="w-2 h-2 bg-[#4b92ff] rounded-full animate-pulse"
                                                style={{ animationDelay: "0.4s" }}
                                            />
                                        </div>
                                        <span className="text-xs text-[#7a7a7a]">
                                            AI is analyzing your request...
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Scroll Anchor */}
                        <div ref={messagesEndRef} />
                    </div>
                </div>

                {/* Input Area - Matching HTML Design */}
                <div className="bg-[#fcfbf8] border border-[#edebe5] rounded-[16px] p-3 shadow-[0_4px_10px_rgba(211,207,193,0.1)]">
                    {/* File Preview Area */}
                    {/* This could be expanded to show selected files before sending */}

                    {/* Input Controls */}
                    <div className="flex gap-2 items-end">
                        <div className="flex-1 relative">
                            <textarea
                                ref={inputRef}
                                value={newMessage}
                                onChange={(e) => setNewMessage(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && !e.shiftKey) {
                                        e.preventDefault()
                                        if (!isTyping) handleSendMessageWrapper()
                                    }
                                }}
                                placeholder={
                                    isTyping
                                        ? "AI is responding..."
                                        : activeChat.mode === "ask"
                                          ? "Ask about your job... (Enter to send, Shift+Enter for new line)"
                                          : "What would you like me to write or edit... (Enter to send, Shift+Enter for new line)"
                                }
                                disabled={isTyping}
                                rows={1}
                                className="w-full px-4 py-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed resize-none min-h-[48px] max-h-32 rounded-2xl border border-[#edebe5] bg-white focus:outline-none focus:ring-2 focus:ring-[#4b92ff] focus:border-transparent shadow-sm"
                                style={{ height: "auto", minHeight: "48px" }}
                                onInput={(e) => {
                                    const target = e.target as HTMLTextAreaElement
                                    target.style.height = "auto"
                                    target.style.height = `${Math.min(target.scrollHeight, 128)}px`
                                }}
                            />

                            {/* Character Count */}
                            {newMessage.length > 100 && (
                                <div className="absolute -top-6 right-0 text-xs text-[#7a7a7a]">
                                    {newMessage.length}/2000
                                </div>
                            )}
                        </div>

                        <div className="flex gap-1">
                            {/* Send Button - Matching HTML Design */}
                            <button
                                type="button"
                                onClick={handleSendMessageWrapper}
                                disabled={
                                    !newMessage.trim() || isTyping || newMessage.length > 2000
                                }
                                className="w-6 h-6 bg-black border-none rounded-[20px] flex items-center justify-center cursor-pointer text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                title="Send message"
                            >
                                ↑
                            </button>
                        </div>
                    </div>

                    {/* Input Options - Matching HTML Design */}
                    <div className="flex gap-2 mt-2">
                        <div className="relative" ref={contextMenuRef}>
                            <button
                                type="button"
                                onClick={() => setShowContextMenu(!showContextMenu)}
                                className="px-3 py-2 border border-[#edebe5] rounded-[16px] text-sm bg-transparent hover:bg-[#f7f4ed] transition-colors"
                            >
                                @ Add context
                            </button>
                            {showContextMenu && (
                                <div className="absolute bottom-full mb-2 left-0 bg-white border border-[#edebe5] rounded-lg shadow-lg p-2 min-w-48 z-50">
                                    <div className="text-xs text-[#7a7a7a] mb-2 px-2">
                                        Available contexts:
                                    </div>
                                    {[
                                        "Facts",
                                        "Research",
                                        "Drafting",
                                        "Evidence",
                                        "Notes",
                                        "Custom",
                                    ].map((context) => (
                                        <button
                                            key={context}
                                            onClick={() => handleAddContext(context)}
                                            className="w-full text-left px-2 py-1 text-sm hover:bg-[#f7f4ed] rounded transition-colors"
                                        >
                                            @{context}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="relative" ref={sourcesMenuRef}>
                            <button
                                onClick={() => setShowSourcesMenu(!showSourcesMenu)}
                                className="px-3 py-2 border border-[#edebe5] rounded-[16px] text-sm bg-transparent hover:bg-[#f7f4ed] transition-colors"
                            >
                                Case sources
                            </button>
                            {showSourcesMenu && (
                                <div className="absolute bottom-full mb-2 left-0 bg-white border border-[#edebe5] rounded-lg shadow-lg p-2 min-w-48 max-h-48 overflow-y-auto z-50">
                                    <div className="text-xs text-[#7a7a7a] mb-2 px-2">
                                        Available sources:
                                    </div>
                                    {availableCasefiles.map((file) => (
                                        <button
                                            key={`${file}-source`}
                                            onClick={() => handleAddSource(file)}
                                            className="w-full text-left px-2 py-1 text-sm hover:bg-[#f7f4ed] rounded transition-colors truncate"
                                            title={file}
                                        >
                                            [{file}]
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="mt-3 flex gap-2 flex-wrap">
                        <button
                            onClick={() => setIsNewChatModalOpen(true)}
                            className="penpot-button-secondary text-xs flex items-center gap-1"
                        >
                            <PlusIcon className="size-3" />
                            New Chat
                        </button>
                        <button className="penpot-button-secondary text-xs">
                            <span className="text-xs">📄</span> Add to Case Material
                        </button>
                    </div>

                    {/* Chat Stats */}
                    <div className="mt-2 flex items-center justify-between text-xs text-[#7a7a7a]">
                        <span>{activeChat.messages.length} messages</span>
                        <span>
                            Last activity:{" "}
                            {new Date(
                                activeChat.lastActivity || activeChat.createdAt
                            ).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                            })}
                        </span>
                    </div>
                </div>
            </div>

            {/* History Popup */}
            {showHistoryPopup && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
                        <div className="p-4 border-b border-[#edebe5] flex items-center justify-between">
                            <h3 className="penpot-heading-medium">Chat History</h3>
                            <button
                                onClick={() => setShowHistoryPopup(false)}
                                className="p-1 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                            >
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex-1 p-4 space-y-3 overflow-y-auto max-h-96">
                            {chats.map((chat) => (
                                <div
                                    key={chat.id}
                                    className={`p-4 rounded-lg cursor-pointer transition-all duration-200 border ${
                                        chat.isActive
                                            ? "bg-[#4b92ff] text-white border-[#4b92ff] shadow-md"
                                            : "bg-white hover:bg-gray-50 hover:shadow-sm border-[#edebe5]"
                                    }`}
                                    onClick={() => {
                                        switchToChat(chat.id)
                                        setShowHistoryPopup(false)
                                    }}
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-sm font-medium truncate mb-1">
                                                {chat.name}
                                            </h4>
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span
                                                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                                        chat.mode === "ask"
                                                            ? chat.isActive
                                                                ? "bg-blue-200 text-blue-900"
                                                                : "bg-blue-100 text-blue-800"
                                                            : chat.isActive
                                                              ? "bg-purple-200 text-purple-900"
                                                              : "bg-purple-100 text-purple-800"
                                                    }`}
                                                >
                                                    {chat.mode.toUpperCase()}
                                                </span>
                                                {chat.tags?.map((tag) => (
                                                    <span
                                                        key={tag}
                                                        className={`text-xs px-1.5 py-0.5 rounded ${
                                                            chat.isActive
                                                                ? "bg-white/20 text-white"
                                                                : "bg-gray-100 text-[#7a7a7a]"
                                                        }`}
                                                    >
                                                        #{tag}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                        {chat.isActive && (
                                            <div className="w-2 h-2 bg-white rounded-full flex-shrink-0 mt-1" />
                                        )}
                                    </div>

                                    <div className="space-y-1">
                                        <div
                                            className={`text-sm ${chat.isActive ? "text-blue-100" : "text-[#7a7a7a]"}`}
                                        >
                                            <span className="font-medium">
                                                {chat.contexts.length}
                                            </span>{" "}
                                            contexts,{" "}
                                            <span className="font-medium">
                                                {chat.casefiles.length}
                                            </span>{" "}
                                            files
                                        </div>
                                        <div
                                            className={`flex items-center justify-between text-xs ${chat.isActive ? "text-blue-200" : "text-[#7a7a7a]"}`}
                                        >
                                            <span>{chat.messages.length} messages</span>
                                            <span>
                                                {new Date(
                                                    chat.lastActivity || chat.createdAt
                                                ).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="p-4 border-t border-[#edebe5]">
                            <button
                                onClick={() => {
                                    setShowHistoryPopup(false)
                                    setIsNewChatModalOpen(true)
                                }}
                                className="w-full penpot-button-primary flex items-center justify-center gap-2"
                            >
                                <PlusIcon className="w-4 h-4" />
                                Start New Chat
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* New Chat Modal */}
            {isNewChatModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-medium">Create New Chat</h3>
                                <button
                                    onClick={() => setIsNewChatModalOpen(false)}
                                    className="p-1 rounded-md text-[#7a7a7a] hover:text-[#151515] hover:bg-[#edebe5] transition-colors"
                                >
                                    <XMarkIcon className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Chat Configuration */}
                            <div className="space-y-6">
                                <div>
                                    <label
                                        htmlFor="new-chat-name"
                                        className="block text-sm font-medium mb-2"
                                    >
                                        Chat Name
                                    </label>
                                    <input
                                        id="new-chat-name"
                                        type="text"
                                        value={newChatForm.name}
                                        onChange={(e) =>
                                            setNewChatForm({ ...newChatForm, name: e.target.value })
                                        }
                                        placeholder="e.g., Legal Research - Sokovia Accords"
                                        className="penpot-input w-full"
                                    />
                                </div>

                                {/* Context Selection */}
                                <div>
                                    <h4 className="text-sm font-medium mb-3">Context Selection</h4>
                                    <div className="space-y-2 max-h-32 overflow-y-auto border border-[#edebe5] rounded-lg p-3">
                                        {[
                                            "Facts",
                                            "Research",
                                            "Drafting",
                                            "Evidence",
                                            "Notes",
                                            "Custom",
                                        ].map((context) => (
                                            <label
                                                key={context}
                                                className="flex items-center gap-2"
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={newChatForm.selectedContexts.includes(
                                                        context
                                                    )}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setNewChatForm({
                                                                ...newChatForm,
                                                                selectedContexts: [
                                                                    ...newChatForm.selectedContexts,
                                                                    context,
                                                                ],
                                                            })
                                                        } else {
                                                            setNewChatForm({
                                                                ...newChatForm,
                                                                selectedContexts:
                                                                    newChatForm.selectedContexts.filter(
                                                                        (c) => c !== context
                                                                    ),
                                                            })
                                                        }
                                                    }}
                                                    className="rounded border-[#edebe5]"
                                                />
                                                <span className="text-sm">{context} Context</span>
                                            </label>
                                        ))}
                                    </div>
                                    <p className="text-xs text-[#7a7a7a] mt-1">
                                        Selected Contexts: {newChatForm.selectedContexts.length} of
                                        6
                                    </p>
                                </div>

                                {/* Casefile Selection */}
                                <div>
                                    <h4 className="text-sm font-medium mb-3">Casefile Selection</h4>
                                    <div className="space-y-2 max-h-32 overflow-y-auto border border-[#edebe5] rounded-lg p-3">
                                        {availableCasefiles.length > 0 ? (
                                            availableCasefiles.map((file, index) => (
                                                <label
                                                    key={`${file}-${index}`}
                                                    className="flex items-center gap-2"
                                                >
                                                    <input
                                                        type="checkbox"
                                                        checked={newChatForm.selectedCasefiles.includes(
                                                            file
                                                        )}
                                                        onChange={(e) => {
                                                            if (e.target.checked) {
                                                                setNewChatForm({
                                                                    ...newChatForm,
                                                                    selectedCasefiles: [
                                                                        ...newChatForm.selectedCasefiles,
                                                                        file,
                                                                    ],
                                                                })
                                                            } else {
                                                                setNewChatForm({
                                                                    ...newChatForm,
                                                                    selectedCasefiles:
                                                                        newChatForm.selectedCasefiles.filter(
                                                                            (f) => f !== file
                                                                        ),
                                                                })
                                                            }
                                                        }}
                                                        className="rounded border-[#edebe5]"
                                                    />
                                                    <span className="text-sm">{file}</span>
                                                </label>
                                            ))
                                        ) : (
                                            <p className="text-sm text-[#7a7a7a]">
                                                No job files available
                                            </p>
                                        )}
                                    </div>
                                    <p className="text-xs text-[#7a7a7a] mt-1">
                                        Selected Files: {newChatForm.selectedCasefiles.length} of{" "}
                                        {availableCasefiles.length}
                                    </p>
                                </div>

                                {/* Chat Mode Selection */}
                                <div>
                                    <h4 className="text-sm font-medium mb-3">
                                        Chat Mode Selection
                                    </h4>
                                    <div className="space-y-3">
                                        <label className="flex items-start gap-3 p-3 border border-[#edebe5] rounded-lg hover:bg-[#f7f4ed] cursor-pointer transition-colors">
                                            <input
                                                type="radio"
                                                name="mode"
                                                value="ask"
                                                checked={newChatForm.mode === "ask"}
                                                onChange={(e) =>
                                                    setNewChatForm({
                                                        ...newChatForm,
                                                        mode: e.target.value as "ask" | "write",
                                                    })
                                                }
                                                className="mt-1"
                                            />
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <div className="text-sm font-medium">
                                                        ASK Mode
                                                    </div>
                                                    <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                                                        Q&A
                                                    </span>
                                                </div>
                                                <p className="text-xs text-[#7a7a7a]">
                                                    AI answers questions based on selected contexts
                                                    and files with source citations and legal
                                                    analysis.
                                                </p>
                                            </div>
                                        </label>
                                        <label className="flex items-start gap-3 p-3 border border-[#edebe5] rounded-lg hover:bg-[#f7f4ed] cursor-pointer transition-colors">
                                            <input
                                                type="radio"
                                                name="mode"
                                                value="write"
                                                checked={newChatForm.mode === "write"}
                                                onChange={(e) =>
                                                    setNewChatForm({
                                                        ...newChatForm,
                                                        mode: e.target.value as "ask" | "write",
                                                    })
                                                }
                                                className="mt-1"
                                            />
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <div className="text-sm font-medium">
                                                        WRITE Mode
                                                    </div>
                                                    <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                                                        Drafting
                                                    </span>
                                                </div>
                                                <p className="text-xs text-[#7a7a7a]">
                                                    AI can directly edit and modify the selected
                                                    context content, adding facts, updating
                                                    research, or drafting new legal documents.
                                                </p>
                                            </div>
                                        </label>
                                    </div>
                                </div>

                                {/* Tags */}
                                <div>
                                    <h4 className="text-sm font-medium mb-3">Tags (Optional)</h4>
                                    <input
                                        type="text"
                                        value={newChatForm.tags.join(", ")}
                                        onChange={(e) => {
                                            const tags = e.target.value
                                                .split(",")
                                                .map((tag) => tag.trim())
                                                .filter((tag) => tag.length > 0)
                                            setNewChatForm({ ...newChatForm, tags })
                                        }}
                                        placeholder="e.g., research, contract, evidence (comma-separated)"
                                        className="penpot-input w-full"
                                    />
                                    <p className="text-xs text-[#7a7a7a] mt-1">
                                        Tags help organize and filter your chats. Press Enter or
                                        comma to add tags.
                                    </p>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center justify-end gap-4 pt-6 border-t border-[#edebe5] mt-6">
                                <button
                                    onClick={() => setIsNewChatModalOpen(false)}
                                    className="penpot-button-secondary"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createNewChat}
                                    disabled={
                                        !newChatForm.name.trim() ||
                                        newChatForm.selectedContexts.length === 0
                                    }
                                    className="penpot-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Create Chat
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

export function AIChatPanel(props: AIChatPanelProps) {
    return (
        <ErrorBoundary
            fallback={
                <div className="p-4">
                    <h3 className="penpot-heading-medium mb-2">AI Chat Error</h3>
                    <p className="text-red-600 text-sm">
                        Something went wrong with the AI chat panel.
                    </p>
                </div>
            }
        >
            <AIChatPanelContent {...props} />
        </ErrorBoundary>
    )
}
