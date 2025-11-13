import { useEffect, useId, useState } from "react"
import {
    Form,
    redirect,
    useActionData,
    useNavigate,
    useParams,
    useSearchParams,
} from "react-router"
import { ErrorBoundary } from "~/components/ui/error-boundary"
import { requireUser } from "~/services/auth.client"
import { createJobMaterial } from "~/services/job.client"
import {
    extractErrorMessage,
    validateJobMaterialTitle,
    validateJobMaterialType,
} from "~/utils/validation"
import type { Route } from "./+types/new-job-material"

export function meta({}: Route.MetaArgs) {
    return [
        { title: "New Job Material" },
        {
            name: "description",
            content: "Job Market Agent - Create New Job Material",
        },
    ]
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
    const result = await requireUser(request)
    return { user: result.user }
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
    const _result = await requireUser(request)
    const formData = await request.formData()

    const title = formData.get("title") as string
    const type = formData.get("type") as string
    const description = formData.get("description") as string

    // Validation using utilities
    const titleValidation = validateCaseMaterialTitle(title)
    const typeValidation = validateCaseMaterialType(type)

    if (!titleValidation.isValid) {
        return { error: titleValidation.errors.join(", ") }
    }

    if (!typeValidation.isValid) {
        return { error: typeValidation.errors.join(", ") }
    }

    try {
        const result = await createJobMaterial({
            jobId: params.jobId,
            title,
            type: type as "ats-optimizer" | "cv-rewriter" | "cover-letter-specialist" | "interview-copilot" | "interview-prep-agent" | "notes" | "research",
            description: description || undefined,
        })

        return redirect(`/jobs/${params.jobId}/job-materials/${result.id}`)
    } catch (error) {
        console.error("Failed to create job material:", error)
        return {
            error: extractErrorMessage(error) || "Failed to create job material",
        }
    }
}

const jobMaterialTypes = [
    {
        id: "ats-optimizer",
        name: "ATS Optimizer",
        description: "Optimize CV for Applicant Tracking Systems",
        icon: "🎯"
    },
    {
        id: "cv-rewriter",
        name: "CV Rewriter",
        description: "Enhance and rewrite your CV content",
        icon: "✍️"
    },
    {
        id: "cover-letter-specialist",
        name: "Cover Letter Specialist",
        description: "Generate personalized cover letters",
        icon: "💼"
    },
    {
        id: "interview-copilot",
        name: "Interview Copilot",
        description: "Real-time interview assistance",
        icon: "🎙️"
    },
    {
        id: "interview-prep-agent",
        name: "Interview Prep Agent",
        description: "Comprehensive interview preparation",
        icon: "📚"
    },
    {
        id: "notes",
        name: "Notes",
        description: "General notes and organization",
        icon: "📝"
    },
    {
        id: "research",
        name: "Research",
        description: "Company and role research",
        icon: "🔍"
    }
]

export default function NewJobMaterial() {
    const navigate = useNavigate()
    const { jobId } = useParams()
    const [searchParams] = useSearchParams()
    const actionData = useActionData() as { error?: string } | undefined
    const [selectedType, setSelectedType] = useState<string>("")
    const titleId = useId()
    const descriptionId = useId()

    // Set initial type from URL parameter
    useEffect(() => {
        const typeParam = searchParams.get("type")
        if (typeParam && jobMaterialTypes.some((type) => type.id === typeParam)) {
            setSelectedType(typeParam)
        }
    }, [searchParams])

    return (
        <ErrorBoundary>
            <div className="penpot-container py-8">
                <div className="max-w-xl lg:max-w-2xl mx-auto">
                    {/* Header */}
                    <div className="mb-8">
                        <button
                            type="button"
                            onClick={() => navigate(`/jobs/${jobId}`)}
                            className="flex items-center gap-2 text-[#7a7a7a] hover:text-[#151515] transition-colors mb-4"
                        >
                            <svg
                                className="w-5 h-5"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Back"
                            >
                                <title>Back</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M15 19l-7-7 7-7"
                                />
                            </svg>
                            Back to Job
                        </button>
                        <h1 className="penpot-heading-large mb-2">Create New Job Material</h1>
                        <p className="penpot-body-large text-[#7a7a7a]">
                            Choose the type of job material you want to add to this job.
                        </p>
                    </div>

                    <Form method="post" className="space-y-6">
                        {/* Error Display */}
                        {actionData?.error && (
                            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                                <p className="penpot-body-medium text-red-600">
                                    {actionData.error}
                                </p>
                            </div>
                        )}

                        {/* Case Material Type Selection */}
                        <div>
                            <h2 className="penpot-heading-medium mb-4">Job Material Type</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {jobMaterialTypes.map((type) => (
                                    <label
                                        key={type.id}
                                        className={`penpot-card p-6 cursor-pointer transition-all hover:shadow-lg ${
                                            selectedType === type.id
                                                ? "ring-2 ring-[#4b92ff] bg-[#f7f4ed]"
                                                : "hover:bg-gray-50"
                                        }`}
                                    >
                                        <input
                                            type="radio"
                                            name="type"
                                            value={type.id}
                                            checked={selectedType === type.id}
                                            onChange={(e) => setSelectedType(e.target.value)}
                                            className="sr-only"
                                        />
                                        <div className="flex items-start gap-4">
                                            <div className="flex-shrink-0 w-12 h-12 bg-[#4b92ff] text-white rounded-lg flex items-center justify-center">
                                                {type.icon}
                                            </div>
                                            <div className="flex-1">
                                                <h3 className="penpot-body-medium font-semibold mb-1">
                                                    {type.name}
                                                </h3>
                                                <p className="penpot-caption text-[#7a7a7a]">
                                                    {type.description}
                                                </p>
                                            </div>
                                        </div>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Case Material Details */}
                        {selectedType && (
                            <div className="space-y-4">
                                <h2 className="penpot-heading-medium mb-4">
                                    Case Material Details
                                </h2>

                                <div>
                                    <label
                                        htmlFor={titleId}
                                        className="block penpot-body-medium font-medium mb-2"
                                    >
                                        Title
                                    </label>
                                    <input
                                        type="text"
                                        id={titleId}
                                        name="title"
                                        required
                                        className="penpot-input"
                                        placeholder={`Enter ${caseMaterialTypes.find((t) => t.id === selectedType)?.name.toLowerCase()} title...`}
                                    />
                                </div>

                                <div>
                                    <label
                                        htmlFor={descriptionId}
                                        className="block penpot-body-medium font-medium mb-2"
                                    >
                                        Description (Optional)
                                    </label>
                                    <textarea
                                        id={descriptionId}
                                        name="description"
                                        rows={3}
                                        className="penpot-input"
                                        placeholder="Add a description for this case material..."
                                    />
                                </div>
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex items-center gap-4 pt-6 border-t border-[#edebe5]">
                            <button
                                type="button"
                                onClick={() => navigate(`/jobs/${jobId}`)}
                                className="penpot-button-secondary"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={!selectedType}
                                className="penpot-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Create Case Material
                            </button>
                        </div>
                    </Form>
                </div>
            </div>
        </ErrorBoundary>
    )
}
