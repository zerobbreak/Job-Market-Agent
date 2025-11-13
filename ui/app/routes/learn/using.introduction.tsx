import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Introduction - Using the Tool" },
        {
            name: "description",
            content:
                "Welcome to Job Market Agent - Learn how to use our AI-powered job application assistant effectively",
        },
    ]
}

export default function UsingIntroduction() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Welcome</h1>

            <p>
                Job Market Agent is designed to streamline your job search and application process by leveraging AI-powered tools. 
                The platform helps you discover opportunities across 20+ job platforms, optimize your CV for Applicant Tracking Systems (ATS), 
                generate tailored cover letters, and prepare for interviews.
            </p>

            <p>
                This tool does not replace your personal career strategy and decision-making, but provides a powerful framework 
                to accelerate your job search while maximizing your chances of success through data-driven optimization and intelligent automation.
            </p>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
