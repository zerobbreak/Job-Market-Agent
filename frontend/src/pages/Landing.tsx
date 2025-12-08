import { Link } from 'react-router-dom'
import { Sparkles, CheckCircle } from 'lucide-react'
import { track } from '../utils/analytics'

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-2 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Job Market Agent</h1>
                <p className="text-xs text-gray-500">AI-Powered Career Matching</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/how-it-works" className="text-sm font-medium text-gray-700">How it works</Link>
              <Link to="/pricing" className="text-sm font-medium text-gray-700">Pricing</Link>
              <Link to="/faq" className="text-sm font-medium text-gray-700">FAQ</Link>
              <Link to="/app" className="text-sm font-medium text-blue-600">Sign in</Link>
              <Link to="/app" className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md">Get Started</Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <section className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl font-extrabold text-gray-900 mb-4">Find your perfect job faster</h2>
            <p className="text-lg text-gray-600 mb-6">Upload your CV, get a structured profile, see high-match roles, and apply with tailored CVs and cover letters in one click.</p>
            <ul className="space-y-3">
              <li className="flex items-start"><CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" /> AI-analyzed profile and match scoring</li>
              <li className="flex items-start"><CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" /> Tailored CV and cover letter generation</li>
              <li className="flex items-start"><CheckCircle className="h-5 w-5 text-green-600 mr-2 mt-0.5" /> Email notifications for top matches</li>
            </ul>
            <div className="mt-8 flex gap-4">
              <Link
                to="/app"
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-md"
                onClick={() => track('cta_click', { cta: 'start_free' }, 'landing')}
              >Start Free</Link>
              <Link
                to="/app"
                className="inline-flex items-center px-6 py-3 border border-gray-300 rounded-md"
                onClick={() => track('cta_click', { cta: 'see_demo' }, 'landing')}
              >See Demo</Link>
            </div>
          </div>
          <div className="bg-white border rounded-xl shadow-sm p-6">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Sparkles className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-center mb-2">How it works</h3>
            <ol className="space-y-4 text-gray-700">
              <li>Upload your CV</li>
              <li>Approve your profile</li>
              <li>View high-match jobs</li>
              <li>Apply with AI-tailored documents</li>
            </ol>
          </div>
        </section>

        <section className="mt-20">
          <h3 className="text-2xl font-bold text-gray-900 mb-6">Trusted by job seekers</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white border rounded-xl p-6">
              <p className="text-gray-700">Matched me to roles I hadn’t considered and the tailored CVs got me interviews.</p>
              <p className="mt-3 text-sm text-gray-500">Software Engineer</p>
            </div>
            <div className="bg-white border rounded-xl p-6">
              <p className="text-gray-700">I applied to three high-match jobs and got quick callbacks.</p>
              <p className="mt-3 text-sm text-gray-500">Data Analyst</p>
            </div>
            <div className="bg-white border rounded-xl p-6">
              <p className="text-gray-700">The email digests keep me focused on the best opportunities.</p>
              <p className="mt-3 text-sm text-gray-500">Product Manager</p>
            </div>
          </div>
        </section>

        <section className="mt-20">
          <div className="bg-white border rounded-xl p-6 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold">Ready to accelerate your job search?</h3>
              <p className="text-gray-600">Start free and apply with AI-tailored documents.</p>
            </div>
            <Link to="/app" className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-md">Get Started</Link>
          </div>
        </section>
      </main>
    </div>
  )
}
