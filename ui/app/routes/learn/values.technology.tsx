import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Technology - Job Market Agent" },
        {
            name: "description",
            content:
                "Explore the advanced AI technologies powering Job Market Agent, including Claude Sonnet 4, multi-platform job scraping, and ATS optimization.",
        },
    ]
}

export default function ValuesTechnology() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Technology</h1>

            <ul>
                <li>
                    <strong>Claude Sonnet 4:</strong> Advanced language model for CV optimization, 
                    cover letter generation, and interview preparation
                </li>
                <li>
                    <strong>Multi-Platform Job Discovery:</strong> Automated scraping and aggregation 
                    from 20+ job platforms including LinkedIn, Indeed, Glassdoor, and more
                </li>
                <li>
                    <strong>ATS Optimization Engine:</strong> Analyzes job descriptions and optimizes 
                    CVs for maximum Applicant Tracking System compatibility
                </li>
                <li>
                    <strong>Advanced NLP:</strong> Natural language processing for semantic job matching 
                    and skills gap analysis
                </li>
                <li>
                    <strong>Continuous Learning:</strong> Regular updates to improve matching algorithms, 
                    ATS patterns, and optimization strategies
                </li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
