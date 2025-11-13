import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Our Values - Job Market Agent" },
        {
            name: "description",
            content:
                "Learn about the core values that guide Job Market Agent's development and commitment to ethical AI in career advancement.",
        },
    ]
}

export default function ValuesOurValues() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Our Values</h1>

            <ul>
                <li>
                    <strong>Accuracy & Effectiveness:</strong> High standards for job matching accuracy,
                    ATS optimization, and application success rates
                </li>
                <li>
                    <strong>Empowerment:</strong> Support, not replace, your career judgment and personal
                    decision-making
                </li>
                <li>
                    <strong>Innovation:</strong> Continuous improvement of AI technology for job search
                    and career advancement
                </li>
                <li>
                    <strong>User Success:</strong> Commitment to helping job seekers achieve better
                    career outcomes and land their ideal roles
                </li>
                <li>
                    <strong>Transparency:</strong> Clear explanations of how our AI optimizes your
                    applications and why specific recommendations are made
                </li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
