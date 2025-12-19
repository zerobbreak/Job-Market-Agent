import React from "react";
import { Link } from "react-router-dom";
import { Sparkles, ArrowLeft } from "lucide-react";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  title,
  subtitle,
}) => {
  return (
    <div className="min-h-screen bg-[#0A0F1C] flex text-white relative overflow-hidden">
      {/* Background Noise */}
      <div className="fixed inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      {/* Left Side - Visuals */}
      <div className="hidden lg:flex w-1/2 relative items-center justify-center p-12 z-10 overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none"></div>
        <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[100px] pointer-events-none"></div>

        {/* Abstract 3D Illustration */}
        <div className="absolute inset-0 flex items-center justify-center opacity-60 mix-blend-lighten pointer-events-none">
          <img
            src="/auth-illustration.png"
            alt="AI Job Market Visualization"
            className="w-full h-full object-cover object-center scale-110"
          />
        </div>

        <div className="relative z-10 max-w-lg space-y-8 backdrop-blur-[2px] p-6 rounded-3xl border border-white/5 bg-black/10 shadow-2xl">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Link>

          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-blue-300 backdrop-blur-md">
              <Sparkles className="h-4 w-4" />
              <span>AI-Powered Job Hunting</span>
            </div>

            <h1 className="text-5xl font-bold tracking-tight bg-linear-to-b from-white to-white/60 bg-clip-text text-transparent drop-shadow-lg">
              {title}
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed font-light">
              {subtitle}
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-12 z-10">
        <div className="w-full max-w-md space-y-8 relative">
          {/* Mobile Gradient */}
          <div className="lg:hidden absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-blue-600/20 rounded-full blur-[80px] -z-10"></div>
          {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
