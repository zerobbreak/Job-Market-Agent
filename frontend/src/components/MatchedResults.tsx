import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Slider } from '@/components/ui/slider'
import { CheckCircle } from 'lucide-react'

type Job = {
  id: string
  title: string
  company: string
  location: string
  description: string
  url: string
}

type MatchedJob = {
  job: Job
  match_score: number
  match_reasons: string[]
}

function getMatchBadgeVariant(score: number): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (score >= 85) return 'secondary'
  if (score >= 70) return 'default'
  if (score >= 50) return 'outline'
  return 'destructive'
}

export default function MatchedResults({
  filteredMatchedJobs,
  minMatchScore,
  setMinMatchScore,
  useDemoJobs,
  setUseDemoJobs,
  location,
  setLocation,
  manualTitle,
  setManualTitle,
  manualDescription,
  setManualDescription,
  findMatches,
  handleApply,
}: {
  filteredMatchedJobs: MatchedJob[]
  minMatchScore: number
  setMinMatchScore: (v: number) => void
  useDemoJobs: boolean
  setUseDemoJobs: (v: boolean) => void
  location: string
  setLocation: (v: string) => void
  manualTitle: string
  setManualTitle: (v: string) => void
  manualDescription: string
  setManualDescription: (v: string) => void
  findMatches: () => void
  handleApply: (job: Job) => void
}) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-gray-900">
          Your Matched Jobs ({filteredMatchedJobs.length})
        </h3>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Minimum Match Score</Label>
              <Badge variant="outline">{minMatchScore}%</Badge>
            </div>
            <Slider value={[minMatchScore]} onValueChange={(value) => setMinMatchScore(value[0])} max={100} step={1} className="w-full" />
          </div>
        </CardContent>
      </Card>

      {filteredMatchedJobs.length === 0 ? (
        <div className="grid gap-6 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Paste a Job Description</CardTitle>
              <CardDescription>Apply with AI using a job you have</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input placeholder="Job title" value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} />
              <Textarea placeholder="Paste the job description here" value={manualDescription} onChange={(e) => setManualDescription(e.target.value)} rows={5} />
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={() => {
                if (!manualDescription.trim()) return;
                handleApply({ id: Date.now().toString(), title: manualTitle || 'Custom Role', company: 'Manual', location, description: manualDescription, url: '' })
              }}>Apply with AI</Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Switch Location</CardTitle>
              <CardDescription>Search matches in a different area</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input placeholder="e.g. Cape Town" value={location} onChange={(e) => setLocation(e.target.value)} />
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={findMatches}>Search Again</Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Enable Demo Jobs</CardTitle>
              <CardDescription>See sample roles when none are found</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <label className="flex items-center gap-3">
                <input type="checkbox" checked={useDemoJobs} onChange={(e) => setUseDemoJobs(e.target.checked)} />
                <span>Show demo jobs</span>
              </label>
            </CardContent>
            <CardFooter>
              <Button className="w-full" onClick={findMatches}>Show Demo Jobs</Button>
            </CardFooter>
          </Card>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredMatchedJobs.map((match, idx) => (
            <Card key={idx} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <CardTitle className="text-xl">{match.job.title}</CardTitle>
                      <Badge variant={getMatchBadgeVariant(match.match_score)}>
                        {match.match_score}% Match
                      </Badge>
                    </div>
                    <CardDescription className="text-base">{match.job.company} • {match.job.location}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-sm font-semibold mb-2">Why this matches:</p>
                  <ul className="space-y-1">
                    {match.match_reasons.map((reason, ridx) => (
                      <li key={ridx} className="text-sm flex items-start">
                        <CheckCircle className="h-4 w-4 mr-2 mt-0.5 text-green-500 flex-shrink-0" />
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="text-gray-700 line-clamp-2">{match.job.description}</p>
              </CardContent>
              <CardFooter className="flex gap-3">
                <Button variant="outline" className="flex-1" onClick={() => window.open(match.job.url, '_blank')}>View Details</Button>
                <Button className="flex-1" onClick={() => handleApply(match.job)}>Apply with AI</Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
