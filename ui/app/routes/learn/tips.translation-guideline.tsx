import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Global Job Search - Job Market Agent" },
        {
            name: "description",
            content:
                "Learn how Job Market Agent supports job searches across global markets with multi-language capabilities.",
        },
    ]
}

export default function TipsTranslationGuideline() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Global Job Search</h1>

            <p>
                Job Market Agent supports job searches across international markets, helping you 
                discover opportunities beyond your local region. Our platform can parse and optimize 
                applications for jobs posted in multiple languages.
            </p>

            <h2>Multi-Language Support</h2>
            <p>
                While the platform interface is currently in English, we can process and optimize 
                job applications for positions posted in various languages. Our AI can help translate 
                and adapt your materials for international opportunities.
            </p>

            <h2>Regional Considerations</h2>
            <ul>
                <li><strong>CV Formats:</strong> Different regions prefer different CV styles (US resume vs. European CV)</li>
                <li><strong>Application Customs:</strong> Understanding local job application conventions</li>
                <li><strong>Time Zones:</strong> Consider application timing for different regions</li>
                <li><strong>Work Authorization:</strong> Clearly indicate work authorization status for international roles</li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
