import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { FileText, Loader2 } from 'lucide-react'
import { useToast } from '@/components/ui/toast'

type Job = {
  id: string
  title: string
  company: string
  location: string
  description: string
  url: string
}

export default function SearchJobs({
  searchQuery,
  setSearchQuery,
  location,
  setLocation,
  loading,
  handleManualSearch,
  manualJobs,
  onApply,
}: {
  searchQuery: string
  setSearchQuery: (v: string) => void
  location: string
  setLocation: (v: string) => void
  loading: boolean
  handleManualSearch: () => void
  manualJobs: Job[]
  onApply: (job: Job) => void
}) {
  const toast = useToast()
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Explore All Jobs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="search-query">Job Title or Keywords</Label>
              <Input id="search-query" placeholder="e.g. Software Engineer" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input id="location" placeholder="e.g. South Africa" value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleManualSearch} disabled={loading} className="w-full" size="lg">
            {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : null}
            Search Jobs
          </Button>
        </CardFooter>
      </Card>

      <div className="grid gap-4">
        {loading && (
          <>
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white border rounded-xl p-6 animate-pulse">
                <div className="h-5 w-1/3 bg-gray-200 rounded mb-3" />
                <div className="h-4 w-1/4 bg-gray-200 rounded mb-4" />
                <div className="h-16 w-full bg-gray-100 rounded" />
              </div>
            ))}
          </>
        )}
        {manualJobs.map((job) => (
          <Card key={job.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle>{job.title}</CardTitle>
              <CardDescription>{job.company} • {job.location}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 line-clamp-2">{job.description}</p>
            </CardContent>
            <CardFooter className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => {
                if (job.url && /^https?:\/\//.test(job.url)) {
                  window.open(job.url, '_blank')
                } else {
                  toast.show({
                    title: 'Invalid link',
                    description: 'This job listing has no valid URL.',
                    variant: 'error'
                  })
                }
              }}>View Details</Button>
              <Button className="flex-1" onClick={() => onApply(job)}>Apply with AI</Button>
            </CardFooter>
          </Card>
        ))}
        {manualJobs.length === 0 && !loading && (
          <Card>
            <CardContent className="py-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Search to see available roles</h3>
              <p className="text-gray-500">Enter keywords and a location, then click Search Jobs</p>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  )
}
