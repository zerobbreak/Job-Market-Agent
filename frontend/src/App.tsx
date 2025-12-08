import React, { useState, useEffect } from 'react'
import { Suspense } from 'react'
import { Search, Upload, FileText, Briefcase, User, Sparkles, CheckCircle, TrendingUp, Target, Award, Loader2, LogOut } from 'lucide-react'
import { useAuth } from './context/AuthContext'
import { useToast } from './components/ui/toast'
import Login from './components/Login'
import Register from './components/Register'
import { apiClient } from './utils/api'
import { track } from './utils/analytics'
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
  const toast = useToast()
  const [showRegister, setShowRegister] = useState(false)

  const [activeTab, setActiveTab] = useState<'home' | 'search' | 'applications' | 'profile'>('home')
  const [uploadStep, setUploadStep] = useState<UploadStep>('upload')
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [matchedJobs, setMatchedJobs] = useState<MatchedJob[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [appsPage, setAppsPage] = useState(1)
  const [appsLimit] = useState(10)
  const [appsTotal, setAppsTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')

  // New state for Apply with AI
  const [applying, setApplying] = useState(false)
  const [generatedFiles, setGeneratedFiles] = useState<{ cv: string, cover_letter: string, interview_prep?: string } | null>(null)
  const [generatedATS, setGeneratedATS] = useState<{ score?: number, analysis?: string } | null>(null)
  const API_ORIGIN = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/api$/, '')

  const ApplicationsList = React.lazy(() => import('./components/ApplicationsList'))

  // Manual search state
  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('South Africa')
  const [manualJobs, setManualJobs] = useState<Job[]>([])

  // Filtering state
  const [minMatchScore, setMinMatchScore] = useState(0)
  const [useDemoJobs, setUseDemoJobs] = useState(false)
  const [manualDescription, setManualDescription] = useState('')
  const [manualTitle, setManualTitle] = useState('')

  // Profile editing state
  const [isEditing, setIsEditing] = useState(false)

  // Load initial data
  useEffect(() => {
    if (user) {
      fetchApplications(1);
      if (matchedJobs.length === 0) {
        recoverMatches();
      }
    }
  }, [user]);

  const fetchApplications = async (page?: number) => {
    try {
      const p = page ?? appsPage
      const response = await apiClient(`/applications?page=${p}&limit=${appsLimit}`);
      const data = await response.json();
      if (data.applications) {
        setApplications(data.applications);
        setAppsPage(data.page || p)
        setAppsTotal(data.total || data.applications.length)
      }
    } catch (err) {
      console.error('Error fetching applications:', err);
    }
  };

  const recoverMatches = async () => {
    try {
      const response = await apiClient(`/matches/last?location=${encodeURIComponent(location)}`)
      const data = await response.json()
      if (data.success && Array.isArray(data.matches) && data.matches.length > 0) {
        setMatchedJobs(data.matches)
        setUploadStep('results')
        toast.show({ title: 'Resumed', description: 'Loaded your last matches', variant: 'success' })
      }
    } catch (e) {
      console.error('Recover matches failed', e)
    }
  }

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
        setSuccess('Profile updated successfully!');
        toast.show({ title: 'Profile saved', description: 'Your changes have been saved', variant: 'success' })
        track('profile_saved', { notification_enabled: profile.notification_enabled, threshold: profile.notification_threshold }, 'app')
      } else {
        setError(data.error || 'Failed to update profile');
        toast.show({ title: 'Save failed', description: data.error || 'Failed to update profile', variant: 'error' })
        track('profile_save_failed', { error: data.error }, 'app')
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

    if (file.size > 10 * 1024 * 1024) {
      setError('File is too large. Max 10MB.')
      toast.show({ title: 'Upload failed', description: 'File is too large. Max 10MB.', variant: 'error' })
      track('cv_upload_invalid', { reason: 'size', size: file.size }, 'app')
      return
    }
    const allowed = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (file.type && !allowed.includes(file.type)) {
      setError('Invalid file type. Please upload PDF, DOC, or DOCX.')
      toast.show({ title: 'Upload failed', description: 'Invalid file type. Use PDF, DOC, or DOCX.', variant: 'error' })
      track('cv_upload_invalid', { reason: 'type', type: file.type }, 'app')
      return
    }

    setCvFile(file)
    setError('')
    setSuccess('')
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
          max_results: 20,
          use_demo: useDemoJobs
        }),
      })

      const data = await response.json()

      if (data.success) {
        setMatchedJobs(data.matches || [])
        setUploadStep('results')
        track('matches_search', { location, count: (data.matches || []).length, use_demo: useDemoJobs }, 'app')
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
    setApplyCancelled(false)

    try {
      const start = await apiClient('/apply-job', {
        method: 'POST',
        body: JSON.stringify({ job }),
      })
      const startData = await start.json()
      if (!startData.success || !startData.job_id) {
        setError(startData.error || 'Failed to start application')
        setApplying(false)
        track('apply_start_failed', { error: startData.error }, 'app')
        return
      }
      const jobId = startData.job_id
      setCurrentApplyJobId(jobId)
      track('apply_start', { jobId, title: job.title, company: job.company }, 'app')

      let attempts = 0
      const maxAttempts = 40
      setApplyMaxAttempts(maxAttempts)
      const delay = (ms: number) => new Promise(res => setTimeout(res, ms))
      while (attempts < maxAttempts) {
        if (applyCancelled) {
          setError('Application cancelled')
          break
        }
        const statusResp = await apiClient(`/apply-status?job_id=${jobId}`, { method: 'GET' })
        const statusData = await statusResp.json()
        if (statusData.status === 'done' && statusData.files) {
          const newApplication: Application = {
            id: Date.now().toString(),
            jobTitle: job.title,
            company: job.company,
            status: 'applied',
            appliedDate: new Date().toISOString().split('T')[0],
            files: statusData.files
          }
          setApplications([...applications, newApplication])
          setGeneratedFiles({
            cv: statusData.files.cv,
            cover_letter: statusData.files.cover_letter,
            interview_prep: statusData.files.interview_prep
          })
          if (statusData.ats) {
            setGeneratedATS({ score: statusData.ats.score, analysis: statusData.ats.analysis })
          }
          track('apply_complete', { jobId, title: job.title, company: job.company }, 'app')
          break
        }
        if (statusData.status === 'error') {
          setError(statusData.error || 'Application failed')
          track('apply_error', { jobId, error: statusData.error }, 'app')
          break
        }
        if (statusData.status === 'not_found') {
          // Short backoff if status not yet registered
          attempts += 1
          await delay(1000)
          continue
        }
        attempts += 1
        setApplyAttempts(attempts)
        const backoff = Math.min(1000 * Math.pow(1.3, attempts), 5000)
        await delay(backoff)
      }
      if (attempts >= maxAttempts) {
        setError('Application is taking longer than expected. Please check again later.')
        toast.show({ title: 'Application delayed', description: 'Please check again later', variant: 'error' })
      }
    } catch (error) {
      console.error('Error applying to job:', error)
      setError('Error submitting application. Please try again.')
      toast.show({ title: 'Application failed', description: 'Please try again later', variant: 'error' })
      track('apply_exception', {}, 'app')
    } finally {
      setApplying(false)
      setCurrentApplyJobId(null)
    }
  }

  const [currentApplyJobId, setCurrentApplyJobId] = useState<string | null>(null)
  const [applyAttempts, setApplyAttempts] = useState(0)
  const [applyMaxAttempts, setApplyMaxAttempts] = useState(40)
  const [applyCancelled, setApplyCancelled] = useState(false)

  const handleCancelApply = async () => {
    try {
      setApplyCancelled(true)
      if (currentApplyJobId) {
        await apiClient(`/apply-cancel?job_id=${currentApplyJobId}`, { method: 'POST' })
      }
      toast.show({ title: 'Cancelled', description: 'Application process cancelled', variant: 'error' })
    } catch (e) {
      console.error('Cancel apply failed', e)
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

  // moved to MatchedResults

  

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
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
          {success}
        </div>
      )}
      {applying && (
        <div className="mb-6 bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Applying to job... ({Math.min(100, Math.round((applyAttempts / applyMaxAttempts) * 100))}%)</span>
          </div>
          <Button variant="outline" onClick={handleCancelApply}>Cancel</Button>
        </div>
      )}

        {/* Generated Files Dialog */}
        <Dialog open={!!generatedFiles} onOpenChange={() => { setGeneratedFiles(null); setGeneratedATS(null) }}>
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
              {generatedATS && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="font-medium text-yellow-900">ATS Score: {generatedATS.score ?? 'N/A'}%</div>
                  {generatedATS.analysis && (
                    <p className="text-yellow-800 text-sm mt-1">{generatedATS.analysis}</p>
                  )}
                </div>
              )}
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
            {profile && (
              <Card>
                <CardHeader>
                  <CardTitle>Settings</CardTitle>
                  <CardDescription>Control email notifications for high-quality matches</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={!!profile.notification_enabled}
                      onChange={(e) => setProfile({ ...profile, notification_enabled: e.target.checked })}
                    />
                    <span>Enable email notifications</span>
                  </label>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Minimum Match Score</Label>
                      <Badge variant="outline">{profile.notification_threshold ?? 70}%</Badge>
                    </div>
                    <Slider
                      value={[profile.notification_threshold ?? 70]}
                      onValueChange={(value) => setProfile({ ...profile, notification_threshold: value[0] })}
                      max={100}
                      step={1}
                      className="w-full"
                    />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button onClick={handleSaveProfile} disabled={!profile}>Save Settings</Button>
                </CardFooter>
              </Card>
            )}
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
              <Suspense fallback={<div className="p-6">Loading results...</div>}>
                {React.createElement((React.lazy(() => import('./components/MatchedResults')) as any), {
                  filteredMatchedJobs,
                  minMatchScore,
                  setMinMatchScore: (v: number) => setMinMatchScore(v),
                  useDemoJobs,
                  setUseDemoJobs: (v: boolean) => setUseDemoJobs(v),
                  location,
                  setLocation: (v: string) => setLocation(v),
                  manualTitle,
                  setManualTitle: (v: string) => setManualTitle(v),
                  manualDescription,
                  setManualDescription: (v: string) => setManualDescription(v),
                  findMatches,
                  handleApply,
                })}
              </Suspense>
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
            <Suspense fallback={<div className="p-6">Loading applications...</div>}>
              <ApplicationsList
                applications={applications}
                API_ORIGIN={API_ORIGIN}
                onApply={(j: Job) => handleApply({ id: j.id, title: j.title, company: j.company, location: j.location, description: j.description, url: j.url })}
                serverPage={appsPage}
                serverTotalPages={Math.max(1, Math.ceil(appsTotal / appsLimit))}
                onPageChange={(p: number) => { setAppsPage(p); fetchApplications(p) }}
              />
            </Suspense>
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

                    <div className="space-y-2">
                      <Label>Notifications</Label>
                      {isEditing ? (
                        <div className="space-y-4">
                          <label className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={!!profile.notification_enabled}
                              onChange={(e) => setProfile({ ...profile, notification_enabled: e.target.checked })}
                            />
                            <span>Enable email notifications for high-quality matches</span>
                          </label>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <Label className="text-sm font-medium">Minimum Match Score</Label>
                              <Badge variant="outline">{profile.notification_threshold ?? 70}%</Badge>
                            </div>
                            <Slider
                              value={[profile.notification_threshold ?? 70]}
                              onValueChange={(value) => setProfile({ ...profile, notification_threshold: value[0] })}
                              max={100}
                              step={1}
                              className="w-full"
                            />
                          </div>
                        </div>
                      ) : (
                        <div className="text-sm text-gray-700">
                          <p>
                            Notifications: {profile.notification_enabled ? 'Enabled' : 'Disabled'}
                          </p>
                          {profile.notification_enabled && (
                            <p>
                              Threshold: {profile.notification_threshold ?? 70}% match
                            </p>
                          )}
                        </div>
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
