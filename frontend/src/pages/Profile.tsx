import { useState } from 'react'
import { useOutletContext, useNavigate } from 'react-router-dom'
import { 
  User, 
  Award, 
  Briefcase, 
  FileText, 
  TrendingUp, 
  Target, 
  Loader2 
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { useToast } from "@/components/ui/toast"
import { apiClient } from '@/utils/api'
import { track } from '@/utils/analytics'
import type { OutletContextType } from '@/components/layout/RootLayout'

export default function Profile() {
  const { profile, setProfile } = useOutletContext<OutletContextType>()
  const [isEditing, setIsEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const toast = useToast()
  const navigate = useNavigate()

  // Local editing state - initialized from profile or empty
  const [editForm, setEditForm] = useState(profile || {
    skills: [],
    experience_level: '',
    education: '',
    strengths: [],
    career_goals: '',
    notification_enabled: false,
    notification_threshold: 70
  })

  const handleSaveProfile = async () => {
    if (!editForm) return
    setLoading(true)

    try {
      const response = await apiClient('/profile', {
        method: 'PUT',
        body: JSON.stringify(editForm),
      })

      const data = await response.json()
      if (data.success) {
        setProfile(editForm) // Update global state
        setIsEditing(false)
        toast.show({ title: 'Profile saved', description: 'Your changes have been saved', variant: 'success' })
        track('profile_saved', { notification_enabled: editForm.notification_enabled }, 'app')
      } else {
        toast.show({ title: 'Save failed', description: data.error || 'Failed to update profile', variant: 'error' })
      }
    } catch (err) {
      console.error('Error saving profile:', err)
      toast.show({ title: 'Error', description: 'Failed to connect to server', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  if (!profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
        <div className="bg-gray-100 p-6 rounded-full">
            <User className="h-16 w-16 text-gray-400" />
        </div>
        <div>
            <h2 className="text-2xl font-bold text-gray-900">No Profile Found</h2>
            <p className="text-gray-500 max-w-md mt-2">Upload your CV to generate your AI profile and start finding jobs.</p>
        </div>
        <Button onClick={() => navigate('/app/dashboard')} size="lg">
            Go to Dashboard
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">My Profile</h1>
            <p className="text-muted-foreground">Manage your skills and preferences</p>
        </div>
        <Button
            onClick={() => {
                if (isEditing) handleSaveProfile()
                else {
                    setEditForm(profile) // Reset form to current profile
                    setIsEditing(true)
                }
            }}
            variant={isEditing ? "default" : "outline"}
            disabled={loading}
        >
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            {isEditing ? 'Save Changes' : 'Edit Profile'}
        </Button>
      </div>

      <Card className="glass-card shadow-sm">
        <CardHeader>
            <div className="flex items-center space-x-4">
            <div className="h-16 w-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center shadow-md">
                <User className="h-8 w-8 text-white" />
            </div>
            <div>
                <CardTitle>Job Seeker Profile</CardTitle>
                <CardDescription>AI-generated analysis of your CV</CardDescription>
            </div>
            </div>
        </CardHeader>
        <CardContent className="space-y-8">
            {/* Skills */}
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-foreground flex items-center">
                        <Award className="h-5 w-5 mr-2 text-blue-500" />
                        Skills
                    </h4>
                    {isEditing && <span className="text-xs text-muted-foreground">Comma separated</span>}
                </div>
                {isEditing ? (
                    <Textarea
                        value={editForm.skills.join(', ')}
                        onChange={(e) => setEditForm({ ...editForm, skills: e.target.value.split(',').map(s => s.trim()) })}
                    />
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {profile.skills.map((skill, idx) => (
                        <Badge key={idx} variant="secondary" className="bg-blue-50 text-blue-700">{skill}</Badge>
                        ))}
                    </div>
                )}
            </div>

            <div className="grid md:grid-cols-2 gap-8">
                {/* Experience */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-foreground flex items-center">
                        <Briefcase className="h-5 w-5 mr-2 text-purple-500" />
                        Experience Level
                    </h4>
                    {isEditing ? (
                        <Input
                            value={editForm.experience_level}
                            onChange={(e) => setEditForm({ ...editForm, experience_level: e.target.value })}
                        />
                    ) : (
                        <p className="text-foreground/80 bg-muted/30 p-3 rounded-lg">{profile.experience_level || 'Not specified'}</p>
                    )}
                </div>

                {/* Education */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-foreground flex items-center">
                        <FileText className="h-5 w-5 mr-2 text-green-500" />
                        Education
                    </h4>
                    {isEditing ? (
                         <Input
                            value={editForm.education}
                            onChange={(e) => setEditForm({ ...editForm, education: e.target.value })}
                        />
                    ) : (
                        <p className="text-foreground/80 bg-muted/30 p-3 rounded-lg">{profile.education || 'Not specified'}</p>
                    )}
                </div>
            </div>

            {/* Strengths (Read-only as they are AI generated typically, but editable if simple text) */}
             <div className="space-y-3">
                  <h4 className="font-semibold text-foreground flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2 text-orange-500" />
                    Key Strengths
                  </h4>
                   {/* Making strengths editable as simple list for now if needed, but let's keep read-only/simulated edit via textarea if complex. 
                       Actually, let's allow editing as comma list for simplicity in this refactor. */}
                   {isEditing ? (
                        <Textarea
                            value={editForm.strengths.join(', ')}
                            onChange={(e) => setEditForm({ ...editForm, strengths: e.target.value.split(',').map(s => s.trim()) })}
                             placeholder="Leadership, Communication..."
                        />
                   ) : (
                     <ul className="space-y-2">
                        {profile.strengths.map((strength, idx) => (
                        <li key={idx} className="text-sm text-foreground/80 flex items-start gap-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-orange-400 mt-2 flex-shrink-0" />
                            {strength}
                        </li>
                        ))}
                    </ul>
                   )}
            </div>

            {/* Career Goals */}
            <div className="space-y-3">
                <h4 className="font-semibold text-foreground flex items-center">
                    <Target className="h-5 w-5 mr-2 text-red-500" />
                    Career Goals
                </h4>
                {isEditing ? (
                    <Textarea 
                         value={editForm.career_goals}
                         onChange={(e) => setEditForm({ ...editForm, career_goals: e.target.value })}
                         rows={4}
                    />
                ) : (
                    <p className="text-foreground/80 bg-muted/30 p-4 rounded-lg">{profile.career_goals}</p>
                )}
            </div>

             {/* Notifications */}
            <div className="pt-6 border-t">
                <h3 className="text-lg font-semibold mb-4">Preferences</h3>
                <div className="space-y-6">
                    <div className="flex items-center space-x-2">
                        <input
                            type="checkbox"
                            id="notifications"
                            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            checked={isEditing ? !!editForm.notification_enabled : !!profile.notification_enabled}
                            onChange={(e) => isEditing && setEditForm({ ...editForm, notification_enabled: e.target.checked })}
                            disabled={!isEditing}
                        />
                        <Label htmlFor="notifications">Enable email notifications for high-quality matches</Label>
                    </div>
                    
                    {(isEditing ? editForm.notification_enabled : profile.notification_enabled) && (
                         <div className="space-y-2 max-w-sm">
                            <div className="flex justify-between">
                                <Label>Minimum Match Score Threshold</Label>
                                <span className="font-medium text-sm">
                                    {isEditing ? editForm.notification_threshold : profile.notification_threshold}%
                                </span>
                            </div>
                            <Slider
                                value={[isEditing ? (editForm.notification_threshold ?? 70) : (profile.notification_threshold ?? 70)]}
                                onValueChange={(vals) => isEditing && setEditForm({...editForm, notification_threshold: vals[0]})}
                                max={100}
                                step={1}
                                disabled={!isEditing}
                            />
                         </div>
                    )}
                </div>
            </div>
        </CardContent>
      </Card>
    </div>
  )
}
