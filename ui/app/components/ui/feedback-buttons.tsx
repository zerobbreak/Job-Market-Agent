import { Button } from "~/components/ui/button"

interface FeedbackButtonsProps {
    className?: string
}

export function FeedbackButtons({ className }: FeedbackButtonsProps) {
    const handleFeedback = (type: "yes" | "no") => {
        // In a real app, this would send feedback to analytics/service
        console.log(`User feedback: ${type === "yes" ? "Helpful" : "Not helpful"}`)
    }

    return (
        <div className={`flex items-center gap-4 ${className}`}>
            <span className="text-[#7a7a7a]">Was this page helpful?</span>
            <Button
                plain
                onClick={() => handleFeedback("yes")}
                className="transition-colors hover:bg-[#f9fafb]"
            >
                👍 Yes
            </Button>
            <Button
                plain
                onClick={() => handleFeedback("no")}
                className="transition-colors hover:bg-[#f9fafb]"
            >
                👎 No
            </Button>
        </div>
    )
}
