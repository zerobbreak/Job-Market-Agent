import React, { useState } from 'react'
import { Search, Upload, FileText, Briefcase, User, Sparkles } from 'lucide-react'

interface Job {
  id: string
  title: string
  company: string
  location: string
  description: string
  url: string
}

interface Application {
  id: string
  jobTitle: string
  company: string
  status: 'pending' | 'applied' | 'interview' | 'rejected'
  appliedDate: string
}

function App() {
  const [activeTab, setActiveTab] = useState<'search' | 'applications' | 'profile'>('search')
  const [searchQuery, setSearchQuery] = useState('')
  const [location, setLocation] = useState('')
  const [jobs, setJobs] = useState<Job[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [loading, setLoading] = useState(false)
  const [cvFile, setCvFile] = useState<File | null>(null)

  const handleSearch = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/search-jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: searchQuery, location }),
      })
      const data = await response.json()
      setJobs(data.jobs || [])
    } catch (error) {
      console.error('Error searching jobs:', error)
      // Fallback mock data
      setJobs([
        {
          id: '1',
          title: 'Senior Software Engineer',
          company: 'Tech Corp',
          location: 'San Francisco, CA',
          description: 'We are looking for an experienced software engineer...',
          url: 'https://example.com/job1'
        },
        {
          id: '2',
          title: 'Full Stack Developer',
          company: 'StartupXYZ',
          location: 'Remote',
          description: 'Join our growing team as a full stack developer...',
          url: 'https://example.com/job2'
        }
      ])
    }
    setLoading(false)
  }

  const handleApply = async (job: Job) => {
    if (!cvFile) {
      alert('Please upload your CV first')
      return
    }

    const formData = new FormData()
    formData.append('cv', cvFile)
    formData.append('job', JSON.stringify(job))

    try {
      const response = await fetch('http://localhost:8000/api/apply-job', {
        method: 'POST',
        body: formData,
      })
      const result = await response.json()
      
      if (result.success) {
        const newApplication: Application = {
          id: Date.now().toString(),
          jobTitle: job.title,
          company: job.company,
          status: 'applied',
          appliedDate: new Date().toISOString().split('T')[0]
        }
        setApplications([...applications, newApplication])
        alert('Application submitted successfully!')
      }
    } catch (error) {
      console.error('Error applying to job:', error)
      alert('Error submitting application. Please try again.')
    }
  }

  const handleCVUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setCvFile(file)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Job Market Agent</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">AI-Powered Job Search</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('search')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'search'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Search className="h-4 w-4" />
                <span>Job Search</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('applications')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'applications'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4" />
                <span>Applications</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'profile'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>Profile</span>
              </div>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'search' && (
          <div className="space-y-6">
            {/* CV Upload */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Your CV</h2>
              <div className="flex items-center justify-center w-full">
                <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-4 text-gray-500" />
                    <p className="mb-2 text-sm text-gray-500">
                      <span className="font-semibold">Click to upload</span> your CV
                    </p>
                    <p className="text-xs text-gray-500">PDF, DOC, DOCX</p>
                  </div>
                  <input
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={handleCVUpload}
                  />
                </label>
              </div>
              {cvFile && (
                <p className="mt-2 text-sm text-green-600">CV uploaded: {cvFile.name}</p>
              )}
            </div>

            {/* Search Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Find Jobs</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <input
                  type="text"
                  placeholder="Job title, keywords, or company"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="text"
                  placeholder="Location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Searching...' : 'Search Jobs'}
              </button>
            </div>

            {/* Job Results */}
            {jobs.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Job Results</h3>
                {jobs.map((job) => (
                  <div key={job.id} className="bg-white rounded-lg shadow p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h4 className="text-xl font-semibold text-gray-900">{job.title}</h4>
                        <p className="text-gray-600">{job.company} • {job.location}</p>
                      </div>
                      <Briefcase className="h-6 w-6 text-gray-400" />
                    </div>
                    <p className="text-gray-700 mb-4">{job.description}</p>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => window.open(job.url, '_blank')}
                        className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200"
                      >
                        View Job
                      </button>
                      <button
                        onClick={() => handleApply(job)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                      >
                        Apply with AI
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Applications</h2>
            {applications.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h3>
                <p className="text-gray-500">Start applying to jobs to see them here</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {applications.map((application) => (
                  <div key={application.id} className="bg-white rounded-lg shadow p-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900">{application.jobTitle}</h4>
                        <p className="text-gray-600">{application.company}</p>
                        <p className="text-sm text-gray-500 mt-1">Applied on {application.appliedDate}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        application.status === 'applied' ? 'bg-blue-100 text-blue-800' :
                        application.status === 'interview' ? 'bg-green-100 text-green-800' :
                        application.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {application.status.charAt(0).toUpperCase() + application.status.slice(1)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'profile' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">Your Profile</h2>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center space-x-4 mb-6">
                <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="h-8 w-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Job Seeker</h3>
                  <p className="text-gray-600">AI-Powered Job Applications</p>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">CV Status</h4>
                  {cvFile ? (
                    <p className="text-green-600">✓ CV uploaded: {cvFile.name}</p>
                  ) : (
                    <p className="text-gray-500">No CV uploaded yet</p>
                  )}
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Applications</h4>
                  <p className="text-gray-600">{applications.length} applications submitted</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">AI Features</h4>
                  <ul className="text-gray-600 space-y-1">
                    <li>• Automatic CV tailoring</li>
                    <li>• Cover letter generation</li>
                    <li>• Interview preparation</li>
                    <li>• Job matching optimization</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App