import { TrendingUp, Users, Clock, CheckCircle } from "lucide-react";

const stats = [
  {
    label: "Success Rate",
    value: "89%",
    description: "Candidates landing interviews",
    icon: TrendingUp,
    color: "text-green-400",
    bg: "bg-green-400/10",
  },
  {
    label: "Active Users",
    value: "10k+",
    description: "Trusting our AI agents",
    icon: Users,
    color: "text-blue-400",
    bg: "bg-blue-400/10",
  },
  {
    label: "Time Saved",
    value: "15hrs",
    description: "Average per week",
    icon: Clock,
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
  },
  {
    label: "Jobs Applied",
    value: "500k+",
    description: "Processed automatically",
    icon: CheckCircle,
    color: "text-purple-400",
    bg: "bg-purple-400/10",
  },
];

const Stats = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="group relative p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl hover:bg-white/10 transition-all duration-300 hover:-translate-y-1"
        >
          <div
            className={`absolute inset-0 bg-linear-to-br ${stat.bg} to-transparent opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-500`}
          />
          <div className="relative flex flex-col items-center text-center">
            <div
              className={`p-3 rounded-xl ${stat.bg} mb-4 group-hover:scale-110 transition-transform duration-300`}
            >
              <stat.icon className={`h-6 w-6 ${stat.color}`} />
            </div>
            <div className="text-3xl font-bold text-white mb-1 tracking-tight">
              {stat.value}
            </div>
            <div className="text-sm font-medium text-gray-200 mb-1">
              {stat.label}
            </div>
            <div className="text-xs text-gray-400">{stat.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Stats;
