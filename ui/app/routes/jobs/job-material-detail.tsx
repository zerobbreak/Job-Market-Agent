import { ATSOptimizer } from "~/components/job-materials"
import { CoverLetterSpecialist } from "~/components/job-materials"
import { InterviewPrepAgent } from "~/components/job-materials"
import { CVRewriter } from "~/components/job-materials"
import { InterviewCopilot } from "~/components/job-materials"
import { Notes } from "~/components/job-materials"
import { requireUser } from "~/services/auth.client"
import { useCaseData } from "~/services/state/state.client"
import type { Route } from "./+types/job-material-detail"

export function meta({ params }: Route.MetaArgs) {
    return [
        { title: `Job Material ${params.jobMaterialId}` },
        { name: "description", content: "Job Market Agent - Job Material Detail" },
    ]
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
    await requireUser(request)
    return {}
}

export default function JobMaterialDetail({ params }: Route.ComponentProps) {
    const { caseData, caseMaterials } = useCaseData(params.caseId)
    const jobMaterial = caseMaterials.find((c) => c.id === params.jobMaterialId)

    // Show loading state if data is not available yet
    if (!caseData || !jobMaterial) {
        return (
            <div className="flex items-center justify-center min-h-96">
                <div className="text-center">
                    <div className="w-8 h-8 border-4 border-[#4b92ff] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="penpot-body-medium text-[#7a7a7a]">Loading job material...</p>
                </div>
            </div>
        )
    }

    // Render the appropriate case material component based on type
    const renderJobMaterial = () => {
        const uploads = caseData?.uploads || []
        const jobMaterialProps = {
            loaderData: { jobMaterial },
            params: { caseId: params.caseId, caseMaterialId: params.caseMaterialId },
            caseData,
            jobMaterial,
            uploads,
        }

        switch (jobMaterial.type) {
            case "cv-rewriter":
                return <CVRewriter {...jobMaterialProps} />
            case "interview-prep-agent":
                return <InterviewPrepAgent {...jobMaterialProps} />
            case "research":
                return <div>Research component coming soon</div>
            case "cover-letter-specialist":
                return <CoverLetterSpecialist {...jobMaterialProps} />
            case "notes":
                return <Notes {...jobMaterialProps} />
            case "ats-optimizer":
                return <ATSOptimizer {...jobMaterialProps} />
            case "interview-copilot":
                return <InterviewCopilot {...jobMaterialProps} />
            default:
                return (
                    <div className="penpot-card p-6 text-center">
                        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg
                                className="w-8 h-8 text-gray-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Warning"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                                />
                            </svg>
                        </div>
                        <h3 className="penpot-heading-medium mb-2">Unknown Case Material Type</h3>
                        <p className="penpot-body-large text-[#7a7a7a] mb-4">
                            The case material type "{caseMaterial.type}" is not supported yet.
                        </p>
                        <button
                            type="button"
                            onClick={() => window.history.back()}
                            className="penpot-button-primary"
                        >
                            Go Back
                        </button>
                    </div>
                )
        }
    }

    return renderJobMaterial()
}
