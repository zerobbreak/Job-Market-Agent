import { Link } from "react-router-dom";
import { Briefcase, ChevronRight } from "lucide-react";

const Navbar = () => {
  return (
    <nav className="fixed top-0 w-full z-50 border-b border-white/10 bg-black/20 backdrop-blur-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="p-2 rounded-lg bg-blue-600/20 group-hover:bg-blue-600/30 transition-colors">
              <Briefcase className="h-6 w-6 text-blue-400" />
            </div>
            <span className="font-bold text-xl tracking-tight text-white group-hover:text-blue-100 transition-colors">
              JobAgent<span className="text-blue-400">.ai</span>
            </span>
          </Link>

          <div className="flex items-center space-x-4">
            <Link
              to="/login"
              className="text-sm font-medium text-gray-300 hover:text-white transition-colors px-4 py-2"
            >
              Log in
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white px-5 py-2.5 rounded-full transition-all hover:shadow-[0_0_20px_rgba(37,99,235,0.5)] flex items-center group"
            >
              Get Started
              <ChevronRight className="ml-1 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
