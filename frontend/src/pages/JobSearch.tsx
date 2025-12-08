import { useState } from 'react'
import { Search, MapPin, Briefcase, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { apiClient } from '@/utils/api'

interface Job {
  id: string
  title: string
  company: string
  location: string
  description: string
  url: string
}

export default function JobSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('South Africa')
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)

  const handleManualSearch = async () => {
    setLoading(true)
    try {
      const response = await apiClient('/search-jobs', {
        method: 'POST',
        body: JSON.stringify({ query: searchQuery, location }),
      })
      const data = await response.json()
      setJobs(data.jobs || [])
    } catch (error) {
      console.error('Error searching jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Explore Jobs</h1>
        <p className="text-muted-foreground">Search for opportunities across the web</p>
      </div>

      <Card className="glass-card border-0 shadow-lg">
        <CardHeader>
          <CardTitle>Search Criteria</CardTitle>
          <CardDescription>Enter keywords and location to find jobs</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="search-query" className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-primary" />
                Job Title or Keywords
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search-query"
                  placeholder="e.g. Software Engineer"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-11"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location" className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" />
                Location
              </Label>
              <div className="relative">
                 <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="location"
                  placeholder="e.g. South Africa"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="pl-9 h-11"
                />
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button
            onClick={handleManualSearch}
            disabled={loading}
            className="w-full h-12 text-lg"
            size="lg"
          >
            {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Search className="h-5 w-5 mr-2" />}
            Search Jobs
          </Button>
        </CardFooter>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {jobs.map((job) => (
          <Card key={job.id} className="group hover:shadow-xl transition-all duration-300 border-l-4 border-l-transparent hover:border-l-primary flex flex-col">
            <CardHeader>
              <CardTitle className="line-clamp-1 group-hover:text-primary transition-colors">{job.title}</CardTitle>
              <CardDescription className="flex items-center gap-2">
                <span className="font-medium text-foreground/80">{job.company}</span>
                <span>•</span>
                <span>{job.location}</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <p className="text-muted-foreground line-clamp-3 text-sm leading-relaxed">{job.description}</p>
            </CardContent>
            <CardFooter className="pt-4 border-t bg-muted/20">
              <Button
                variant="outline"
                className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-all"
                onClick={() => window.open(job.url, '_blank')}
              >
                View Details <ExternalLink className="h-4 w-4 ml-2" />
              </Button>
            </CardFooter>
          </Card>
        ))}
        {jobs.length === 0 && !loading && (
            <div className="col-span-full text-center py-20 text-muted-foreground">
                <Search className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>No jobs found. Try adjusting your search terms.</p>
            </div>
        )}
      </div>
    </div>
  )
}
