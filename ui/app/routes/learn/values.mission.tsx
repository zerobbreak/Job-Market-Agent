import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [{ title: "Mission" }]
}

export default function ValuesMission() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Mission</h1>

            <p>
                Democratizing access to AI-powered job search tools, helping job seekers of all backgrounds 
                compete effectively in the modern job market by leveraging enterprise-grade optimization 
                and automation without prohibitive costs.
            </p>

            <p>
                We believe everyone deserves equal access to the tools that maximize their career opportunities, 
                regardless of their current employment status or resources.
            </p>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
