/**
 * Brand and Marketing Content Types
 *
 * Type definitions for brand messaging, assets, and marketing content
 */

export interface BrandContent {
    appName: string
    tagline: string
    description: string
    welcomeMessage: string
    copyright: string
    metaTitle: string
    metaDescription: string
}

export interface BrandAssets {
    logo: string
    favicon: string
    ogImage: string
}

export interface ContactInfo {
    address: {
        street: string
        city: string
        state: string
        zipCode: string
        country: string
    }
    phone: string
    email: string
    emergencyEmail: string
    businessHours: {
        weekdays: string
        saturday: string
        sunday: string
    }
    socialMedia: {
        twitter?: string
        linkedin?: string
        github?: string
    }
}

export interface SupportInfo {
    generalSupport: string
    technicalSupport: string
    billingSupport: string
    emergencySupport: string
}
