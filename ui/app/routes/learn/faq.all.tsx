import { useState } from "react"
import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [
        { title: "FAQ - Job Market Agent" },
        {
            name: "description",
            content: "Frequently asked questions about Job Market Agent",
        },
    ]
}

const faqs = [
    {
        question: "Can I use AI-generated materials without editing them?",
        answer: "No. Always personalize and verify AI-generated content to ensure it accurately reflects your experience and voice.",
    },
    {
        question: "How many job platforms does Job Market Agent search?",
        answer: "We aggregate jobs from 20+ platforms including LinkedIn, Indeed, Glassdoor, and specialized industry sites.",
    },
    {
        question: "Does this tool guarantee job offers?",
        answer: "No, it optimizes your applications and maximizes your chances, but success depends on many factors including your qualifications and the job market.",
    },
    {
        question: "How does ATS optimization work?",
        answer: "We analyze job descriptions to identify key requirements and optimize your CV with appropriate keywords, formatting, and structure that ATS systems can parse effectively.",
    },
    {
        question: "Is my data secure?",
        answer: "Yes. We use encryption and zero-knowledge infrastructure to protect your personal information and job search data.",
    },
    {
        question: "Can I customize the generated materials?",
        answer: "Absolutely. All materials are fully editable and we encourage you to add your personal touch and verify accuracy.",
    },
    {
        question: "Which file formats are supported?",
        answer: "We support PDF, DOCX, DOC, TXT, and common image formats for document uploads.",
    },
    {
        question: "What values guide the platform?",
        answer: "Accuracy, empowerment, innovation, user success, and transparency in AI-powered career advancement.",
    },
]

export default function FAQAll() {
    const [openItems, setOpenItems] = useState<Set<number>>(new Set())

    const toggleItem = (index: number) => {
        const newOpenItems = new Set(openItems)
        if (newOpenItems.has(index)) {
            newOpenItems.delete(index)
        } else {
            newOpenItems.add(index)
        }
        setOpenItems(newOpenItems)
    }

    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>FAQ</h1>

            <p className="text-[#7a7a7a] mb-8">Frequently asked questions about Job Market Agent</p>

            <div className="space-y-4">
                {faqs.map((faq, index) => (
                    <div
                        key={faq.question}
                        className="border border-[#edebe5] rounded-lg overflow-hidden"
                    >
                        <button
                            type="button"
                            onClick={() => toggleItem(index)}
                            aria-expanded={openItems.has(index)}
                            aria-controls={`faq-panel-${index}`}
                            className="w-full px-6 py-4 text-left bg-white hover:bg-[#f9fafb] transition-colors flex items-center justify-between"
                        >
                            <span className="font-medium text-[#151515] flex items-center gap-3">
                                <span className="text-lg">{openItems.has(index) ? "▼" : "▶"}</span>
                                {faq.question}
                            </span>
                        </button>

                        {openItems.has(index) && (
                            <div id={`faq-panel-${index}`} className="px-6 pb-4 pl-14">
                                <p className="text-[#7a7a7a]">{faq.answer}</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Feedback Section */}
            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
