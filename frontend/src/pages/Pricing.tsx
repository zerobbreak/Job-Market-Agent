import { Link } from 'react-router-dom'
import { Accordion, AccordionItem } from '@/components/ui/accordion'

export default function Pricing() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-4xl font-extrabold mb-3">Pricing</h1>
        <p className="text-gray-600 mb-10">Choose a plan that fits your job search.</p>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="border rounded-xl p-6">
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="text-xl font-bold">Free</h2>
              <div className="text-3xl font-extrabold">$0</div>
            </div>
            <p className="text-gray-600 mb-4">Get started with essentials</p>
            <ul className="space-y-2 text-sm">
              <li>CV analysis</li>
              <li>Basic match results</li>
              <li>Manual apply</li>
              <li>Community support</li>
            </ul>
          </div>

          <div className="border rounded-xl p-6 bg-blue-50">
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="text-xl font-bold">Pro</h2>
              <div className="text-3xl font-extrabold">$15<span className="text-base font-semibold text-gray-500">/mo</span></div>
            </div>
            <p className="text-gray-600 mb-4">Accelerate your applications</p>
            <ul className="space-y-2 text-sm">
              <li>Unlimited matching</li>
              <li>Tailored CV & cover letters</li>
              <li>Email digests</li>
              <li>Priority support</li>
            </ul>
            <Link to="/app" className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-md">Start Pro</Link>
          </div>

          <div className="border rounded-xl p-6">
            <div className="flex items-baseline justify-between mb-4">
              <h2 className="text-xl font-bold">Team</h2>
              <div className="text-3xl font-extrabold">$49<span className="text-base font-semibold text-gray-500">/mo</span></div>
            </div>
            <p className="text-gray-600 mb-4">For career centers</p>
            <ul className="space-y-2 text-sm">
              <li>Bulk onboarding</li>
              <li>Shared insights</li>
              <li>Admin dashboard</li>
              <li>Priority support</li>
            </ul>
            <Link to="/app" className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-md">Contact Sales</Link>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold mb-4">What’s included</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="border rounded-xl p-6">
              <h3 className="font-semibold mb-2">AI Matching</h3>
              <p className="text-gray-600">See high-match jobs and why they fit your profile.</p>
            </div>
            <div className="border rounded-xl p-6">
              <h3 className="font-semibold mb-2">Tailored Documents</h3>
              <p className="text-gray-600">Generate CVs and cover letters aligned to each role.</p>
            </div>
            <div className="border rounded-xl p-6">
              <h3 className="font-semibold mb-2">Alerts</h3>
              <p className="text-gray-600">Get email digests for top matches above your threshold.</p>
            </div>
          </div>
        </div>

        <div className="mt-16">
          <h2 className="text-2xl font-bold mb-4">FAQ</h2>
          <Accordion>
            <AccordionItem title="Can I cancel anytime?" defaultOpen>
              Yes, you can cancel your subscription at any time.
            </AccordionItem>
            <AccordionItem title="Do you store my CV?">
              Your CV is stored securely and used to tailor applications.
            </AccordionItem>
            <AccordionItem title="How are matches scored?">
              We analyze your skills, experience, and goals against job descriptions.
            </AccordionItem>
          </Accordion>
        </div>
      </div>
    </div>
  )
}
