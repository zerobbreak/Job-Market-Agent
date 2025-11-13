import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Feature Overview - Using the Tool" },
        {
            name: "description",
            content: "Learn about the different features available in Job Market Agent",
        },
    ]
}

export default function UsingModeOverview() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Feature Overview</h1>

            <p>
                Job Market Agent provides multiple AI-powered tools to optimize your job search. 
                You can generate tailored CVs, cover letters, ATS optimization reports, and interview 
                preparation materials within the same job application workflow.
            </p>

            <p>
                This integrated approach reduces complexity by keeping all your job application materials 
                in one place, allowing you to seamlessly switch between different optimization tools 
                as you refine your applications.
            </p>

            <h2>Available Features</h2>
            <ul>
                <li><strong>CV Rewriter:</strong> Tailor your CV to match specific job descriptions</li>
                <li><strong>ATS Optimizer:</strong> Maximize compatibility with Applicant Tracking Systems</li>
                <li><strong>Cover Letter Specialist:</strong> Generate compelling, personalized cover letters</li>
                <li><strong>Interview Prep Agent:</strong> Prepare for interviews with AI-generated questions and answers</li>
                <li><strong>Research:</strong> Deep dive into company information and industry insights</li>
                <li><strong>Notes:</strong> Keep track of your application progress and insights</li>
            </ul>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
