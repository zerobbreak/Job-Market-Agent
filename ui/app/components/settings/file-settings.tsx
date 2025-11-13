import { useState } from "react"
import type { FileSettings } from "../../../@types/settings.types"
import { Button } from "~/components/ui/button"
import { Field, Label } from "~/components/ui/fieldset"
import { Select } from "~/components/ui/select"

interface FileSettingsProps {
    settings: FileSettings
    onSave: (updates: Partial<FileSettings>) => Promise<void>
    isLoading?: boolean
}

export function FileSettingsComponent({ settings, onSave, isLoading = false }: FileSettingsProps) {
    const [autoDelete, setAutoDelete] = useState<FileSettings["autoDeleteUploads"]>(
        settings.autoDeleteUploads
    )
    const [isDirty, setIsDirty] = useState(false)

    const autoDeleteOptions = [
        { value: "never", label: "Never" },
        { value: "1 day", label: "After 1 day" },
        { value: "7 days", label: "After 7 days" },
        { value: "30 days", label: "After 30 days" },
    ] as const

    const handleAutoDeleteChange = (value: FileSettings["autoDeleteUploads"]) => {
        setAutoDelete(value)
        setIsDirty(true)
    }

    const handleSave = async () => {
        try {
            await onSave({ autoDeleteUploads: autoDelete })
            setIsDirty(false)
        } catch (_error) {
            // Error handled by parent
        }
    }

    const handleCancel = () => {
        setAutoDelete(settings.autoDeleteUploads)
        setIsDirty(false)
    }

    const usagePercentage = (settings.currentUsageMB / settings.maxStorageMB) * 100
    const isNearLimit = usagePercentage > 80
    const isOverLimit = usagePercentage > 100

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-[#151515] mb-1">Files & data</h3>
                <p className="text-sm text-[#7a7a7a]">
                    Manage your file storage and upload preferences
                </p>
            </div>

            <Field>
                <Label className="text-sm font-medium text-[#151515]">
                    Auto-delete uploads after
                </Label>
                <Select
                    value={autoDelete}
                    onChange={(e) =>
                        handleAutoDeleteChange(e.target.value as FileSettings["autoDeleteUploads"])
                    }
                    disabled={isLoading}
                >
                    {autoDeleteOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </Select>
                <p className="text-xs text-[#7a7a7a] mt-1">
                    Automatically delete uploaded files after the selected period to save storage
                    space
                </p>
            </Field>

            {/* Storage Usage */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h4 className="text-sm font-medium text-[#151515]">Storage Usage</h4>
                        <p className="text-xs text-[#7a7a7a]">
                            {settings.currentUsageMB}MB of {settings.maxStorageMB}MB used
                        </p>
                    </div>
                    {isNearLimit && (
                        <Button type="button" color="blue" disabled={isLoading}>
                            Upgrade Plan
                        </Button>
                    )}
                </div>

                <div className="space-y-2">
                    <div className="w-full h-3 bg-[#edebe5] rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-300 ${
                                isOverLimit
                                    ? "bg-red-500"
                                    : isNearLimit
                                      ? "bg-orange-500"
                                      : "bg-[#4b92ff]"
                            }`}
                            style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                        />
                    </div>

                    <div className="flex gap-4 text-xs">
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-[#4b92ff] rounded-sm" />
                            <span className="text-[#7a7a7a]">
                                PDF ({settings.fileTypeBreakdown.pdf}MB)
                            </span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-[#7a7a7a] rounded-sm" />
                            <span className="text-[#7a7a7a]">
                                Docx ({settings.fileTypeBreakdown.docx}MB)
                            </span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-orange-500 rounded-sm" />
                            <span className="text-[#7a7a7a]">
                                Xlsx ({settings.fileTypeBreakdown.xlsx}MB)
                            </span>
                        </div>
                        <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-green-500 rounded-sm" />
                            <span className="text-[#7a7a7a]">
                                Other ({settings.fileTypeBreakdown.other}MB)
                            </span>
                        </div>
                    </div>
                </div>

                {isOverLimit && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">
                            You have exceeded your storage limit. Please delete some files or
                            upgrade your plan.
                        </p>
                    </div>
                )}
            </div>

            {isDirty && (
                <div className="flex justify-end gap-3 pt-4 border-t border-[#edebe5]">
                    <Button type="button" color="white" onClick={handleCancel} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button type="button" onClick={handleSave} disabled={isLoading}>
                        {isLoading ? "Saving..." : "Save Changes"}
                    </Button>
                </div>
            )}
        </div>
    )
}
