import type { LLMResponse } from "@/types/api.types"
import type { UploadedFile } from "@/types/job.types"
import { localStore } from "./state/state.client"

const MOCK_MARKDOWN = `# Sample Document Export\n\nThis is a locally generated markdown export.\n\n- Generated: ${new Date().toLocaleString()}\n- Source: Job Market Agent mock workspace\n`

const MOCK_RESPONSES: LLMResponse[] = [
    {
        id: "llm-demo-001",
        query_text: "How should I tailor my resume for a senior product role?",
        query_mode: "facts",
        response_text:
            "Focus on quantifiable outcomes, cross-functional leadership, and strategic impact. Highlight 2-3 marquee launches with metrics.",
        provider: "mock",
        model: "claude-3.5-sonnet",
        quality_score: 0.92,
        processing_time_ms: 120,
        chunks_used: ["resume-best-practices", "senior-product-role"],
        citations: [],
        response_metadata: {
            tone: "friendly",
            structure: "bulleted",
        },
        created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        session: "job-demo-001",
    },
]

const FALLBACK_DOCUMENT: UploadedFile = {
    id: "mock-doc-001",
    name: "Job-Market-Agent-Demo.pdf",
    size: 86_400,
    type: "application/pdf",
    uploadedAt: new Date().toISOString(),
    status: "completed",
    url: "mock://documents/job-market-agent-demo.pdf",
}

export async function exportDocumentToMarkdown(): Promise<string> {
    return MOCK_MARKDOWN
}

export async function downloadDocumentAsMarkdown(
    _documentId: string,
    filename: string
): Promise<void> {
    const markdown = await exportDocumentToMarkdown()
    const blob = new Blob([markdown], { type: "text/markdown" })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = filename.endsWith(".md") ? filename : `${filename}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
}

export async function getLLMResponses(_accessToken?: string, sessionId?: string): Promise<LLMResponse[]> {
    if (sessionId) {
        return MOCK_RESPONSES.filter((response) => response.session === sessionId)
    }

    return [...MOCK_RESPONSES]
}

export async function getDocuments(_accessToken?: string, sessionId?: string): Promise<UploadedFile[]> {
    const cases = localStore.getCases()
    const uploads = cases.flatMap((caseItem) => caseItem.uploads ?? [])

    if (sessionId) {
        return uploads.length > 0
            ? uploads.filter((file) => file.id.includes(sessionId) || file.name.includes(sessionId))
            : [FALLBACK_DOCUMENT]
    }

    if (uploads.length === 0) {
        return [FALLBACK_DOCUMENT]
    }

    return uploads.map((file) => ({ ...file }))
}
