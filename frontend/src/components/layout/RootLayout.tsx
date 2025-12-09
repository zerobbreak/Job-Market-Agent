import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { 
  Search, 
  FileText, 
  User, 
  LogOut, 
  Menu, 
  Sparkles,
  LayoutDashboard
} from 'lucide-react'
import { Button } from "@/components/ui/button"
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/lib/utils'


interface Profile {
  skills: string[]
  experience_level: string
  education: string
  strengths: string[]
  career_goals: string
  notification_enabled?: boolean
  notification_threshold?: number
}

export type OutletContextType = {
  profile: Profile | null
  setProfile: React.Dispatch<React.SetStateAction<Profile | null>>
}

export default function RootLayout() {
  const { user, logout } = useAuth()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/app', icon: LayoutDashboard },
    { name: 'Find Jobs', href: '/app/search', icon: Search },
    { name: 'Applications', href: '/app/applications', icon: FileText },
    { name: 'Profile', href: '/app/profile', icon: User },
  ]

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Desktop Sidebar - Visible on Medium Screens and Up */}
      <aside className="hidden md:flex w-72 flex-col bg-zinc-900 border-r border-zinc-800 shrink-0 text-white">
        <div className="p-6 flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-2 rounded-xl shadow-lg shadow-blue-900/20">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Job Market
            </h1>
            <p className="text-xs text-zinc-400">AI Agent</p>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group",
                  isActive 
                    ? "bg-zinc-800 text-white shadow-lg shadow-black/20" 
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                )}
              >
                <Icon className={cn("h-5 w-5", location.pathname === item.href ? "text-white" : "text-zinc-500 group-hover:text-white")} />
                {item.name}
              </NavLink>
            )
          })}
        </nav>

        <div className="p-4 border-t border-zinc-800 mt-auto">
          <div className="bg-zinc-800/50 rounded-xl p-4 mb-4 backdrop-blur-md border border-zinc-700">
            <div className="flex items-center gap-3 mb-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold shadow-inner">
                {user?.name?.[0] || 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="font-medium text-sm text-white truncate">{user?.name}</p>
                <p className="text-xs text-zinc-400 truncate">{user?.email}</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              className="w-full justify-start text-zinc-400 hover:text-red-400 hover:bg-red-500/10"
              onClick={logout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* Mobile Sidebar - Drawer Style */}
      <div className={cn(
        "fixed inset-0 z-50 md:hidden", 
        isMobileMenuOpen ? "pointer-events-auto" : "pointer-events-none"
      )}>
        {/* Backdrop */}
        <div 
          className={cn(
            "fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300",
            isMobileMenuOpen ? "opacity-100" : "opacity-0"
          )}
          onClick={() => setIsMobileMenuOpen(false)}
        />
        
        {/* Sidebar Panel */}
        <aside 
          className={cn(
            "fixed inset-y-0 left-0 z-50 w-72 bg-zinc-900 border-r border-zinc-800 transform transition-transform duration-300 ease-in-out flex flex-col text-white",
            isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
          )}
        >
          <div className="p-6 flex items-center gap-3">
             <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-2 rounded-xl shadow-lg shadow-blue-900/20">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Job Market
              </h1>
              <p className="text-xs text-zinc-400">AI Agent</p>
            </div>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={`mobile-${item.name}`}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={({ isActive }) => cn(
                    "flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 group",
                    isActive 
                      ? "bg-zinc-800 text-white shadow-lg shadow-black/20" 
                      : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
                  )}
                >
                  <Icon className={cn("h-5 w-5", location.pathname === item.href ? "text-white" : "text-zinc-500 group-hover:text-white")} />
                  {item.name}
                </NavLink>
              )
            })}
          </nav>

          <div className="p-4 border-t border-zinc-800 mt-auto">
            <div className="bg-zinc-800/50 rounded-xl p-4 mb-4 backdrop-blur-md border border-zinc-700">
               <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold shadow-inner">
                  {user?.name?.[0] || 'U'}
                </div>
                <div className="overflow-hidden">
                  <p className="font-medium text-sm text-white truncate">{user?.name}</p>
                  <p className="text-xs text-zinc-400 truncate">{user?.email}</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                className="w-full justify-start text-zinc-400 hover:text-red-400 hover:bg-red-500/10"
                onClick={logout}
              >
                <LogOut className="h-4 w-4 mr-2" />
                Sign Out
              </Button>
            </div>
          </div>
        </aside>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-background/50">
        <header className="md:hidden h-16 border-b bg-background/80 backdrop-blur-md px-4 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center gap-3">
             <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-1.5 rounded-lg">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold">Job Market Agent</span>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setIsMobileMenuOpen(true)}>
            <Menu className="h-6 w-6" />
          </Button>
        </header>

        <main className="flex-1 overflow-auto p-4 md:p-8">
          <div className="max-w-7xl mx-auto animate-fade-in">
            <Outlet context={{ profile, setProfile }} />
          </div>
        </main>
      </div>
    </div>
  )
}
