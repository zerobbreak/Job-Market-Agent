import CustomCaseMaterial from "~/components/case-materials/custom"
import DraftingCaseMaterial from "~/components/case-materials/drafting"
import EvidenceCaseMaterial from "~/components/case-materials/evidence"
import FactsCaseMaterial from "~/components/case-materials/facts"
import NotesCaseMaterial from "~/components/case-materials/notes"
import ResearchCaseMaterial from "~/components/case-materials/research"
import { useCaseData } from "~/services/state/state.client"

interface CaseMaterialViewerProps {
    caseId: string
    caseMaterialId: string
    onBack: () => void
}

export function CaseMaterialViewer({ caseId, caseMaterialId, onBack }: CaseMaterialViewerProps) {
    const { caseMaterials } = useCaseData(caseId)
    const caseMaterial = caseMaterials.find((cm) => cm.id === caseMaterialId)

    if (!caseMaterial) {
        return (
            <div className="flex items-center justify-center min-h-96">
                <div className="text-center">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg
                            className="w-8 h-8 text-red-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                            role="img"
                            aria-label="Error icon"
                        >
                            <title>Error</title>
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                            />
                        </svg>
                    </div>
                    <h3 className="penpot-heading-medium mb-2">Case Material Not Found</h3>
                    <p className="penpot-body-medium text-[#7a7a7a] mb-6">
                        The requested case material could not be found.
                    </p>
                    <button type="button" onClick={onBack} className="penpot-button-primary">
                        Back to Overview
                    </button>
                </div>
            </div>
        )
    }

    // Render the appropriate case material component based on type
    const renderCaseMaterial = () => {
        const commonProps = {
            params: { caseId, caseMaterialId },
            loaderData: {
                case: { id: caseId, title: "Current Case" }, // This would come from actual case data
                caseMaterial,
            },
            caseData: {
                id: caseId,
                title: "Current Case",
                editedDate: new Date().toISOString(),
            },
            caseMaterial,
            uploads: [],
        }

        switch (caseMaterial.type) {
            case "facts":
                return <FactsCaseMaterial {...commonProps} />
            case "evidence":
                return <EvidenceCaseMaterial {...commonProps} />
            case "research":
                return <ResearchCaseMaterial {...commonProps} />
            case "drafting":
                return <DraftingCaseMaterial {...commonProps} />
            case "notes":
                return <NotesCaseMaterial {...commonProps} />
            case "custom":
                return <CustomCaseMaterial {...commonProps} />
            default:
                return (
                    <div className="text-center py-12">
                        <h3 className="penpot-heading-medium mb-4">
                            Unsupported Case Material Type
                        </h3>
                        <p className="penpot-body-medium text-[#7a7a7a]">
                            The case material type "{caseMaterial.type}" is not yet supported.
                        </p>
                    </div>
                )
        }
    }

    return (
        <div className="relative">
            {/* Case Material Header */}
            <div className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                    <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            caseMaterial.type === "facts"
                                ? "bg-blue-100"
                                : caseMaterial.type === "evidence"
                                  ? "bg-green-100"
                                  : caseMaterial.type === "research"
                                    ? "bg-pink-100"
                                    : caseMaterial.type === "drafting"
                                      ? "bg-purple-100"
                                      : caseMaterial.type === "notes"
                                        ? "bg-yellow-100"
                                        : "bg-indigo-100"
                        }`}
                    >
                        {caseMaterial.type === "facts" && (
                            <svg
                                className="w-4 h-4 text-blue-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Facts icon"
                            >
                                <title>Facts</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                />
                            </svg>
                        )}
                        {caseMaterial.type === "evidence" && (
                            <svg
                                className="w-4 h-4 text-green-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Evidence icon"
                            >
                                <title>Evidence</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                />
                            </svg>
                        )}
                        {caseMaterial.type === "research" && (
                            <svg
                                className="w-4 h-4 text-pink-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Research icon"
                            >
                                <title>Research</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                                />
                            </svg>
                        )}
                        {caseMaterial.type === "drafting" && (
                            <svg
                                className="w-4 h-4 text-purple-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Drafting icon"
                            >
                                <title>Drafting</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                />
                            </svg>
                        )}
                        {caseMaterial.type === "notes" && (
                            <svg
                                className="w-4 h-4 text-yellow-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Notes icon"
                            >
                                <title>Notes</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                />
                            </svg>
                        )}
                        {caseMaterial.type === "custom" && (
                            <svg
                                className="w-4 h-4 text-indigo-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                role="img"
                                aria-label="Custom icon"
                            >
                                <title>Custom</title>
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth={2}
                                    d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                                />
                            </svg>
                        )}
                    </div>
                    <div>
                        <h2 className="penpot-heading-medium">{caseMaterial.title}</h2>
                        <p className="penpot-caption text-[#7a7a7a]">
                            {caseMaterial.type.charAt(0).toUpperCase() + caseMaterial.type.slice(1)}{" "}
                            Case Material
                        </p>
                    </div>
                </div>

                {/* Status Badge */}
                <div className="flex items-center gap-2">
                    <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${
                            caseMaterial.status === "completed"
                                ? "bg-green-100 text-green-800"
                                : caseMaterial.status === "processing"
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-gray-100 text-gray-800"
                        }`}
                    >
                        {caseMaterial.status || "Active"}
                    </span>
                    <span className="text-xs text-[#7a7a7a]">
                        Created {new Date(caseMaterial.createdAt).toLocaleDateString()}
                    </span>
                </div>
            </div>

            {/* Case Material Content */}
            {renderCaseMaterial()}
        </div>
    )
}
