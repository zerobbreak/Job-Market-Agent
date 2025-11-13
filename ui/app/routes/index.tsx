import { Link } from "react-router"
import { getBrandAssets, getBrandContent } from "~/mocks/mock-brand"

export default function LandingPage() {
    const brandContent = getBrandContent()
    const brandAssets = getBrandAssets()

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#fcfbf8] to-[#f7f4ed]">
            {/* Header */}
            <header className="bg-[#fcfbf8] border-b border-[#edebe5]">
                <div className="penpot-container py-6 flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-4 hover:opacity-80 transition-opacity">
                        <img
                            src={brandAssets.logo || "/placeholder.svg"}
                            alt={`${brandContent.appName} Logo`}
                            className="h-8 w-8 object-contain"
                        />
                        <span className="text-2xl font-semibold text-[#151515]">
                            {brandContent.appName}
                        </span>
                    </Link>
                    <nav className="hidden md:flex items-center gap-8" aria-label="Primary navigation">
                        <Link
                            to="/learn"
                            className="text-[#151515] hover:text-[#4b92ff] transition-colors font-medium"
                        >
                            Learn
                        </Link>
                        <Link
                            to="/register"
                            className="text-[#151515] hover:text-[#4b92ff] transition-colors font-medium"
                        >
                            Sign Up
                        </Link>
                        <Link
                            to="/login"
                            className="bg-[#151515] text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                        >
                            Sign In
                        </Link>
                    </nav>

                    {/* Mobile actions */}
                    <div className="md:hidden flex items-center gap-3">
                        <Link
                            to="/login"
                            className="text-[#151515] hover:text-[#4b92ff] transition-colors font-medium"
                        >
                            Sign In
                        </Link>
                        <Link
                            to="/register"
                            className="bg-[#151515] text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                        >
                            Sign Up
                        </Link>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <main className="penpot-container py-16">
                <div className="text-center mb-16">
                    <h1 className="penpot-heading-xl mb-6 text-[#151515]">
                        Transform Your Job Search with
                        <span className="text-[#4b92ff]"> AI-Powered</span> Tools
                    </h1>
                    <p className="penpot-body-xl mb-8 text-[#7a7a7a] max-w-3xl mx-auto">
                        Stop wasting time on manual applications. Our AI agents optimize your CV,
                        craft personalized cover letters, and guide you through interviews -
                        all while you focus on what matters most.
                    </p>
                    <div className="flex flex-wrap justify-center gap-4">
                        <Link to="/register" className="penpot-button-primary px-8 py-3">
                            Start Your Journey
                        </Link>
                        <Link to="/learn" className="penpot-button-secondary px-8 py-3">
                            Learn More
                        </Link>
                    </div>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
                    <div className="p-6 bg-white rounded-lg border border-[#edebe5] hover:shadow-sm transition-shadow">
                        <div className="w-12 h-12 bg-[#4b92ff] rounded-lg flex items-center justify-center mb-4">
                            <span className="text-white font-bold">🔍</span>
                        </div>
                        <h3 className="font-semibold text-[#151515] mb-2">Universal Job Search</h3>
                        <p className="text-[#7a7a7a] text-sm">
                            Search across 20+ platforms simultaneously. Never miss an opportunity again.
                        </p>
                    </div>

                    <div className="p-6 bg-white rounded-lg border border-[#edebe5] hover:shadow-sm transition-shadow">
                        <div className="w-12 h-12 bg-[#4b92ff] rounded-lg flex items-center justify-center mb-4">
                            <span className="text-white font-bold">🤖</span>
                        </div>
                        <h3 className="font-semibold text-[#151515] mb-2">AI-Powered Optimization</h3>
                        <p className="text-[#7a7a7a] text-sm">
                            ATS-optimized CVs, personalized cover letters, and interview preparation.
                        </p>
                    </div>

                    <div className="p-6 bg-white rounded-lg border border-[#edebe5] hover:shadow-sm transition-shadow">
                        <div className="w-12 h-12 bg-[#4b92ff] rounded-lg flex items-center justify-center mb-4">
                            <span className="text-white font-bold">📊</span>
                        </div>
                        <h3 className="font-semibold text-[#151515] mb-2">Progress Tracking</h3>
                        <p className="text-[#7a7a7a] text-sm">
                            Monitor application status, success rates, and optimize your strategy.
                        </p>
                    </div>
                </div>

                {/* AI Tools Showcase */}
                <div className="text-center mb-16">
                    <h2 className="penpot-heading-large mb-4 text-[#151515]">Meet Your AI Career Assistants</h2>
                    <p className="text-[#7a7a7a] mb-8">
                        Seven specialized AI agents working together to maximize your job search success
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {[
                            { name: "ATS Optimizer", icon: "🎯", desc: "Beat applicant tracking systems" },
                            { name: "CV Rewriter", icon: "✍️", desc: "Enhance your resume content" },
                            { name: "Cover Letter Specialist", icon: "💼", desc: "Personalized cover letters" },
                            { name: "Interview Prep Agent", icon: "🎭", desc: "Comprehensive preparation" },
                            { name: "Interview Copilot", icon: "🎙️", desc: "Real-time interview support" },
                            { name: "Notes", icon: "📝", desc: "Application organization" },
                            { name: "Research", icon: "🔍", desc: "Company intelligence" }
                        ].map((tool) => (
                            <div key={tool.name} className="p-4 bg-white rounded-lg border border-[#edebe5] hover:shadow-sm transition-shadow">
                                <div className="text-2xl mb-2">{tool.icon}</div>
                                <h4 className="font-medium text-[#151515] mb-1">{tool.name}</h4>
                                <p className="text-xs text-[#7a7a7a]">{tool.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CTA Section */}
                <div className="text-center bg-white rounded-lg border border-[#edebe5] p-8">
                    <h2 className="penpot-heading-medium mb-4 text-[#151515]">Ready to Transform Your Job Search?</h2>
                    <p className="text-[#7a7a7a] mb-6">
                        Join thousands of job seekers who have streamlined their applications with AI assistance.
                    </p>
                    <Link to="/register" className="penpot-button-primary px-8 py-3">
                        Get Started Free
                    </Link>
                </div>
            </main>

            {/* Footer */}
            <footer className="border-t border-[#edebe5] px-6 py-8 mt-16">
                <div className="max-w-7xl mx-auto text-center text-[#7a7a7a]">
                    <p>&copy; 2025 Job Market Agent. Transforming job searches with AI.</p>
                </div>
            </footer>
        </div>
    )
}
