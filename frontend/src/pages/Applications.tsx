import { useState, useEffect } from 'react'
import { apiClient } from '@/utils/api'
import ApplicationsList from '@/components/ApplicationsList'
import { useToast } from '@/components/ui/toast'

interface Application {
  id: string
  jobTitle: string
  company: string
  jobUrl?: string
  location?: string
  status: 'pending' | 'applied' | 'interview' | 'rejected'
  appliedDate: string
  files?: { cv: string, cover_letter: string, interview_prep?: string }
}

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([])
  const [page, setPage] = useState(1)
  const [limit] = useState(10)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  const API_ORIGIN = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '')

  const fetchApplications = async (p: number) => {
    setLoading(true)
    try {
      const response = await apiClient(`/applications?page=${p}&limit=${limit}`)
      const data = await response.json()
      if (data.applications) {
        setApplications(data.applications)
        setPage(data.page || p)
        setTotal(data.total || data.applications.length)
      }
    } catch (err) {
      console.error('Error fetching applications:', err)
      toast.show({ title: 'Error', description: 'Failed to load applications', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApplications(1)
  }, [])

  const handleApply = (app: any) => {
    // For now, we just redirect potential re-applications or show a message.
    // Full AI re-application logic would need the Wizard flow or a modal.
    if (typeof app.url === 'string' && /^https?:\/\//.test(app.url)) {
      window.open(app.url, '_blank')
    } else {
      toast.show({ title: 'Info', description: 'Re-application flow is being updated or link is invalid.', variant: 'default' })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Applications</h1>
        <p className="text-muted-foreground">Track your job application status</p>
      </div>

      {loading && applications.length === 0 ? (
        <div className="p-12 text-center text-muted-foreground">Loading applications...</div>
      ) : (
        <ApplicationsList
            applications={applications}
            API_ORIGIN={API_ORIGIN}
            onApply={handleApply}
            serverPage={page}
            serverTotalPages={Math.max(1, Math.ceil(total / limit))}
            onPageChange={(p) => fetchApplications(p)}
        />
      )}
    </div>
  )
}
