import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { User, CheckCircle } from 'lucide-react'

type Profile = {
  skills: string[]
  experience_level: string
  education: string
  strengths: string[]
  career_goals: string
  notification_enabled?: boolean
  notification_threshold?: number
}

export default function ProfileView({
  profile,
  isEditing,
  cvFileName,
  setProfile,
}: {
  profile: Profile
  isEditing: boolean
  cvFileName?: string
  setProfile: (p: Profile) => void
}) {
  return (
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
          {cvFileName ? (
            <p className="text-green-600 flex items-center"><CheckCircle className="h-4 w-4 mr-2" />CV uploaded: {cvFileName}</p>
          ) : (
            <p className="text-gray-500">No CV uploaded yet</p>
          )}
        </div>

        <div className="border-t pt-6 space-y-6">
          <div className="space-y-2">
            <Label htmlFor="skills">Skills (comma separated)</Label>
            {isEditing ? (
              <Textarea id="skills" value={profile.skills.join(', ')} onChange={(e) => setProfile({ ...profile, skills: e.target.value.split(',').map(s => s.trim()) })} rows={3} />
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
              <Input id="experience" value={profile.experience_level} onChange={(e) => setProfile({ ...profile, experience_level: e.target.value })} />
            ) : (
              <p className="text-gray-700">{profile.experience_level || 'Not specified'}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="education">Education</Label>
            {isEditing ? (
              <Input id="education" value={profile.education} onChange={(e) => setProfile({ ...profile, education: e.target.value })} />
            ) : (
              <p className="text-gray-700">{profile.education || 'Not specified'}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="goals">Career Goals</Label>
            {isEditing ? (
              <Textarea id="goals" value={profile.career_goals} onChange={(e) => setProfile({ ...profile, career_goals: e.target.value })} rows={3} />
            ) : (
              <p className="text-gray-700">{profile.career_goals}</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
