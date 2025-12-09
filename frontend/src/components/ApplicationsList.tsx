import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/toast'
import { FileText, Upload, Sparkles, ExternalLink } from 'lucide-react'

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
  const totalPages = serverTotalPages ?? Math.max(1, Math.ceil(applications.length / 10))
  const start = (page - 1) * 10
  const visible = serverTotalPages ? applications : applications.slice(start, start + 10)

  return (
    <>
      <h2 className="text-2xl font-bold text-gray-900">Your Applications</h2>
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
                  <Badge variant={getStatusBadgeVariant(application.status)}>
                    {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                  </Badge>
                </div>
              </CardHeader>
              {application.files && (
                <CardContent>
                  <div className="grid sm:grid-cols-3 gap-3">
                    <a href={`${API_ORIGIN}${application.files.cv}`} download className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-blue-600 mr-3" />
                        <span className="font-medium text-blue-900">Tailored CV</span>
                      </div>
                      <Upload className="h-4 w-4 text-blue-500 rotate-180" />
                    </a>
                    <a href={`${API_ORIGIN}${application.files.cover_letter}`} download className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
                      <div className="flex items-center">
                        <FileText className="h-5 w-5 text-purple-600 mr-3" />
                        <span className="font-medium text-purple-900">Cover Letter</span>
                      </div>
                      <Upload className="h-4 w-4 text-purple-500 rotate-180" />
                    </a>
                    {application.files.interview_prep && (
                      <a href={`${API_ORIGIN}${application.files.interview_prep}`} download className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
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
                <Button variant="outline" className="flex-1" asChild>
                  <a
                    href={application.jobUrl || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`View job posting for ${application.jobTitle} at ${application.company}`}
                    onClick={(e) => {
                      const url = application.jobUrl
                      const valid = typeof url === 'string' && /^https?:\/\//.test(url)
                      if (!valid) {
                        e.preventDefault()
                        toast.show({
                          title: 'Invalid link',
                          description: 'This job link is invalid or missing.',
                          variant: 'error'
                        })
                      }
                    }}
                  >
                    View Job <ExternalLink className="h-4 w-4 ml-2" />
                  </a>
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => onApply({ id: application.id, title: application.jobTitle, company: application.company, location: application.location || '', description: '', url: application.jobUrl || '' })}
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
              }}>Previous</Button>
              <Button variant="outline" disabled={page >= totalPages} onClick={() => {
                const next = Math.min(totalPages, page + 1)
                setPage(next)
                onPageChange?.(next)
              }}>Next</Button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
