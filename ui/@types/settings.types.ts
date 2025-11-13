export interface UserProfileSettings {
    firstName: string
    lastName: string
    occupation: string
    firmName: string
}

export interface FileSettings {
    autoDeleteUploads: "never" | "1 day" | "7 days" | "30 days"
    maxStorageMB: number
    currentUsageMB: number
    fileTypeBreakdown: {
        pdf: number
        docx: number
        xlsx: number
        other: number
    }
}

export interface SecuritySettings {
    twoFactorEnabled: boolean
    sessionTimeout: "15 min" | "30 min" | "1 hour" | "4 hours" | "8 hours"
    passwordLastChanged?: string
}

export interface NotificationSettings {
    emailNotifications: boolean
    jobUpdates: boolean
    documentUploads: boolean
    systemAlerts: boolean
}

export interface DraftingSettings {
    citationStyle: "footnotes" | "endnotes" | "inline"
    toneVerbosity: "concise" | "detailed" | "comprehensive"
    autoSave: boolean
}

export interface BillingSettings {
    currentPlan: "FREE" | "PRO" | "ENTERPRISE"
    billingCycle: "monthly" | "yearly"
    nextBillingDate?: string
    paymentMethod?: {
        type: "visa" | "mastercard" | "amex"
        last4: string
    }
}

export interface KnowledgeSettings {
    defaultSearchEngine: "google" | "bing" | "duckduckgo"
    aiModelPreference: "gpt-4" | "gpt-3.5" | "claude"
    maxSearchResults: number
}

export interface AppSettings {
    profile: UserProfileSettings
    files: FileSettings
    security: SecuritySettings
    notifications: NotificationSettings
    drafting: DraftingSettings
    billing: BillingSettings
    knowledge: KnowledgeSettings
}
