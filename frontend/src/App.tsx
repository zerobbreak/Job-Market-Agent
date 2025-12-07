import React, { useState, useEffect } from 'react'
import { Search, Upload, FileText, Briefcase, User, Sparkles, CheckCircle, TrendingUp, Target, Award, Loader2, LogOut } from 'lucide-react'
import { useAuth } from './context/AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import { apiClient } from './utils/api'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Slider } from "@/components/ui/slider"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"

interface Job {
  id: string
  title: string
  company: string
  location: string
  description: string
  url: string
}

interface MatchedJob {
  job: Job
  match_score: number
  match_reasons: string[]
}

interface Profile {
  skills: string[]
  experience_level: string
  education: string
  strengths: string[]
  career_goals: string
  notification_enabled?: boolean
  notification_threshold?: number
}

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

type UploadStep = 'upload' | 'analyzing' | 'profile' | 'matching' | 'results'

function App() {
  const { user, loading: authLoading, logout } = useAuth()
  const [showRegister, setShowRegister] = useState(false)

  const [activeTab, setActiveTab] = useState<'home' | 'search' | 'applications' | 'profile'>('home')
  const [uploadStep, setUploadStep] = useState<UploadStep>('upload')
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [matchedJobs, setMatchedJobs] = useState<MatchedJob[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')

  // New state for Apply with AI
  const [applying, setApplying] = useState(false)
  const [generatedFiles, setGeneratedFiles] = useState<{ cv: string, cover_letter: string, interview_prep?: string } | null>(null)
  const API_ORIGIN = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '')

  // Manual search state
  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('South Africa')
  const [manualJobs, setManualJobs] = useState<Job[]>([])

  // Filtering state
  const [minMatchScore, setMinMatchScore] = useState(0)

  // Profile editing state
  const [isEditing, setIsEditing] = useState(false)

  // Load initial data
  useEffect(() => {
    if (user) {
      fetchApplications();
    }
  }, [user]);

  const fetchApplications = async () => {
    try {
      const response = await apiClient('/applications');
      const data = await response.json();
      if (data.applications) {
        setApplications(data.applications);
      }
    } catch (err) {
      console.error('Error fetching applications:', err);
    }
  };

  const handleSaveProfile = async () => {
    if (!profile) return;

    try {
      const response = await apiClient('/profile', {
        method: 'PUT',
        body: JSON.stringify(profile),
      });

      const data = await response.json();
      if (data.success) {
        setIsEditing(false);
        alert('Profile updated successfully!');
      } else {
        setError(data.error || 'Failed to update profile');
      }
    } catch (err) {
      console.error('Error saving profile:', err);
      setError('Error saving profile. Please try again.');
    }
  };

  if (authLoading) {
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

  const handleCVUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setCvFile(file)
    setError('')
    setUploadStep('analyzing')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('cv', file)

      const response = await apiClient('/analyze-cv', {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (data.success) {
        setProfile(data.profile)
        setUploadStep('profile')

        // Auto-trigger job matching
        setTimeout(() => findMatches(), 1500)
      } else {
        setError(data.error || 'Failed to analyze CV')
        setUploadStep('upload')
      }
    } catch (err) {
      setError('Error uploading CV. Please try again.')
      setUploadStep('upload')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const findMatches = async () => {
    setUploadStep('matching')
    setLoading(true)
    setError('')

    try {
      const response = await apiClient('/match-jobs', {
        method: 'POST',
        body: JSON.stringify({
          location: location,
          max_results: 20
        }),
      })

      const data = await response.json()

      if (data.success) {
        setMatchedJobs(data.matches || [])
        setUploadStep('results')
      } else {
        setError(data.error || 'Failed to find matches')
        setUploadStep('profile')
      }
    } catch (err) {
      setError('Error finding job matches. Please try again.')
      setUploadStep('profile')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleApply = async (job: Job) => {
    setApplying(true)
    setError('')

    try {
      const response = await apiClient('/apply-job', {
        method: 'POST',
        body: JSON.stringify({ job }),
      });

      const result = await response.json();

      if (result.success) {
        const newApplication: Application = {
          id: Date.now().toString(),
          jobTitle: job.title,
          company: job.company,
          status: 'applied',
          appliedDate: new Date().toISOString().split('T')[0],
          files: result.files
        };
        setApplications([...applications, newApplication]);

        // Show generated files
        if (result.files) {
          setGeneratedFiles({
            cv: result.files.cv,
            cover_letter: result.files.cover_letter,
            interview_prep: result.files.interview_prep
          });
        } else {
          alert('Application submitted successfully!');
        }
      } else {
        setError(result.error || 'Failed to apply');
      }
    } catch (error) {
      console.error('Error applying to job:', error);
      setError('Error submitting application. Please try again.');
    } finally {
      setApplying(false);
    }
  }

  const handleManualSearch = async () => {
    setLoading(true)
    try {
      const response = await apiClient('/search-jobs', {
        method: 'POST',
        body: JSON.stringify({ query: searchQuery, location }),
      })
      const data = await response.json()
      setManualJobs(data.jobs || [])
    } catch (error) {
      console.error('Error searching jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  const getMatchBadgeVariant = (score: number): "default" | "secondary" | "destructive" | "outline" => {
    if (score >= 80) return 'default'
    if (score >= 60) return 'secondary'
    return 'outline'
  }

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    if (status === 'applied') return 'default'
    if (status === 'interview') return 'secondary'
    if (status === 'rejected') return 'destructive'
    return 'outline'
  }

  // Filter matched jobs based on minMatchScore
  const filteredMatchedJobs = matchedJobs.filter(match => match.match_score >= minMatchScore)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-blue-600 to-purple-600 p-2 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Job Market Agent
                </h1>
                <p className="text-xs text-gray-500">AI-Powered Career Matching</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {profile && (
                <div className="flex items-center space-x-2 text-sm">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-gray-600">Profile Active</span>
                </div>
              )}
              <div className="flex items-center space-x-3 border-l pl-4">
                <span className="text-sm font-medium text-gray-700">{user.name}</span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={logout}
                  title="Sign Out"
                >
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Generated Files Dialog */}
        <Dialog open={!!generatedFiles} onOpenChange={() => setGeneratedFiles(null)}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <div className="flex items-center justify-center mb-4">
                <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
              </div>
              <DialogTitle className="text-center text-2xl">Application Generated!</DialogTitle>
              <DialogDescription className="text-center">
                Your tailored documents are ready for download.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3 mt-4">
              {generatedFiles && (
                <>
                  <a
                    href={`${API_ORIGIN}${generatedFiles.cv}`}
                    download
                    className="flex items-center justify-between p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-blue-600 mr-3" />
                      <span className="font-medium text-blue-900">Tailored CV</span>
                    </div>
                    <Upload className="h-4 w-4 text-blue-500 rotate-180" />
                  </a>

                  <a
                    href={`${API_ORIGIN}${generatedFiles.cover_letter}`}
                    download
                    className="flex items-center justify-between p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
                  >
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-purple-600 mr-3" />
                      <span className="font-medium text-purple-900">Cover Letter</span>
                    </div>
                    <Upload className="h-4 w-4 text-purple-500 rotate-180" />
                  </a>

                  {generatedFiles.interview_prep && (
                    <a
                      href={`${API_ORIGIN}${generatedFiles.interview_prep}`}
                      download
                      className="flex items-center justify-between p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                    >
                      <div className="flex items-center">
                        <Sparkles className="h-5 w-5 text-green-600 mr-3" />
                        <span className="font-medium text-green-900">Interview Prep</span>
                      </div>
                      <Upload className="h-4 w-4 text-green-500 rotate-180" />
                    </a>
                  )}
                </>
              )}
            </div>

            <Button
              onClick={() => setGeneratedFiles(null)}
              className="w-full mt-4"
              variant="outline"
            >
              Close
            </Button>
          </DialogContent>
        </Dialog>

        {/* Loading Overlay for Application Generation */}
        {applying && (
          <div className="fixed inset-0 bg-white/80 flex items-center justify-center z-50">
            <div className="text-center">
              <Loader2 className="h-12 w-12 text-blue-600 animate-spin mx-auto mb-4" />
              <h3 className="text-xl font-bold text-gray-900">Generating Application...</h3>
              <p className="text-gray-600">Tailoring your CV and writing a cover letter</p>
            </div>
          </div>
        )}

        {/* Tabs Navigation */}
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="home" className="flex items-center gap-2">
              <Target className="h-4 w-4" />
              Smart Match
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Explore Jobs
            </TabsTrigger>
            <TabsTrigger value="applications" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Applications
              {applications.length > 0 && (
                <Badge variant="secondary" className="ml-1">{applications.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              My Profile
            </TabsTrigger>
          </TabsList>

          {/* HOME TAB - CV Upload & Matches */}
          <TabsContent value="home" className="space-y-6">
            {uploadStep === 'upload' && (
              <div className="text-center py-12">
                <div className="bg-gradient-to-br from-blue-500 to-purple-600 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Sparkles className="h-10 w-10 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-3">
                  Find Your Perfect Job Match
                </h2>
                <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                  Upload your CV and let our AI analyze your skills, experience, and career goals to find the best job opportunities for you.
                </p>

                <div className="max-w-xl mx-auto">
                  <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl cursor-pointer bg-white hover:bg-blue-50 transition-all shadow-sm hover:shadow-md border-blue-300">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-16 h-16 mb-4 text-blue-500" />
                      <p className="mb-2 text-lg font-semibold text-gray-700">
                        Click to upload your CV
                      </p>
                      <p className="text-sm text-gray-500">PDF, DOC, or DOCX (Max 10MB)</p>
                    </div>
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.doc,.docx"
                      onChange={handleCVUpload}
                    />
                  </label>
                </div>
              </div>
            )}

            {uploadStep === 'analyzing' && (
              <div className="text-center py-16">
                <Loader2 className="h-16 w-16 text-blue-500 animate-spin mx-auto mb-6" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Analyzing Your CV...</h3>
                <p className="text-gray-600">Our AI is extracting your skills, experience, and strengths</p>
              </div>
            )}

            {uploadStep === 'profile' && profile && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-2xl">Your Profile Analysis</CardTitle>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Award className="h-5 w-5 mr-2 text-blue-500" />
                        Skills & Expertise
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.map((skill, idx) => (
                          <Badge key={idx} variant="secondary">{skill}</Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Briefcase className="h-5 w-5 mr-2 text-purple-500" />
                        Experience Level
                      </h4>
                      <p className="text-gray-700">{profile.experience_level || 'Not specified'}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <FileText className="h-5 w-5 mr-2 text-green-500" />
                        Education
                      </h4>
                      <p className="text-gray-700">{profile.education || 'Not specified'}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <TrendingUp className="h-5 w-5 mr-2 text-orange-500" />
                        Key Strengths
                      </h4>
                      <ul className="space-y-1">
                        {profile.strengths.map((strength, idx) => (
                          <li key={idx} className="text-gray-700 text-sm">• {strength}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {profile.career_goals && (
                    <div className="pt-6 border-t">
                      <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                        <Target className="h-5 w-5 mr-2 text-red-500" />
                        Career Goals
                      </h4>
                      <p className="text-gray-700">{profile.career_goals}</p>
                    </div>
                  )}
                </CardContent>
                <CardFooter>
                  <Button onClick={findMatches} className="w-full" size="lg">
                    Find Matching Jobs
                  </Button>
                </CardFooter>
              </Card>
            )}

            {uploadStep === 'matching' && (
              <div className="text-center py-16">
                <Loader2 className="h-16 w-16 text-purple-500 animate-spin mx-auto mb-6" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Finding Your Perfect Matches...</h3>
                <p className="text-gray-600">Analyzing thousands of jobs to find the best fit for you</p>
              </div>
            )}

            {uploadStep === 'results' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-2xl font-bold text-gray-900">
                    Your Matched Jobs ({filteredMatchedJobs.length})
                  </h3>
                  <Button variant="ghost" onClick={() => setUploadStep('profile')}>
                    View Profile
                  </Button>
                </div>

                {/* Filter Slider */}
                <Card>
                  <CardContent className="pt-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-sm font-medium">Minimum Match Score</Label>
                        <Badge variant="outline">{minMatchScore}%</Badge>
                      </div>
                      <Slider
                        value={[minMatchScore]}
                        onValueChange={(value) => setMinMatchScore(value[0])}
                        max={100}
                        step={1}
                        className="w-full"
                      />
                    </div>
                  </CardContent>
                </Card>

                {filteredMatchedJobs.length === 0 ? (
                  <Card>
                    <CardContent className="py-12 text-center">
                      <Briefcase className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No matches found</h3>
                      <p className="text-gray-500">Try adjusting your filters or location</p>
                    </CardContent>
                  </Card>
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
                              <CardDescription className="text-base">
                                {match.job.company} • {match.job.location}
                              </CardDescription>
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
                          <Button
                            variant="outline"
                            className="flex-1"
                            onClick={() => window.open(match.job.url, '_blank')}
                          >
                            View Details
                          </Button>
                          <Button
                            className="flex-1"
                            onClick={() => handleApply(match.job)}
                          >
                            Apply with AI
                          </Button>
                        </CardFooter>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          {/* SEARCH TAB */}
          <TabsContent value="search" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Explore All Jobs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="search-query">Job Title or Keywords</Label>
                    <Input
                      id="search-query"
                      placeholder="e.g. Software Engineer"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      placeholder="e.g. South Africa"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  onClick={handleManualSearch}
                  disabled={loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Search className="h-5 w-5 mr-2" />}
                  Search Jobs
                </Button>
              </CardFooter>
            </Card>

            <div className="grid gap-4">
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
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => window.open(job.url, '_blank')}
                    >
                      View Details
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={() => handleApply(job)}
                    >
                      Apply with AI
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* APPLICATIONS TAB */}
          <TabsContent value="applications" className="space-y-6">
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
                {applications.map((application) => (
                  <Card key={application.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle>{application.jobTitle}</CardTitle>
                          <CardDescription>{application.company}{application.location ? ` • ${application.location}` : ''}</CardDescription>
                          <p className="text-sm text-muted-foreground mt-1">
                            Applied on {application.appliedDate}
                          </p>
                        </div>
                        <Badge variant={getStatusBadgeVariant(application.status)}>
                          {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                        </Badge>
                      </div>
                    </CardHeader>
                    {application.files && (
                      <CardContent>
                        <div className="grid sm:grid-cols-3 gap-3">
                          <a
                            href={`${API_ORIGIN}${application.files.cv}`}
                            download
                            className="flex items-center justify-between p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                          >
                            <div className="flex items-center">
                              <FileText className="h-5 w-5 text-blue-600 mr-3" />
                              <span className="font-medium text-blue-900">Tailored CV</span>
                            </div>
                            <Upload className="h-4 w-4 text-blue-500 rotate-180" />
                          </a>
                          <a
                            href={`${API_ORIGIN}${application.files.cover_letter}`}
                            download
                            className="flex items-center justify-between p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
                          >
                            <div className="flex items-center">
                              <FileText className="h-5 w-5 text-purple-600 mr-3" />
                              <span className="font-medium text-purple-900">Cover Letter</span>
                            </div>
                            <Upload className="h-4 w-4 text-purple-500 rotate-180" />
                          </a>
                          {application.files.interview_prep && (
                            <a
                              href={`${API_ORIGIN}${application.files.interview_prep}`}
                              download
                              className="flex items-center justify-between p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                            >
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
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={() => application.jobUrl ? window.open(application.jobUrl, '_blank') : undefined}
                      >
                        View Job
                      </Button>
                      <Button
                        className="flex-1"
                        onClick={() => handleApply({ id: application.id, title: application.jobTitle, company: application.company, location: application.location || '', description: '', url: application.jobUrl || '' })}
                      >
                        Apply Again
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* PROFILE TAB */}
          <TabsContent value="profile" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">My Profile</h2>
              {profile && (
                <Button
                  onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)}
                  variant={isEditing ? "default" : "outline"}
                >
                  {isEditing ? 'Save Changes' : 'Edit Profile'}
                </Button>
              )}
            </div>

            <Card>
              <CardHeader>
                <div className="flex items-center space-x-4">
                  <div className="h-16 w-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <User className="h-8 w-8 text-white" />
                  </div>
                  <div>
                    <CardTitle>Job Seeker</CardTitle>
                    <CardDescription>AI-Powered Job Applications</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">CV Status</h4>
                  {cvFile ? (
                    <p className="text-green-600 flex items-center">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      CV uploaded: {cvFile.name}
                    </p>
                  ) : (
                    <p className="text-gray-500">No CV uploaded yet</p>
                  )}
                </div>

                {profile && (
                  <div className="border-t pt-6 space-y-6">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">Profile Analysis</h4>
                      {isEditing && <Badge variant="secondary">Editing Mode</Badge>}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="skills">Skills (comma separated)</Label>
                      {isEditing ? (
                        <Textarea
                          id="skills"
                          value={profile.skills.join(', ')}
                          onChange={(e) => setProfile({ ...profile, skills: e.target.value.split(',').map(s => s.trim()) })}
                          rows={3}
                        />
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {profile.skills.map((skill, idx) => (
                            <Badge key={idx} variant="secondary">{skill}</Badge>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="experience">Experience Level</Label>
                      {isEditing ? (
                        <Input
                          id="experience"
                          value={profile.experience_level}
                          onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })}
                        />
                      ) : (
                        <p className="text-gray-700">{profile.experience_level || 'Not specified'}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="education">Education</Label>
                      {isEditing ? (
                        <Input
                          id="education"
                          value={profile.education}
                          onChange={(e) => setProfile({ ...profile, education: e.target.value })}
                        />
                      ) : (
                        <p className="text-gray-700">{profile.education || 'Not specified'}</p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="goals">Career Goals</Label>
                      {isEditing ? (
                        <Textarea
                          id="goals"
                          value={profile.career_goals}
                          onChange={(e) => setProfile({ ...profile, career_goals: e.target.value })}
                          rows={3}
                        />
                      ) : (
                        <p className="text-gray-700">{profile.career_goals}</p>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App
