import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuth } from './context/AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import RootLayout from './components/layout/RootLayout'
import Dashboard from './pages/Dashboard'
import JobSearch from './pages/JobSearch'
import Applications from './pages/Applications'
import Profile from './pages/Profile'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
    )
  }

  if (!user) {
    return showRegister ? (
      <Register onLoginClick={() => setShowRegister(false)} />
    ) : (
      <Login onRegisterClick={() => setShowRegister(true)} />
    )
  }

  return children
}

function App() {
  return (
    <Routes>
      <Route
        element={
          <RequireAuth>
            <RootLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="search" element={<JobSearch />} />
        <Route path="applications" element={<Applications />} />
        <Route path="profile" element={<Profile />} />
      </Route>
    </Routes>
  )
}

export default App

