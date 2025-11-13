import React from "react"
import { useParams } from "react-router"
import { JobUploadArea } from "~/components/ui/job-upload-area"
import { requireUser } from "~/services/auth.client"
import { useCaseData, useCases } from "~/services/state/state.client"
import type { Route } from "./+types/job-upload"

export function meta({}: Route.MetaArgs) {
    return [
        { title: "Job Upload" },
        { name: "description", content: "Job Market Agent - Job Upload" },
    ]
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
    const result = await requireUser(request)
    return {
        user: result.user,
        accessToken: result.accessToken,
    }
}

export default function CaseUpload({ loaderData }: Route.ComponentProps) {
    const params = useParams()
    const caseId = params.caseId // Get caseId from route params

    // Call hooks unconditionally at the top level
    const { uploads, addUploadedFiles, removeUploadedFile, caseData } = useCaseData(caseId || "")
    const { addCase } = useCases()
    const { accessToken } = loaderData

    // Debug logging for re-renders
    console.log(
        "[CaseUpload] Component re-rendered. caseId:",
        caseId,
        "uploads length:",
        uploads.length
    )
    console.log(
        "[CaseUpload] Current uploads:",
        uploads.map((f) => ({ id: f.id, name: f.name }))
    )

    // Create case if it doesn't exist and caseId is valid
    React.useEffect(() => {
        if (caseId && !caseData) {
            addCase({
                id: caseId,
                title: `Case ${caseId}`,
                editedDate: new Date().toISOString(),
                description: "",
                status: "active",
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
                uploads: [],
                caseMaterials: [],
            })
        }
    }, [caseData, caseId, addCase])

    // Early return if no caseId (shouldn't happen with proper routing)
    if (!caseId) {
        return (
            <div className="min-h-screen bg-white flex items-center justify-center">
                <div className="text-center">
                    <h2 className="text-xl font-medium text-red-600 mb-2">Invalid Case</h2>
                    <p className="text-gray-600">No case ID provided in the URL.</p>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-white">
            {/* Main content area with centered layout */}
            <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
                <div className="w-full max-w-4xl">
                    <JobUploadArea
                        key={`upload-area-${caseId}-${uploads.length}`} // Force re-render when uploads change
                        caseId={caseId}
                        uploads={uploads}
                        accessToken={accessToken || ""}
                        onFilesUploaded={(files) => {
                            // Add files to case state so they appear in the uploads prop
                            addUploadedFiles(files)
                            // Files successfully added to case state
                        }}
                        onFileRemoved={(fileId) => {
                            console.log("[CaseUpload] Attempting to remove file:", fileId)
                            console.log(
                                "[CaseUpload] Current uploads:",
                                uploads.map((f) => ({ id: f.id, name: f.name }))
                            )

                            // Check if file exists before attempting removal
                            const fileExists = uploads.some((f) => f.id === fileId)
                            console.log("[CaseUpload] File exists in uploads:", fileExists)

                            if (!fileExists) {
                                console.warn(
                                    "[CaseUpload] File not found in uploads, skipping removal:",
                                    fileId
                                )
                                return
                            }

                            // Remove file from case state
                            console.log("[CaseUpload] Removing file from state:", fileId)
                            removeUploadedFile(fileId)
                        }}
                    />
                </div>
            </div>
        </div>
    )
}
