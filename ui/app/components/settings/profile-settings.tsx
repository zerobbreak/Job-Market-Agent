import { useId } from "react"
import type { UserProfileSettings } from "../../../@types/settings.types"
import { Button } from "~/components/ui/button"
import { Field, Label } from "~/components/ui/fieldset"
import { Input } from "~/components/ui/input"
import { useForm } from "~/hooks"
import {
    validateProfileCompanyName,
    validateProfileName,
    validateProfileOccupation,
} from "~/utils/validation"

interface ProfileSettingsProps {
    settings: UserProfileSettings
    onSave: (updates: UserProfileSettings) => Promise<void>
    isLoading?: boolean
}

export function ProfileSettings({ settings, onSave, isLoading = false }: ProfileSettingsProps) {
    // Validation functions for useForm hook
    const validations = {
        firstName: (value: unknown) => validateProfileName(value as string),
        lastName: (value: unknown) => validateProfileName(value as string),
        occupation: (value: unknown) => validateProfileOccupation(value as string),
        companyName: (value: unknown) => validateProfileCompanyName(value as string),
    }

    const { getFieldProps, handleSubmit, isDirty, reset } = useForm(
        settings as unknown as Record<string, unknown>,
        validations
    )

    const handleSave = async (formValues: Record<string, unknown>) => {
        try {
            await onSave(formValues as unknown as UserProfileSettings)
            reset(formValues) // Reset form with new values to clear dirty state
        } catch (_error) {
            // Error is handled by parent component
        }
    }

    const handleCancel = () => {
        reset(settings as unknown as Record<string, unknown>)
    }

    const firstNameId = useId()
    const lastNameId = useId()
    const occupationId = useId()
    const companyNameId = useId()

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold text-[#151515] mb-1">Profile Information</h3>
                <p className="text-sm text-[#7a7a7a]">
                    Update your personal and professional information
                </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <Field>
                    <Label htmlFor={firstNameId} className="text-sm font-medium text-[#151515]">
                        First name *
                    </Label>
                    <Input
                        id={firstNameId}
                        type="text"
                        value={getFieldProps("firstName").value as string}
                        onChange={(e) => getFieldProps("firstName").onChange(e.target.value)}
                        onBlur={getFieldProps("firstName").onBlur}
                        className={
                            getFieldProps("firstName").error
                                ? "border-red-500 focus:border-red-500"
                                : ""
                        }
                        disabled={isLoading}
                        required
                    />
                    {getFieldProps("firstName").error && (
                        <p className="text-sm text-red-600 mt-1">
                            {getFieldProps("firstName").error}
                        </p>
                    )}
                </Field>

                <Field>
                    <Label htmlFor={lastNameId} className="text-sm font-medium text-[#151515]">
                        Last name *
                    </Label>
                    <Input
                        id={lastNameId}
                        type="text"
                        value={getFieldProps("lastName").value as string}
                        onChange={(e) => getFieldProps("lastName").onChange(e.target.value)}
                        onBlur={getFieldProps("lastName").onBlur}
                        className={
                            getFieldProps("lastName").error
                                ? "border-red-500 focus:border-red-500"
                                : ""
                        }
                        disabled={isLoading}
                        required
                    />
                    {getFieldProps("lastName").error && (
                        <p className="text-sm text-red-600 mt-1">
                            {getFieldProps("lastName").error}
                        </p>
                    )}
                </Field>
            </div>

            <Field>
                <Label htmlFor={occupationId} className="text-sm font-medium text-[#151515]">
                    Target Role / Occupation
                </Label>
                <Input
                    id={occupationId}
                    type="text"
                    value={getFieldProps("occupation").value as string}
                    onChange={(e) => getFieldProps("occupation").onChange(e.target.value)}
                    onBlur={getFieldProps("occupation").onBlur}
                    placeholder="e.g. Senior Software Engineer, Product Manager"
                    className={
                        getFieldProps("occupation").error
                            ? "border-red-500 focus:border-red-500"
                            : ""
                    }
                    disabled={isLoading}
                />
                {getFieldProps("occupation").error && (
                    <p className="text-sm text-red-600 mt-1">{getFieldProps("occupation").error}</p>
                )}
            </Field>

            <Field>
                <Label htmlFor={companyNameId} className="text-sm font-medium text-[#151515]">
                    Current / Most Recent Company
                </Label>
                <Input
                    id={companyNameId}
                    type="text"
                    value={getFieldProps("companyName").value as string}
                    onChange={(e) => getFieldProps("companyName").onChange(e.target.value)}
                    onBlur={getFieldProps("companyName").onBlur}
                    placeholder="Your current or most recent employer"
                    className={
                        getFieldProps("companyName").error ? "border-red-500 focus:border-red-500" : ""
                    }
                    disabled={isLoading}
                />
                {getFieldProps("companyName").error && (
                    <p className="text-sm text-red-600 mt-1">{getFieldProps("companyName").error}</p>
                )}
            </Field>

            {isDirty && (
                <div className="flex justify-end gap-3 pt-4 border-t border-[#edebe5]">
                    <Button type="button" color="white" onClick={handleCancel} disabled={isLoading}>
                        Cancel
                    </Button>
                    <Button type="button" onClick={handleSubmit(handleSave)} disabled={isLoading}>
                        {isLoading ? "Saving..." : "Save Changes"}
                    </Button>
                </div>
            )}
        </div>
    )
}
