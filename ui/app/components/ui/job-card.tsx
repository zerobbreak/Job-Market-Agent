import { TrashIcon } from "@heroicons/react/24/outline"
import type { Case } from "@/types/job.types"
import { Link } from "~/components/ui/link"

interface CaseCardProps extends Pick<Case, "id" | "title" | "editedDate"> {
    initials?: string
    href?: string
    className?: string
    onDelete?: (id: string) => void
}

export function CaseCard({
    id,
    title,
    editedDate,
    initials,
    href,
    className = "",
    onDelete,
}: CaseCardProps) {
    const displayInitial = initials || title.charAt(0).toUpperCase()
    const truncatedTitle = title.length > 100 ? `${title.slice(0, 100)}...` : title
    const CardContent = (
        <div
            className={`w-full max-w-sm bg-white border border-[#edebe5] rounded-lg shadow-[0px_2px_4px_0px_rgba(237,235,229,1)] p-4 group hover:shadow-md transition-shadow relative ${className}`}
        >
            {onDelete && (
                <button
                    type="button"
                    onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onDelete(id)
                    }}
                    className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-red-50 hover:text-red-600"
                    title="Delete job"
                >
                    <TrashIcon className="w-4 h-4" />
                </button>
            )}
            <div className="flex items-start gap-2">
                <div className="w-10 h-10 bg-[#4b92ff] rounded-full flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">{displayInitial}</span>
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="penpot-body-medium mb-1 group-hover:text-[#4b92ff] transition-colors">
                        {truncatedTitle}
                    </h3>
                    <p className="penpot-caption">{editedDate}</p>
                </div>
            </div>
        </div>
    )

    if (href) {
        return (
            <Link href={href} className="block">
                {CardContent}
            </Link>
        )
    }

    return CardContent
}
