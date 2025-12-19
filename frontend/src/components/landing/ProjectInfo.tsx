import { Code2, Database, Globe, Server, Users, Cpu } from "lucide-react";

export const ProjectInfo = () => {
  const stack = [
    { name: "React + Vite", icon: Globe, color: "text-blue-400" },
    { name: "TailwindCSS", icon: Code2, color: "text-cyan-400" },
    { name: "Python / Flask", icon: Server, color: "text-yellow-400" },
    { name: "Google Gemini", icon: Cpu, color: "text-purple-400" },
    { name: "Appwrite", icon: Database, color: "text-pink-400" },
  ];

  const contributors = [
    { name: "Kheepo", role: "Core Developer" },
    { name: "Unathi-Tshuma", role: "Core Developer" },
  ];

  return (
    <section className="py-24 border-t border-white/10 relative bg-black/40">
      <div className="max-w-7xl mx-auto px-4">
        {/* Tech Stack */}
        <div className="mb-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold mb-4">Powered by Modern Tech</h2>
            <div className="h-1 w-20 bg-blue-600 rounded-full mx-auto"></div>
          </div>

          <div className="flex flex-wrap justify-center gap-8 md:gap-16 opacity-80">
            {stack.map((item) => (
              <div
                key={item.name}
                className="flex flex-col items-center gap-3 group"
              >
                <div
                  className={`p-4 rounded-2xl bg-white/5 border border-white/10 group-hover:border-white/20 transition-colors ${item.color}`}
                >
                  <item.icon className="w-8 h-8" />
                </div>
                <span className="text-sm font-medium text-gray-400 group-hover:text-white transition-colors">
                  {item.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Contributors */}
        <div>
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold mb-4 flex items-center justify-center gap-2">
              <Users className="w-6 h-6 text-blue-400" />
              Contributors
            </h2>
            <p className="text-gray-400 text-sm">
              Built with passion by the open source community
            </p>
          </div>

          <div className="flex justify-center gap-6">
            {contributors.map((contributor) => (
              <div
                key={contributor.name}
                className="flex items-center gap-4 bg-white/5 border border-white/10 px-6 py-4 rounded-full hover:bg-white/10 transition-colors"
              >
                <div className="w-10 h-10 rounded-full bg-linear-to-br from-blue-500 to-purple-600 flex items-center justify-center text-lg font-bold">
                  {contributor.name[0].toUpperCase()}
                </div>
                <div className="text-left">
                  <div className="font-semibold text-white">
                    {contributor.name}
                  </div>
                  <div className="text-xs text-blue-300">
                    {contributor.role}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
