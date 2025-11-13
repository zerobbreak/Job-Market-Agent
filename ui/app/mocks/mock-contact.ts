/**
 * Mock Contact Information
 *
 * Centralized contact information and business details for the Junior Counsel application.
 * This allows for easy updates and consistency across the application.
 */

import type { ContactInfo, SupportInfo } from "@/types/brand.types"

export const mockContactInfo: ContactInfo = {
    address: {
        street: "123 Legal Street, Suite 100",
        city: "Legal City",
        state: "LC",
        zipCode: "12345",
        country: "United States",
    },
    phone: "+1 (555) 123-4567",
    email: "support@juniorcounsel.com",
    emergencyEmail: "emergency@juniorcounsel.com",
    businessHours: {
        weekdays: "Monday - Friday: 9:00 AM - 6:00 PM",
        saturday: "Saturday: 10:00 AM - 4:00 PM",
        sunday: "Sunday: Closed",
    },
    socialMedia: {
        twitter: "@juniorcounsel",
        linkedin: "company/junior-counsel",
        github: "juniorcounsel",
    },
}

export const mockSupportInfo: SupportInfo = {
    generalSupport: "support@juniorcounsel.com",
    technicalSupport: "tech@juniorcounsel.com",
    billingSupport: "billing@juniorcounsel.com",
    emergencySupport: "emergency@juniorcounsel.com",
}

/**
 * Get formatted address string
 */
export function getFormattedAddress(): string {
    const { address } = mockContactInfo
    return `${address.street}\n${address.city}, ${address.state} ${address.zipCode}`
}

/**
 * Get contact information for a specific department
 */
export function getContactForDepartment(
    department: "general" | "technical" | "billing" | "emergency"
): string {
    switch (department) {
        case "general":
            return mockSupportInfo.generalSupport
        case "technical":
            return mockSupportInfo.technicalSupport
        case "billing":
            return mockSupportInfo.billingSupport
        case "emergency":
            return mockSupportInfo.emergencySupport
        default:
            return mockSupportInfo.generalSupport
    }
}

/**
 * Get business hours for display
 */
export function getBusinessHours(): string[] {
    const { businessHours } = mockContactInfo
    return [businessHours.weekdays, businessHours.saturday, businessHours.sunday]
}

/**
 * Get social media links
 */
export function getSocialMediaLinks(): Record<string, string> {
    const { socialMedia } = mockContactInfo
    const links: Record<string, string> = {}

    if (socialMedia.twitter) {
        links.twitter = `https://twitter.com/${socialMedia.twitter.replace("@", "")}`
    }
    if (socialMedia.linkedin) {
        links.linkedin = `https://linkedin.com/company/${socialMedia.linkedin}`
    }
    if (socialMedia.github) {
        links.github = `https://github.com/${socialMedia.github}`
    }

    return links
}
