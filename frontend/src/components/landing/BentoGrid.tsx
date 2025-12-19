import {
  Brain,
  Globe,
  LineChart,
  MessageSquare,
  Search,
  Shield,
  Zap,
} from "lucide-react";

export const BentoGrid = () => {
  return (
    <section className="py-24 bg-black/20">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold mb-6">
            Everything you need to{" "}
            <span className="text-blue-400">dominate the market</span>
          </h2>
          <p className="text-gray-400 max-w-2xl mx-auto text-lg">
            Our autonomous agents work 24/7 to find, analyze, and secure
            opportunities tailored to your unique profile.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 md:grid-rows-3 gap-4 h-auto md:h-[800px]">
          {/* Main Feature - Large Square */}
          <div className="md:col-span-2 md:row-span-2 rounded-3xl p-8 bg-linear-to-br from-blue-900/20 to-indigo-900/20 border border-white/10 backdrop-blur-sm hover:border-blue-500/30 transition-all group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-30 transition-opacity">
              <Globe className="w-64 h-64 text-blue-400" />
            </div>
            <div className="relative z-10 h-full flex flex-col justify-between">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4">
                <Search className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">
                  Global Sourcing Engine
                </h3>
                <p className="text-gray-400 mb-6">
                  Aggregates millions of data points from major job boards,
                  company career pages, and hidden niche communities. We don't
                  just search LinkedIn; we scan the entire visible web.
                </p>
                <div className="flex flex-wrap gap-2">
                  {[
                    "LinkedIn",
                    "Indeed",
                    "Glassdoor",
                    "Remote.co",
                    "Y Combinator",
                  ].map((source) => (
                    <span
                      key={source}
                      className="text-xs font-medium px-2 py-1 rounded-full bg-white/5 border border-white/10 text-gray-300"
                    >
                      {source}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Secondary Feature - Tall Vertical */}
          <div className="md:col-span-1 md:row-span-2 rounded-3xl p-8 bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-6">
              <Brain className="h-6 w-6 text-purple-400" />
            </div>
            <h3 className="text-xl font-bold mb-2">Semantic Matching</h3>
            <p className="text-gray-400 text-sm mb-4">
              Our NLP engine understands "Python expert" isn't the same as
              "Learned Python once". It matches deep manufacturing skills, not
              just keywords.
            </p>
            <div className="space-y-3 mt-8">
              {[98, 85, 92].map((score, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500 rounded-full"
                      style={{ width: `${score}%` }}
                    ></div>
                  </div>
                  <span className="text-xs font-mono text-purple-300">
                    {score}% Match
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Speed Feature - Small */}
          <div className="md:col-span-1 md:row-span-1 rounded-3xl p-6 bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all">
            <Zap className="h-8 w-8 text-yellow-400 mb-4" />
            <h3 className="text-lg font-bold mb-1">Zero Latency</h3>
            <p className="text-sm text-gray-400">
              Apply to hot jobs within 45 seconds of posting.
            </p>
          </div>

          {/* Security Feature - Small */}
          <div className="md:col-span-1 md:row-span-1 rounded-3xl p-6 bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-all">
            <Shield className="h-8 w-8 text-green-400 mb-4" />
            <h3 className="text-lg font-bold mb-1">Privacy First</h3>
            <p className="text-sm text-gray-400">
              Your data never leaves our secure encrypted enclave.
            </p>
          </div>

          {/* Wide Feature - Horizontal */}
          <div className="md:col-span-2 md:row-span-1 rounded-3xl p-8 bg-linear-to-r from-gray-900 to-gray-800 border border-white/10 backdrop-blur-sm flex items-center justify-between gap-8 group overflow-hidden">
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
                <LineChart className="h-5 w-5 text-green-400" />
                Market Intelligence
              </h3>
              <p className="text-sm text-gray-400">
                Real-time salary insights and demand forecasting. Know what
                you're worth before you negotiate.
              </p>
            </div>
            <div className="hidden md:flex gap-2">
              <div className="w-16 h-24 bg-white/5 rounded-lg border border-white/10 flex items-end p-1">
                <div className="w-full bg-green-500/50 rounded-sm h-[40%] group-hover:h-[60%] transition-all duration-500"></div>
              </div>
              <div className="w-16 h-24 bg-white/5 rounded-lg border border-white/10 flex items-end p-1">
                <div className="w-full bg-blue-500/50 rounded-sm h-[70%] group-hover:h-[85%] transition-all duration-500 delay-100"></div>
              </div>
              <div className="w-16 h-24 bg-white/5 rounded-lg border border-white/10 flex items-end p-1">
                <div className="w-full bg-purple-500/50 rounded-sm h-[50%] group-hover:h-[90%] transition-all duration-500 delay-200"></div>
              </div>
            </div>
          </div>

          {/* Last Feature - Medium */}
          <div className="md:col-span-2 md:row-span-1 rounded-3xl p-8 bg-white/5 border border-white/10 backdrop-blur-sm flex items-center gap-6">
            <div className="w-16 h-16 rounded-2xl bg-pink-500/20 flex items-center justify-center shrink-0">
              <MessageSquare className="h-8 w-8 text-pink-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Interview Coach</h3>
              <p className="text-sm text-gray-400">
                Generate custom interview Q&A cards based on the specific job
                description and your resume gaps.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
