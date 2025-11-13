import type { AuthenticatedUser } from "@/types/auth.types"
import type { AppSettings, UserProfileSettings } from "@/types/settings.types"

const SETTINGS_STORAGE_KEY = "job-market-agent-settings"

let cachedSettings: AppSettings | null = null

function loadFromStorage(): AppSettings | null {
    if (typeof window === "undefined") {
        return cachedSettings
    }

    try {
        const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY)
        if (!raw) return null
        return JSON.parse(raw) as AppSettings
    } catch (error) {
        console.warn("[Settings] Failed to parse stored settings, resetting", error)
        window.localStorage.removeItem(SETTINGS_STORAGE_KEY)
        return null
    }
}

function persistToStorage(settings: AppSettings): void {
    cachedSettings = settings

    if (typeof window === "undefined") {
        return
    }

    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings))
}

export async function getUserSettings(_accessToken?: string): Promise<AppSettings> {
    const current = loadFromStorage() || cachedSettings

    if (current) {
        return current
    }

    const defaults = getDefaultSettings()
    persistToStorage(defaults)
    return defaults
}

export async function updateUserSettings(
    updates: Partial<AppSettings>,
    _accessToken?: string
): Promise<AppSettings> {
    const existing = await getUserSettings()
    const merged: AppSettings = {
        ...existing,
        ...updates,
        profile: {
            ...existing.profile,
            ...(updates.profile ?? {}),
        },
    }

    persistToStorage(merged)
    return merged
}

export async function updateUserProfile(
    profile: UserProfileSettings,
    accessToken?: string
): Promise<UserProfileSettings> {
    const settings = await updateUserSettings({ profile }, accessToken)
    return settings.profile
}

export function getDefaultSettings(): AppSettings {
    return {
        profile: {
            firstName: "",
            lastName: "",
            occupation: "",
            firmName: "",
        },
        files: {
            autoDeleteUploads: "never",
            maxStorageMB: 100,
            currentUsageMB: 12,
            fileTypeBreakdown: {
                pdf: 5,
                docx: 4,
                xlsx: 1,
                other: 2,
            },
        },
        security: {
            twoFactorEnabled: false,
            sessionTimeout: "30 min",
        },
        notifications: {
            emailNotifications: true,
            caseUpdates: true,
            documentUploads: true,
            systemAlerts: true,
        },
        drafting: {
            citationStyle: "footnotes",
            toneVerbosity: "concise",
            autoSave: true,
        },
        billing: {
            currentPlan: "FREE",
            billingCycle: "monthly",
        },
        knowledge: {
            defaultSearchEngine: "google",
            aiModelPreference: "claude-sonnet",
            maxSearchResults: 10,
        },
    }
}

export function populateSettingsWithUser(
    settings: AppSettings,
    user: AuthenticatedUser
): AppSettings {
    return {
        ...settings,
        profile: {
            ...settings.profile,
            firstName: user.first_name || settings.profile.firstName,
            lastName: user.last_name || settings.profile.lastName,
        },
    }
}
