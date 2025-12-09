import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { AuthProvider } from './context/AuthContext'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider, ToastViewport } from './components/ui/toast'

const App = React.lazy(() => import('./App'))
const Landing = React.lazy(() => import('./pages/Landing'))
const Pricing = React.lazy(() => import('./pages/Pricing'))
const HowItWorks = React.lazy(() => import('./pages/HowItWorks'))
const FAQ = React.lazy(() => import('./pages/FAQ'))

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-gray-50">Loading...</div>}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/app/*" element={<App />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/faq" element={<FAQ />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
          <ToastViewport />
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  </React.StrictMode>,
)
