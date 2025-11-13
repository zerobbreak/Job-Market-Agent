import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [{ title: "General Best Practices" }]
}

export default function UsingGeneralBestPractices() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>General Best Practices</h1>

            <p>
                While Job Market Agent provides powerful AI-driven optimization, your success 
                ultimately depends on how you use these tools. Treat AI-generated content as 
                a starting point that requires your personal touch, verification, and strategic thinking.
            </p>

            <h2>Do's</h2>
            <ul>
                <li>Personalize all AI-generated content to reflect your authentic voice and experiences</li>
                <li>Use specific job descriptions and requirements when generating materials</li>
                <li>Review and verify all company research and job details before applications</li>
                <li>Keep your CV and profile information up-to-date for better optimization</li>
                <li>Test different versions of optimized materials to see what works best</li>
                <li>Follow up on applications and track your success metrics</li>
            </ul>

            <h2>Don'ts</h2>
            <ul>
                <li>Never submit AI-generated materials without thorough review and personalization</li>
                <li>Do not exaggerate skills or experience in optimized CVs</li>
                <li>Avoid using generic templates without customization</li>
                <li>Do not apply to jobs that don't genuinely match your qualifications</li>
                <li>Never ignore red flags about companies or roles during research</li>
                <li>Don't rely solely on keyword optimization—substance matters more</li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
