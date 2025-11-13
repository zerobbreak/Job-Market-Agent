export interface ConversationMessage {
    role: "user" | "assistant"
    content: string
    timestamp: string
    metadata?: Record<string, unknown>
}

export interface Citation {
    id: string
    citation_text: string
    citation_type: "citation" | "statute_reference" | string
    reference_number: string
    page_number: number
    linked_documents: string[]
    created_at: string
    document: string
    chunk: string
}

export interface LLMResponse {
    id: string
    query_text: string
    query_mode: string
    response_text: string
    provider: string
    model: string
    quality_score: number
    processing_time_ms: number
    chunks_used: string[]
    citations: Citation[]
    response_metadata: Record<string, unknown>
    created_at: string
    session?: string
}

export interface ChatSession {
    id: string
    topic: string
    created_at: string
    updated_at: string
    metadata?: {
        description?: string
        tags?: string[]
    }
    // New fields from enhanced backend
    job?: string // Job ID
    user?: string
    conversation_context?: ConversationMessage[]
    context_summary?: string
    documents_count?: number
    queries_count?: number
    responses_count?: number
    recent_responses?: LLMResponse[]
    last_activity_at?: string
}

export interface CreateChatSessionOptions {
    topic: string
    description?: string
    tags?: string[]
    accessToken: string
    job_id?: string // NEW: Link session to a job
}

export interface ChatSessionResult {
    id: string
    topic: string
    metadata: {
        description?: string
        tags: string[]
    }
}

export interface GenerateAnswerOptions {
    query: string
    mode: "law" | "facts"
    sessionId: string
    accessToken: string
    limit?: number
    similarityThreshold?: number
    alpha?: number
    metadataFilters?: Record<string, unknown>
    chunkMode?: "context" | string
}

export interface GenerateAnswerResponse {
    query: string
    mode: "law" | "facts"
    answer: {
        text: string
        citations: Citation[]
        provider: string
        model: string
        quality_score: number
        metadata: {
            mode: string
            chunks_used: number
        }
    }
    session: {
        id: string
        topic: string
    }
    processing_time_ms: number
}

export interface ConversationHistoryResponse {
    session: ChatSession
    conversation_context: ConversationMessage[]
    context_summary: string
    responses: LLMResponse[]
}
