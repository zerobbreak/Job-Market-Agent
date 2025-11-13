/**
 * Learning Module Types
 *
 * Type definitions for the learning and educational content system
 */

export interface LearningSection {
    id: string
    title: string
    description: string
    icon?: string
    pages: LearningPage[]
    order: number
}

export interface LearningPage {
    id: string
    title: string
    content: string
    section: string
    order: number
    lastModified: string
    tags: string[]
    difficulty: "beginner" | "intermediate" | "advanced"
    estimatedReadTime: number // in minutes
}

export interface LearningProgress {
    userId: string
    pageId: string
    completed: boolean
    lastAccessed: string
    timeSpent: number // in seconds
    bookmarked: boolean
}

export interface LearningSearchResult {
    page: LearningPage
    section: LearningSection
    relevanceScore: number
    matchedTerms: string[]
}

// Legacy types for backwards compatibility
export interface ContentItem {
    section: string
    page: string
    title: string
    content: string
}

export interface SearchResult extends ContentItem {
    score: number
    titleMatch: boolean
    contentMatch: boolean
}
