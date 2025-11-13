export interface FileAttachment {
    id: string
    name: string
    size: number
    type: string
    url?: string
}

export interface Message {
    id: number
    type: "ai" | "user"
    content: string
    timestamp: string
    status?: "sending" | "error" | "delivered" | "read"
    attachments?: FileAttachment[]
    reactions?: Array<{
        emoji: string
        count: number
        users: string[]
    }>
    metadata?: {
        sources?: string[]
        citations?: Citation[]
        quality_score?: number
        provider?: string
        model?: string
        chunks_used?: number
        processing_time_ms?: number
        mode?: string
        confidence?: number
        processingTime?: number
        tokens?: number
    }
}

export interface Citation {
    id: string
    citation_text: string
    citation_type: string
    reference_number: string
    page_number: number
    document: string
    chunk: string
}

export interface Chat {
    id: string
    name: string
    mode: "ask" | "write"
    contexts: string[]
    jobfiles: string[]
    messages: Message[]
    isActive: boolean
    createdAt: string
    lastActivity: string
    tags?: string[]
    settings?: {
        autoSave?: boolean
        maxTokens?: number
        temperature?: number
    }
}

// Simple message interface for basic chat functionality
export interface SimpleMessage {
    id: string
    content: string
    sender: "user" | "ai"
    timestamp: Date
}

// Re-export Citation from api.types for convenience
export type { Citation as ApiCitation } from "./api.types"

export interface Chat {
    id: string
    name: string
    mode: "ask" | "write"
    contexts: string[]
    jobfiles: string[]
    messages: Message[]
    isActive: boolean
    createdAt: string
    lastActivity: string
    tags?: string[]
    settings?: {
        autoSave?: boolean
        maxTokens?: number
        temperature?: number
    }
}

export interface AIChatPanelProps {
    isOpen: boolean
    onToggle: () => void
    jobId?: string
    availableContexts?: string[]
    availableJobfiles?: string[]
    accessToken?: string
}
