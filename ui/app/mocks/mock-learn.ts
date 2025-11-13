import type {
    LearningPage,
    LearningProgress,
    LearningSearchResult,
    LearningSection,
} from "@/types/learn.types"

// In-memory mock store for learn data
const mockSections: LearningSection[] = [
    {
        id: "using",
        title: "Using Junior Counsel",
        description: "Learn how to use the app effectively",
        icon: "book-open",
        order: 1,
        pages: [
            {
                id: "using.introduction",
                title: "Introduction",
                content: "Welcome to Junior Counsel. This guide will help you get started...",
                section: "using",
                order: 1,
                lastModified: new Date().toISOString(),
                tags: ["getting-started", "overview"],
                difficulty: "beginner",
                estimatedReadTime: 5,
            },
            {
                id: "using.mode-overview",
                title: "Mode Overview",
                content: "Understand the different modes and workflows available...",
                section: "using",
                order: 2,
                lastModified: new Date().toISOString(),
                tags: ["modes", "workflow"],
                difficulty: "beginner",
                estimatedReadTime: 8,
            },
        ],
    },
    {
        id: "values",
        title: "Our Values",
        description: "Principles guiding Junior Counsel",
        icon: "scale",
        order: 2,
        pages: [
            {
                id: "values.mission",
                title: "Mission",
                content: "Our mission is to augment legal professionals...",
                section: "values",
                order: 1,
                lastModified: new Date().toISOString(),
                tags: ["mission", "ethics"],
                difficulty: "beginner",
                estimatedReadTime: 4,
            },
            {
                id: "values.technology",
                title: "Technology",
                content: "We use responsible AI and secure engineering practices...",
                section: "values",
                order: 2,
                lastModified: new Date().toISOString(),
                tags: ["ai", "security"],
                difficulty: "intermediate",
                estimatedReadTime: 6,
            },
        ],
    },
]

const progressByUser: Map<string, LearningProgress[]> = new Map()
const bookmarksByUser: Map<string, Set<string>> = new Map()

function delay(ms = 250) {
    return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function mockGetLearningSections(): Promise<LearningSection[]> {
    await delay()
    return JSON.parse(JSON.stringify(mockSections))
}

export async function mockGetLearningPage(pageId: string): Promise<LearningPage> {
    await delay()
    const page = mockSections.flatMap((s) => s.pages).find((p) => p.id === pageId)
    if (!page) {
        throw new Error("Learning page not found")
    }
    return JSON.parse(JSON.stringify(page))
}

export async function mockSearchLearningContent(
    query: string,
    filters?: { section?: string; difficulty?: string; tags?: string[] }
): Promise<LearningSearchResult[]> {
    await delay()
    const q = query.toLowerCase()
    const results: LearningSearchResult[] = []
    for (const section of mockSections) {
        for (const page of section.pages) {
            const matchesQuery =
                !q ||
                page.title.toLowerCase().includes(q) ||
                page.content.toLowerCase().includes(q) ||
                page.tags.some((t) => t.toLowerCase().includes(q))

            const matchesFilters =
                (!filters?.section || page.section === filters.section) &&
                (!filters?.difficulty || page.difficulty === filters.difficulty) &&
                (!filters?.tags || filters.tags.every((t) => page.tags.includes(t)))

            if (matchesQuery && matchesFilters) {
                const relevanceScore =
                    (page.title.toLowerCase().includes(q) ? 3 : 0) +
                    (page.content.toLowerCase().includes(q) ? 2 : 0) +
                    page.tags.filter((t) => t.toLowerCase().includes(q)).length
                const matchedTerms = [q].filter(Boolean)
                results.push({ page, section, relevanceScore, matchedTerms })
            }
        }
    }
    return results.sort((a, b) => b.relevanceScore - a.relevanceScore)
}

export async function mockUpdateLearningProgress(
    userId: string,
    pageId: string,
    updates: Partial<LearningProgress>
): Promise<LearningProgress> {
    await delay()
    const existing = progressByUser.get(userId) || []
    let record = existing.find((p) => p.pageId === pageId)
    if (!record) {
        record = {
            userId,
            pageId,
            completed: false,
            lastAccessed: new Date().toISOString(),
            timeSpent: 0,
            bookmarked: false,
        }
        existing.push(record)
    }
    Object.assign(record, updates, { lastAccessed: new Date().toISOString() })
    progressByUser.set(userId, existing)
    return JSON.parse(JSON.stringify(record))
}

export async function mockGetUserLearningProgress(userId: string): Promise<LearningProgress[]> {
    await delay()
    return JSON.parse(JSON.stringify(progressByUser.get(userId) || []))
}

export async function mockBookmarkLearningPage(
    userId: string,
    pageId: string,
    bookmarked: boolean
): Promise<void> {
    await delay()
    const set = bookmarksByUser.get(userId) || new Set<string>()
    if (bookmarked) set.add(pageId)
    else set.delete(pageId)
    bookmarksByUser.set(userId, set)
}

export async function mockGetBookmarkedPages(userId: string): Promise<LearningPage[]> {
    await delay()
    const ids = bookmarksByUser.get(userId) || new Set<string>()
    const pages = mockSections.flatMap((s) => s.pages).filter((p) => ids.has(p.id))
    return JSON.parse(JSON.stringify(pages))
}
