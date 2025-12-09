import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { FileText, Upload, Sparkles, ExternalLink } from 'lucide-react'
import { track } from '@/utils/analytics'
import { Input } from '@/components/ui/input'

type Application = {
  id: string
  jobTitle: string
  company: string
  jobUrl?: string
  location?: string
  status: 'pending' | 'applied' | 'interview' | 'rejected'
  appliedDate: string
  files?: { cv: string, cover_letter: string, interview_prep?: string }
}

function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'applied') return 'default'
  if (status === 'interview') return 'secondary'
  if (status === 'rejected') return 'destructive'
  return 'outline'
}

export default function ApplicationsList({
  applications,
  API_ORIGIN,
  onApply,
  serverPage,
  serverTotalPages,
  onPageChange,
}: {
  applications: Application[]
  API_ORIGIN: string
  onApply: (app: { id: string, title: string, company: string, location: string, description: string, url: string }) => void
  serverPage?: number
  serverTotalPages?: number
  onPageChange?: (page: number) => void
}) {
  const toast = useToast()
  const [page, setPage] = React.useState(serverPage ?? 1)
  React.useEffect(() => { if (serverPage) setPage(serverPage) }, [serverPage])

  // Local copy to support inline status edits without requiring parent refresh
  const [localApps, setLocalApps] = React.useState<Application[]>(applications)
  React.useEffect(() => { setLocalApps(applications) }, [applications])

  // Filters / sort / search state
  const [filterStatus, setFilterStatus] = React.useState<string>('')
  const [searchQuery, setSearchQuery] = React.useState('')
  const [sortBy, setSortBy] = React.useState<'date_desc' | 'date_asc' | 'company' | 'title'>('date_desc')

  // 1. Filter first
  const filtered = localApps.filter((a) => {
    const statusOk = filterStatus ? a.status === filterStatus : true
    const q = searchQuery.trim().toLowerCase()
    const textOk = q
      ? [a.jobTitle, a.company, a.location, a.appliedDate].filter(Boolean).some(v => String(v).toLowerCase().includes(q))
      : true
    return statusOk && textOk
  })

  // 2. Sort
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'date_desc') return (b.appliedDate || '').localeCompare(a.appliedDate || '')
    if (sortBy === 'date_asc') return (a.appliedDate || '').localeCompare(b.appliedDate || '')
    if (sortBy === 'company') return (a.company || '').localeCompare(b.company || '')
    return (a.jobTitle || '').localeCompare(b.jobTitle || '')
  })

  // 3. Paginate
  // If server-side pagination is active, we assume 'sorted' is just the current page (and server handles sort/filter properly? 
  // actually usually server handles it all. If serverTotalPages is set, we shouldn't act like we have all data locally to filter/sort effectively 
  // unless we just filter the current page. But for this fix, we assume client-side if serverTotalPages is missing.)
  
  const totalPages = serverTotalPages ?? Math.max(1, Math.ceil(sorted.length / 10))
  const start = serverTotalPages ? 0 : (page - 1) * 10
  const visible = serverTotalPages ? sorted : sorted.slice(start, start + 10)

  return (
    <>
      <h2 className="text-2xl font-bold text-gray-900">Your Applications</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
        <div>
          <Input
            placeholder="Search title, company, location"
            value={searchQuery}
            onChange={(e) => {
              const v = e.target.value
              setSearchQuery(v)
              track('applications_search', { query: v }, 'applications')
            }}
            aria-label="Search applications"
          />
        </div>
        <div>
          <select
            value={filterStatus}
            onChange={(e) => {
              const v = e.target.value
              setFilterStatus(v)
              track('applications_filter_status', { status: v || 'all' }, 'applications')
            }}
            className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            <option value="applied">Applied</option>
            <option value="interview">Interview</option>
            <option value="rejected">Rejected</option>
            <option value="pending">Pending</option>
          </select>
        </div>
        <div>
          <select
            value={sortBy}
            onChange={(e) => {
              const v = e.target.value as typeof sortBy
              setSortBy(v)
              track('applications_sort', { sortBy: v }, 'applications')
            }}
            className="w-full h-10 rounded-md border border-gray-300 bg-white px-3 text-sm"
            aria-label="Sort applications"
          >
            <option value="date_desc">Newest first</option>
            <option value="date_asc">Oldest first</option>
            <option value="company">Company</option>
            <option value="title">Job Title</option>
          </select>
        </div>
      </div>
      {applications.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
            <p className="text-gray-500">Start applying to jobs to see them here</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {visible.map((application) => (
            <Card key={application.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle>{application.jobTitle}</CardTitle>
                    <CardDescription>{application.company}{application.location ? ` • ${application.location}` : ''}</CardDescription>
                    <p className="text-sm text-muted-foreground mt-1">Applied on {application.appliedDate}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={getStatusBadgeVariant(application.status)}>
                      {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                    </Badge>
                    <select
                      value={application.status}
                      onChange={async (e) => {
                        const newStatus = e.target.value as Application['status']
                        try {
                          const res = await fetch(`${API_ORIGIN}/applications/${application.id}/status`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ status: newStatus })
                          })
                          const data = await res.json()
                          if (!res.ok || data.success === false) throw new Error(data.error || 'Status update failed')
                          setLocalApps(prev => prev.map(a => a.id === application.id ? { ...a, status: newStatus } : a))
                          toast.show({ title: 'Updated', description: 'Application status updated' })
                          track('application_status_changed', { applicationId: application.id, status: newStatus }, 'applications')
                        } catch (err) {
                          toast.show({ title: 'Error', description: 'Could not update status', variant: 'error' })
                        }
                      }}
                      className="h-8 rounded-md border border-gray-300 bg-white px-2 text-sm"
                    >
                      <option value="applied">Applied</option>
                      <option value="interview">Interview</option>
                      <option value="rejected">Rejected</option>
                      <option value="pending">Pending</option>
                    </select>
                  </div>
                </div>
              </CardHeader>
              {application.files && (
                <CardContent>
                  <div className="grid sm:grid-cols-3 gap-3">
                    <a href={`${API_ORIGIN}${application.files.cv}`} download className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors" onClick={() => track('file_download_cv', { applicationId: application.id }, 'applications')}>
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-blue-600 mr-3" />
                        <span className="font-medium text-blue-900">Tailored CV</span>
                      </div>
                      <Upload className="h-4 w-4 text-blue-500 rotate-180" />
                    </a>
                    <a href={`${API_ORIGIN}${application.files.cover_letter}`} download className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors" onClick={() => track('file_download_cover_letter', { applicationId: application.id }, 'applications')}>
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-purple-600 mr-3" />
                        <span className="font-medium text-purple-900">Cover Letter</span>
                      </div>
                      <Upload className="h-4 w-4 text-purple-500 rotate-180" />
                    </a>
                    {application.files.interview_prep && (
                      <a href={`${API_ORIGIN}${application.files.interview_prep}`} download className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors" onClick={() => track('file_download_interview_prep', { applicationId: application.id }, 'applications')}>
                        <div className="flex items-center">
                          <Sparkles className="h-5 w-5 text-green-600 mr-3" />
                          <span className="font-medium text-green-900">Interview Prep</span>
                        </div>
                        <Upload className="h-4 w-4 text-green-500 rotate-180" />
                      </a>
                    )}
                  </div>
                </CardContent>
              )}
              <CardFooter className="flex gap-3">
                {(() => {
                  const url = application.jobUrl
                  const valid = typeof url === 'string' && /^https?:\/\//.test(url)
                  return (
                    <Button
                      variant="outline"
                      className="flex-1"
                      disabled={!valid}
                      onClick={() => {
                        if (!valid) {
                          toast.show({
                            title: 'Invalid link',
                            description: 'This job link is invalid or missing.',
                            variant: 'error'
                          })
                          return
                        }
                        track('application_view_job', { applicationId: application.id, url }, 'applications')
                        window.open(url!, '_blank', 'noopener,noreferrer')
                      }}
                    >
                      View Job <ExternalLink className="h-4 w-4 ml-2" />
                    </Button>
                  )
                })()}
                <Button
                  className="flex-1"
                  onClick={() => {
                    track('application_apply_again', { applicationId: application.id }, 'applications')
                    onApply({ id: application.id, title: application.jobTitle, company: application.company, location: application.location || '', description: '', url: application.jobUrl || '' })
                  }}
                >
                  Apply Again
                </Button>
              </CardFooter>
            </Card>
          ))}
          <div className="flex items-center justify-between mt-2">
            <p className="text-sm text-gray-600">Page {page} of {totalPages}</p>
            <div className="flex gap-2">
              <Button variant="outline" disabled={page <= 1} onClick={() => {
                const next = Math.max(1, page - 1)
                setPage(next)
                onPageChange?.(next)
                track('applications_pagination_prev', { page: next }, 'applications')
              }}>Previous</Button>
              <Button variant="outline" disabled={page >= totalPages} onClick={() => {
                const next = Math.min(totalPages, page + 1)
                setPage(next)
                onPageChange?.(next)
                track('applications_pagination_next', { page: next }, 'applications')
              }}>Next</Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
