import { ArrowRight, Radar, Sparkles, Target, Zap } from "lucide-react";
import Navbar from "../components/layout/Navbar";
import Stats from "../components/landing/Stats";
import { BentoGrid } from "../components/landing/BentoGrid";
import { ProjectInfo } from "../components/landing/ProjectInfo";
import { Link } from "react-router-dom";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#0A0F1C] text-white selection:bg-blue-500/30">
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <div className="fixed top-[-20%] right-[-10%] w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="fixed bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[100px] pointer-events-none"></div>

      <Navbar />

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-4 overflow-hidden">
        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-blue-300 mb-8 hover:bg-white/10 transition-colors animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Sparkles className="h-4 w-4" />
            <span>AI-Powered Job Hunting 2.0</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-8 bg-linear-to-b from-white to-white/60 bg-clip-text text-transparent pb-2 animate-in fade-in slide-in-from-bottom-8 duration-1000 fill-mode-forwards">
            Your Personal
            <br />
            <span className="bg-linear-to-r from-blue-400 via-purple-400 to-blue-400 bg-clip-text text-transparent bg-size-[200%_auto] animate-gradient">
              Job Market Agent
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 mb-10 leading-relaxed animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-200 fill-mode-forwards">
            Stop manually applying. Let our advanced AI agents analyze
            applications, optimize your profile, and secure interviews while you
            sleep.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-16 duration-1000 delay-300 fill-mode-forwards">
            <Link
              to="/register"
              className="w-full sm:w-auto px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-semibold transition-all hover:shadow-[0_0_40px_rgba(37,99,235,0.4)] hover:-translate-y-1 flex items-center justify-center group"
            >
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#demo"
              className="w-full sm:w-auto px-8 py-4 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-full font-semibold transition-all hover:-translate-y-1 backdrop-blur-sm"
            >
              Watch Demo
            </a>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section
        id="stats"
        className="py-20 bg-white/5 border-y border-white/5 relative"
      >
        <div className="max-w-7xl mx-auto px-4">
          <Stats />
        </div>
      </section>

      {/* Feature Preview Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4">
          <div className="bg-linear-to-br from-blue-900/20 to-purple-900/20 rounded-3xl p-8 md:p-12 border border-white/10 backdrop-blur-sm relative">
            <div className="flex flex-col md:flex-row items-center gap-12">
              <div className="flex-1 space-y-8">
                <h2 className="text-3xl md:text-4xl font-bold">
                  Intelligent{" "}
                  <span className="text-blue-400">Application Management</span>
                </h2>
                <div className="space-y-6">
                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center shrink-0">
                      <Target className="h-6 w-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2">
                        Smart Matching
                      </h3>
                      <p className="text-gray-400">
                        Our AI analyzes your CV against thousands of listings,
                        assigning a match score so you only apply to roles
                        you'll enjoy.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center shrink-0">
                      <Zap className="h-6 w-6 text-purple-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2">
                        Auto-Generated Assets
                      </h3>
                      <p className="text-gray-400">
                        Get a custom tailored CV and cover letter for every
                        single application in seconds, not hours.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center shrink-0">
                      <Radar className="h-6 w-6 text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold mb-2">
                        Real-time Tracking
                      </h3>
                      <p className="text-gray-400">
                        Watch your application status in real-time. Know exactly
                        when you've been viewed, shortlisted, or invited for an
                        interview.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex-1 w-full relative group">
                {/* Mock UI Card */}
                <div className="relative z-10 bg-[#0F172A] rounded-xl border border-white/10 p-6 shadow-2xl skew-y-1 group-hover:skew-y-0 transition-transform duration-500">
                  <div className="flex items-center justify-between mb-6 border-b border-white/5 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-600/20 flex items-center justify-center">
                        <Target className="h-5 w-5 text-blue-400" />
                      </div>
                      <div>
                        <div className="font-semibold">
                          Senior React Developer
                        </div>
                        <div className="text-xs text-gray-400">
                          TechCorp Inc. • Remote
                        </div>
                      </div>
                    </div>
                    <div className="px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-sm font-medium border border-green-500/20">
                      98% Match
                    </div>
                  </div>

                  <div className="space-y-4 mb-6">
                    <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                      <div className="text-xs text-gray-400 mb-1">
                        Generated Cover Letter snippet
                      </div>
                      <div className="text-sm text-gray-300 italic">
                        "I am writing to express my strong interest in the
                        Senior React Developer position. With my 5 years of
                        experience in..."
                      </div>
                    </div>
                  </div>

                  <button className="w-full py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium text-sm transition-colors">
                    One-Click Apply
                  </button>
                </div>

                {/* Decorative Elements */}
                <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-600/30 rounded-full blur-3xl -z-10"></div>
                <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-purple-600/30 rounded-full blur-3xl -z-10"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bento Grid Features */}
      <BentoGrid />

      {/* How It Works Grid */}
      <section id="features" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Your Journey to Hired
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Simple, transparent, and effective. Here is how we get you placed.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative z-10">
            <FeatureCard
              icon={Target}
              title="1. Connect"
              description="Upload your CV and connect your LinkedIn profile. Our agent builds a comprehensive professional profile for you."
              delay="0"
            />
            <FeatureCard
              icon={Sparkles}
              title="2. Automate"
              description="Set your preferences and let our agent hunt. It identifies high-value opportunities and crafts personalized applications."
              delay="100"
            />
            <FeatureCard
              icon={Zap}
              title="3. Succeed"
              description="Review shortlisted opportunities, approve applications in bulk, and prep for interviews with AI-generated insights."
              delay="200"
            />
          </div>
        </div>
      </section>

      {/* Project Info Section */}
      <ProjectInfo />

      {/* Footer */}
      <footer className="py-12 border-t border-white/10 bg-black/20">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500">
          <p>© 2024 Job Market Agent. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

const FeatureCard = ({
  icon: Icon,
  title,
  description,
  delay,
}: {
  icon: any;
  title: string;
  description: string;
  delay: string;
}) => (
  <div
    className="p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all duration-300 group hover:-translate-y-2"
    style={{ animationDelay: `${delay}ms` }}
  >
    <div className="w-14 h-14 rounded-2xl bg-blue-600/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
      <Icon className="h-7 w-7 text-blue-400" />
    </div>
    <h3 className="text-xl font-bold mb-3 text-white group-hover:text-blue-200 transition-colors">
      {title}
    </h3>
    <p className="text-gray-400 leading-relaxed">{description}</p>
  </div>
);

export default LandingPage;
