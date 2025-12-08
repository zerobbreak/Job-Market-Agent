import { Link } from 'react-router-dom'
import { Accordion, AccordionItem } from '@/components/ui/accordion'

export default function HowItWorks() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-extrabold mb-6">How It Works</h1>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="border rounded-xl p-6">
            <h2 className="text-xl font-bold mb-2">1. Upload CV</h2>
            <p className="text-gray-700">We parse your skills, experience, and goals to build a structured profile.</p>
          </div>
          <div className="border rounded-xl p-6">
            <h2 className="text-xl font-bold mb-2">2. Approve Profile</h2>
            <p className="text-gray-700">Edit and confirm your profile and set preferences like location and thresholds.</p>
          </div>
          <div className="border rounded-xl p-6">
            <h2 className="text-xl font-bold mb-2">3. Get Matches</h2>
            <p className="text-gray-700">Browse high-match roles with reasons why they fit your profile.</p>
          </div>
        </div>

        <div className="mt-12 grid md:grid-cols-3 gap-6">
          <div className="border rounded-xl p-6">
            <h3 className="font-semibold mb-2">Tailored Documents</h3>
            <p className="text-gray-700">Generate CVs and cover letters optimized for each role.</p>
          </div>
          <div className="border rounded-xl p-6">
            <h3 className="font-semibold mb-2">Notifications</h3>
            <p className="text-gray-700">Receive email digests for top matches above your threshold.</p>
          </div>
          <div className="border rounded-xl p-6">
            <h3 className="font-semibold mb-2">Application Tracking</h3>
            <p className="text-gray-700">See applied roles and download your generated documents anytime.</p>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold mb-4">FAQ</h2>
          <Accordion>
            <AccordionItem title="Do I need to re-upload my CV for each application?" defaultOpen>
              No, upload once and we tailor documents per job.
            </AccordionItem>
            <AccordionItem title="Can I edit my profile?">
              Yes, update skills, experience, and goals anytime.
            </AccordionItem>
            <AccordionItem title="How are match reasons generated?">
              We analyze overlap between your profile and the job description.
            </AccordionItem>
          </Accordion>
        </div>

        <Link to="/app" className="inline-block mt-12 px-4 py-2 bg-blue-600 text-white rounded-md">Get Started</Link>
      </div>
    </div>
  )
}
