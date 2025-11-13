import { FeedbackButtons } from "~/components/ui/feedback-buttons"

export function meta() {
    return [{ title: "Data Protection" }]
}

export default function SecurityDataProtection() {
    return (
        <div className="prose prose-lg max-w-4xl">
            <h1>Data Protection</h1>

            <p>
                Your privacy and data security are our top priorities. Job Market Agent implements 
                industry-leading security measures to protect your personal information, career data, 
                and application materials.
            </p>

            <h2>Security Measures</h2>
            <ul>
                <li>
                    <strong>End-to-end encryption:</strong> All data transmitted between your device 
                    and our servers is encrypted using TLS 1.3
                </li>
                <li>
                    <strong>Zero-knowledge architecture:</strong> Your sensitive documents are encrypted 
                    on your device before upload
                </li>
                <li>
                    <strong>Secure storage:</strong> All stored data is encrypted at rest using AES-256
                </li>
                <li>
                    <strong>Access controls:</strong> Strict authentication and authorization for all 
                    data access
                </li>
                <li>
                    <strong>Regular audits:</strong> Periodic security assessments and penetration testing
                </li>
            </ul>

            <h2>Your Data Rights</h2>
            <p>
                You have full control over your data. You can export, delete, or modify your information 
                at any time through your account settings.
            </p>

            <div className="mt-12 pt-8 border-t border-[#edebe5]">
                <FeedbackButtons />
            </div>
        </div>
    )
}
