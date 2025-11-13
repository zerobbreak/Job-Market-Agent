import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Reporting Issues - Job Market Agent" },
        {
            name: "description",
            content:
                "Learn how to report bugs, errors, or technical issues with Job Market Agent to help improve the platform.",
        },
    ]
}

export default function UsingReportingIssues() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Reporting Issues</h1>

            <p>
                We encourage users to report any errors, optimization issues, or technical problems 
                encountered while using Job Market Agent. Your feedback helps us continuously improve 
                the platform's accuracy, performance, and user experience.
            </p>

            <h2>What to Report</h2>
            <p>Please report issues such as:</p>
            <ul>
                <li>Inaccurate ATS optimization scores or recommendations</li>
                <li>Generated materials that don't match job requirements</li>
                <li>Job search results that seem irrelevant or mismatched</li>
                <li>Technical errors, bugs, or performance problems</li>
                <li>Security or privacy concerns</li>
            </ul>

            <h2>How to Report</h2>
            <p>When reporting an issue, please include:</p>
            <ul>
                <li>
                    <strong>Issue type:</strong> Optimization accuracy, job matching, technical error, etc.
                </li>
                <li>
                    <strong>Context:</strong> What feature you were using (CV optimization, job search, etc.)
                </li>
                <li>
                    <strong>Steps to reproduce:</strong> What actions led to the issue
                </li>
                <li>
                    <strong>Expected vs. actual result:</strong> What you expected vs. what happened
                </li>
                <li>Any screenshots or error messages if applicable</li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
