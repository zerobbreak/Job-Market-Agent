import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "Mission - Job Market Agent" },
        {
            name: "description",
            content:
                "Learn about Job Market Agent's mission to democratize access to AI-powered job search tools.",
        },
    ]
}

export default function AboutMission() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>About Job Market Agent</h1>

            <h2>Our Mission</h2>
            <p>
                To democratize access to enterprise-grade job search optimization tools, empowering 
                every job seeker—regardless of background or resources—to compete effectively in 
                the modern job market.
            </p>

            <h2>Our Vision</h2>
            <p>
                A world where career opportunities are accessible to all, and where AI technology 
                amplifies human potential rather than creating barriers. We believe the job search 
                process should be fair, transparent, and optimized for success.
            </p>

            <h2>Why We Built This</h2>
            <p>
                The traditional job search process is inefficient and often feels like a black box. 
                Applicant Tracking Systems (ATS) filter out qualified candidates, and job seekers 
                struggle to stand out among hundreds of applicants. Meanwhile, professional career 
                coaches and optimization services cost thousands of dollars—creating an uneven playing field.
            </p>

            <p>
                Job Market Agent levels the playing field by providing AI-powered tools that were 
                previously only available to executive job seekers or those who could afford expensive 
                career services.
            </p>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
