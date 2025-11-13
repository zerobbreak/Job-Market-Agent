import { XMarkIcon } from "@heroicons/react/24/outline"
import { memo, useId } from "react"
import { useForm } from "~/hooks"
import { createJob } from "~/services/job.client"
import { extractErrorMessage, validateJobTitle } from "~/utils/validation"

interface CreateJobModalProps {
    isOpen: boolean
    onClose: () => void
    onCaseCreated: (jobId: string, jobTitle: string) => void
    accessToken?: string
}

export const CreateJobModal = memo(function CreateJobModal({
    isOpen,
    onClose,
    onCaseCreated,
    accessToken,
}: CreateJobModalProps) {
    const jobTitleId = useId()

    // Validation functions for useForm hook
    const validations = {
        title: (value: unknown) => {
            const validation = validateJobTitle(value as string)
            return {
                isValid: validation.isValid,
                errors: validation.errors,
            }
        },
    }

    const { getFieldProps, handleSubmit, reset, isSubmitting } = useForm({ title: "" }, validations)

    const handleCreateJob = async (formValues: { title: string }) => {
        try {
            const result = await createJob(
                {
                    title: formValues.title.trim(),
                },
                accessToken
            )

            // Check if result is successful
            if (result && "success" in result && !result.success) {
                throw new Error(result.error?.message || "Failed to create job")
            }

            // Notify parent component - result.data contains the job data when successful
            const jobData = result.data as { id: string; title: string }
            onCaseCreated(jobData.id, jobData.title)

            // Reset form and close modal
            reset({ title: "" })
            onClose()
        } catch (err) {
            throw new Error(extractErrorMessage(err) || "Failed to create job")
        }
    }

    const handleClose = () => {
        reset({ title: "" })
        onClose()
    }

    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
                aria-hidden="true"
                role="presentation"
                onClick={() => !isSubmitting && handleClose()}
            />

            {/* Modal */}
            <div className="flex min-h-full items-center justify-center p-4">
                <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-[#edebe5]">
                        <h2 className="penpot-heading-medium text-[#151515]">Create New Job</h2>
                        <button
                            type="button"
                            onClick={handleClose}
                            disabled={isSubmitting}
                            className="p-2 text-[#7a7a7a] hover:text-[#151515] hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <XMarkIcon className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Content */}
                    <form onSubmit={handleSubmit(handleCreateJob)} className="p-6">
                        <div className="space-y-4">
                            <div>
                                <label
                                    htmlFor={jobTitleId}
                                    className="block penpot-body-medium font-medium mb-2"
                                >
                                    Job Title
                                </label>
                                <input
                                    type="text"
                                    id={jobTitleId}
                                    value={getFieldProps("title").value as string}
                                    onChange={(e) =>
                                        getFieldProps("title").onChange(e.target.value)
                                    }
                                    onBlur={getFieldProps("title").onBlur}
                                    placeholder="Enter job title..."
                                    className="penpot-input w-full"
                                    disabled={isSubmitting}
                                    required
                                    maxLength={100}
                                />
                            </div>

                            {getFieldProps("title").error && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                    <p className="penpot-body-medium text-red-600">
                                        {getFieldProps("title").error}
                                    </p>
                                </div>
                            )}

                            <div className="text-sm text-[#7a7a7a]">
                                <p>
                                    You can add job materials (ATS Optimizer, CV Rewriter, Cover Letter Specialist, etc.)
                                    after creating the job.
                                </p>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-[#edebe5]">
                            <button
                                type="button"
                                onClick={handleClose}
                                disabled={isSubmitting}
                                className="penpot-button-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="penpot-button-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {isSubmitting ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        Creating...
                                    </>
                                ) : (
                                    "Create Job"
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    )
})
