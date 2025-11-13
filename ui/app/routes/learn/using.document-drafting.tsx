import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Application Materials - Using the Tool" },
        {
            name: "description",
            content: "Learn about generating optimized application materials in Job Market Agent",
        },
    ]
}

export default function UsingDocumentDrafting() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Application Materials</h1>

            <p>
                Job Market Agent enables the creation and download of professionally optimized 
                application materials tailored to specific job opportunities. These include:
            </p>

            <ul>
                <li>
                    <strong>Optimized CVs:</strong> Tailored to match job descriptions with appropriate 
                    keywords, formatting, and structure for maximum ATS compatibility.
                </li>
                <li>
                    <strong>Cover Letters:</strong> Personalized cover letters that highlight relevant 
                    experience and demonstrate genuine interest in the role and company.
                </li>
                <li>
                    <strong>ATS Reports:</strong> Detailed analysis of how well your application 
                    matches the job requirements, including keyword optimization scores.
                </li>
                <li>
                    <strong>Interview Prep Materials:</strong> Customized interview questions, 
                    answers, and company research to help you prepare effectively.
                </li>
            </ul>

            <p>
                These materials are designed to give you a competitive edge, but should be reviewed 
                and personalized to reflect your authentic voice, experiences, and career goals.
            </p>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
