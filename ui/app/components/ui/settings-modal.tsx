import { useCallback, useEffect, useState } from "react"
import type { AuthenticatedUser } from "@/types/auth.types"
import type { AppSettings } from "@/types/settings.types"
import { FileSettingsComponent } from "~/components/settings/file-settings"
import { ProfileSettings } from "~/components/settings/profile-settings"
import { Dialog } from "~/components/ui/dialog"
import {
    getUserSettings,
    populateSettingsWithUser,
    updateUserSettings,
} from "~/services/settings.client"
import { withErrorHandling } from "~/utils/error-handling"

interface SettingsModalProps {
    isOpen: boolean
    onClose: () => void
    user: AuthenticatedUser
    accessToken?: string
}

const SettingsModal = ({ isOpen, onClose, user, accessToken }: SettingsModalProps) => {
    const [activeSection, setActiveSection] = useState("account")
    const [settings, setSettings] = useState<AppSettings | null>(null)

    // Available menu sections
    const menuItems = [
        { id: "account", label: "Account" },
        { id: "files", label: "Files & data" },
        { id: "notifications", label: "Notifications" },
        { id: "security", label: "Security" },
        { id: "drafting", label: "Document drafting" },
        { id: "billing", label: "Billing" },
    ]

    // Manual state management for loading settings
    const [loadedSettings, setLoadedSettings] = useState<AppSettings | null>(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<Error | null>(null)

    const loadSettings = useCallback(async () => {
        setIsLoading(true)
        setError(null)

        const result = await withErrorHandling(async () => {
            const userSettings = await getUserSettings(accessToken)
            return populateSettingsWithUser(userSettings, user)
        }, "SettingsModal.loadSettings")

        if (result.success && result.data) {
            setLoadedSettings(result.data)
        } else {
            setError(new Error(result.error?.message || "Failed to load settings"))
        }

        setIsLoading(false)
    }, [accessToken, user])

    // Update local settings when loadedSettings changes
    useEffect(() => {
        if (loadedSettings) {
            setSettings(loadedSettings)
        }
    }, [loadedSettings])

    // Load settings when modal opens
    useEffect(() => {
        if (isOpen && !settings && !isLoading) {
            loadSettings()
        }
    }, [isOpen, settings, isLoading, loadSettings])

    // Manual state management for saving settings
    const [_isSaving, setIsSaving] = useState(false)

    const handleSaveSettings = useCallback(
        async (updates: Partial<AppSettings>) => {
            if (!settings) return

            setIsSaving(true)

            const result = await withErrorHandling(
                () => updateUserSettings(updates, accessToken),
                "SettingsModal.handleSaveSettings"
            )

            if (result.success && result.data) {
                setSettings(result.data)
            } else {
                console.error("Failed to save settings:", result.error?.message)
            }

            setIsSaving(false)
        },
        [settings, accessToken]
    )

    const renderContent = () => {
        if (!settings) {
            return (
                <div className="flex items-center justify-center p-12">
                    <div className="text-center">
                        <div className="w-8 h-8 border-2 border-[#4b92ff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                        <p className="text-sm text-[#7a7a7a]">Loading settings...</p>
                    </div>
                </div>
            )
        }

        switch (activeSection) {
            case "account":
                return (
                    <ProfileSettings
                        settings={settings.profile}
                        onSave={(profileUpdates) => handleSaveSettings({ profile: profileUpdates })}
                        isLoading={isLoading}
                    />
                )

            case "files":
                return (
                    <FileSettingsComponent
                        settings={settings.files}
                        onSave={(fileUpdates) =>
                            handleSaveSettings({
                                files: { ...settings.files, ...fileUpdates },
                            })
                        }
                        isLoading={isLoading}
                    />
                )

            default:
                return (
                    <div className="text-center p-12">
                        <h3 className="text-lg font-semibold text-[#151515] mb-2">
                            {menuItems.find((item) => item.id === activeSection)?.label}
                        </h3>
                        <p className="text-sm text-[#7a7a7a]">
                            This section is coming soon. Stay tuned for updates!
                        </p>
                    </div>
                )
        }
    }

    return (
        <Dialog open={isOpen} onClose={onClose} size="4xl">
            <div className="flex h-full max-h-[90vh]">
                {/* Sidebar Navigation */}
                <div className="w-64 border-r border-[#edebe5] bg-[#fcfbf8] p-6">
                    <div className="flex items-center justify-between mb-8">
                        <h2 className="text-xl font-semibold text-[#151515]">Settings</h2>
                    </div>

                    <nav className="space-y-2">
                        {menuItems.map((item) => (
                            <button
                                type="button"
                                key={item.id}
                                onClick={() => setActiveSection(item.id)}
                                className={`w-full px-4 py-3 rounded-lg text-left transition-colors ${
                                    activeSection === item.id
                                        ? "bg-[#4b92ff] text-white"
                                        : "text-[#151515] hover:bg-[#edebe5]"
                                }`}
                            >
                                <span className="font-medium">{item.label}</span>
                            </button>
                        ))}
                    </nav>

                    {error && (
                        <div className="mt-6 p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-sm text-red-800">{error.message}</p>
                        </div>
                    )}
                </div>

                {/* Main Content */}
                <div className="flex-1 overflow-y-auto">
                    <div className="p-8">{renderContent()}</div>
                </div>
            </div>
        </Dialog>
    )
}

export default SettingsModal
