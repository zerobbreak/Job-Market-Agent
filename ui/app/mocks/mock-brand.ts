/**
 * Mock Brand Content
 *
 * Centralized brand messaging and content for the Job Market AI Analyzer application.
 * This allows for easy updates and consistency across the application.
 */

import type { BrandAssets, BrandContent } from "@/types/brand.types"

export const mockBrandContent: BrandContent = {
    appName: "Job Market Agent",
    tagline: "AI-Powered Job Application Assistant",
    description: "Streamline your job search with AI-powered CV optimization, ATS analysis, cover letter generation, and interview preparation across 20+ job platforms",
    welcomeMessage: "Welcome to Job Market Agent",
    copyright: "Job Market Agent. All rights reserved.",
    metaTitle: "Job Market Agent - AI-Powered Job Application Assistant",
    metaDescription:
        "Streamline your job search with AI-powered CV optimization, ATS analysis, cover letter generation, and interview preparation across 20+ job platforms",
}

export const mockBrandAssets: BrandAssets = {
    logo: "/placeholder-logo.svg",
    favicon: "/favicon.ico",
    ogImage: "/placeholder.svg",
}

/**
 * Get brand content for a specific context
 */
export function getBrandContent(_context?: string): BrandContent {
    // In the future, this could return different content based on context
    // For example, different messaging for different user types or regions
    return mockBrandContent
}

/**
 * Get brand assets
 */
export function getBrandAssets(): BrandAssets {
    return mockBrandAssets
}

/**
 * Get page-specific meta information
 */
export function getPageMeta(page: string): {
    title: string
    description: string
} {
    const baseTitle = mockBrandContent.metaTitle
    const baseDescription = mockBrandContent.metaDescription
    const appName = mockBrandContent.appName

    switch (page) {
        case "home":
            return {
                title: baseTitle,
                description: baseDescription,
            }
        case "jobs":
            return {
                title: `Job Applications - ${appName}`,
                description: "Discover jobs across 20+ platforms and manage your applications with AI-powered optimization",
            }
        case "learn":
            return {
                title: `Learn - ${appName}`,
                description: `Master ${appName} to accelerate your job search and optimize your applications`,
            }
        default:
            return {
                title: baseTitle,
                description: baseDescription,
            }
    }
}
