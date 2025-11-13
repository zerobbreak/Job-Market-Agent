/**
 * Learn Service Module
 *
 * Handles all client-side logic related to learning resources and educational content
 * within the Junior Counsel application. Provides functions for fetching, managing,
 * and caching learning materials from the backend API or static sources.
 */

import type {
    LearningPage,
    LearningProgress,
    LearningSearchResult,
    LearningSection,
} from "@/types/learn.types"
import {
    mockBookmarkLearningPage,
    mockGetBookmarkedPages,
    mockGetLearningPage,
    mockGetLearningSections,
    mockGetUserLearningProgress,
    mockSearchLearningContent,
    mockUpdateLearningProgress,
} from "~/mocks/mock-learn"

export async function getLearningSections(): Promise<LearningSection[]> {
    return mockGetLearningSections()
}

export async function getLearningPage(pageId: string): Promise<LearningPage> {
    return mockGetLearningPage(pageId)
}

export async function searchLearningContent(
    query: string,
    filters?: {
        section?: string
        difficulty?: string
        tags?: string[]
    }
): Promise<LearningSearchResult[]> {
    return mockSearchLearningContent(query, filters)
}

export async function updateLearningProgress(
    pageId: string,
    progress: Partial<LearningProgress>,
    accessToken?: string
): Promise<LearningProgress> {
    const userId = accessToken || "mock-user"
    return mockUpdateLearningProgress(userId, pageId, progress)
}

export async function getUserLearningProgress(
    _accessToken?: string
): Promise<LearningProgress[]> {
    return mockGetUserLearningProgress("mock-user")
}

export async function getBookmarkedLearningPages(
    _accessToken?: string
): Promise<LearningPage[]> {
    return mockGetBookmarkedPages("mock-user")
}

export async function bookmarkLearningPage(pageId: string): Promise<void> {
    await mockBookmarkLearningPage("mock-user", pageId)
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Calculate reading progress percentage
 */
export function calculateReadingProgress(progress: LearningProgress, page: LearningPage): number {
    if (!progress.timeSpent || !page.estimatedReadTime) {
        return 0
    }

    const estimatedTimeSeconds = page.estimatedReadTime * 60
    return Math.min(100, Math.round((progress.timeSpent / estimatedTimeSeconds) * 100))
}

/**
 * Get difficulty color for UI
 */
export function getDifficultyColor(difficulty: LearningPage["difficulty"]): string {
    switch (difficulty) {
        case "beginner":
            return "text-green-600 bg-green-50"
        case "intermediate":
            return "text-yellow-600 bg-yellow-50"
        case "advanced":
            return "text-red-600 bg-red-50"
        default:
            return "text-gray-600 bg-gray-50"
    }
}

/**
 * Format estimated read time for display
 */
export function formatReadTime(minutes: number): string {
    if (minutes < 1) {
        return "< 1 min"
    }
    if (minutes < 60) {
        return `${minutes} min`
    }

    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60

    if (remainingMinutes === 0) {
        return `${hours}h`
    }

    return `${hours}h ${remainingMinutes}m`
}

/**
 * Generate search suggestions based on content
 */
export function generateSearchSuggestions(sections: LearningSection[]): string[] {
    const suggestions: string[] = []

    sections.forEach((section) => {
        suggestions.push(section.title)
        section.pages.forEach((page) => {
            suggestions.push(page.title)
            page.tags.forEach((tag) => {
                if (!suggestions.includes(tag)) {
                    suggestions.push(tag)
                }
            })
        })
    })

    return suggestions.slice(0, 10) // Limit to 10 suggestions
}
