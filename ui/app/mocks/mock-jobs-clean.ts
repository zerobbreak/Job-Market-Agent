import type { Job, UploadedFile } from "../../@types/job.types"

// Mock uploaded files
const mockUploadedFiles: Record<string, UploadedFile[]> = {
    "job-1": [
        {
            id: "file-1",
            name: "resume_john_doe.pdf",
            size: 2457600,
            type: "application/pdf",
            uploadedAt: "2024-10-01T10:30:00Z",
            status: "completed",
            url: "/mock-files/resume_john_doe.pdf",
        },
        {
            id: "file-2",
            name: "cover_letter.pdf",
            size: 524288,
            type: "application/pdf",
            uploadedAt: "2024-10-01T11:15:00Z",
            status: "completed",
            url: "/mock-files/cover_letter.pdf",
        },
    ],
    "job-2": [
        {
            id: "file-3",
            name: "portfolio.pdf",
            size: 3145728,
            type: "application/pdf",
            uploadedAt: "2024-09-28T14:20:00Z",
            status: "completed",
            url: "/mock-files/portfolio.pdf",
        },
    ],
    "job-3": [
        {
            id: "file-4",
            name: "certifications.pdf",
            size: 2097152,
            type: "application/pdf",
            uploadedAt: "2024-10-05T08:15:00Z",
            status: "completed",
            url: "/mock-files/certifications.pdf",
        },
    ],
}

export const mockJobs: Job[] = (() => {
    const now = new Date().toISOString()
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
    const lastWeek = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()

    return [
        {
            id: "job-1",
            title: "Senior Software Engineer - TechCorp",
            editedDate: now,
            status: "active",
            createdAt: lastWeek,
            updatedAt: now,
            uploads: mockUploadedFiles["job-1"],
            jobMaterials: [
                {
                    id: "mat-1",
                    type: "ats-optimizer",
                    title: "ATS Optimization Report",
                    description: "CV optimization analysis for TechCorp Senior Software Engineer position",
                    content: `# ATS Optimization Report: TechCorp Senior Software Engineer

## Job Description Analysis
Analyzed job posting for Senior Software Engineer position at TechCorp. Key requirements identified: React, TypeScript, Node.js, AWS, and 5+ years experience.

## ATS Compatibility Score: 87%

## Keyword Analysis
**Matched Keywords (Green):**
- JavaScript, TypeScript, React, Node.js, AWS, Docker, Kubernetes, CI/CD

**Missing Keywords (Red):**
- GraphQL, Redux, Jest, Cypress

## Optimization Recommendations
1. **Skills Section**: Add missing technical keywords
2. **Experience**: Quantify achievements with metrics
3. **Summary**: Tailor to job requirements`,
                    createdAt: lastWeek,
                    updatedAt: now,
                    jobId: "job-1",
                },
            ],
        },
        {
            id: "job-2",
            title: "Full Stack Developer - StartupX",
            editedDate: yesterday,
            status: "researching",
            createdAt: lastWeek,
            updatedAt: yesterday,
            uploads: mockUploadedFiles["job-2"],
            jobMaterials: [
                {
                    id: "mat-2",
                    type: "cv-rewriter",
                    title: "CV Enhancement Analysis",
                    description: "Content optimization for StartupX Full Stack Developer role",
                    content: `# CV Enhancement Analysis: StartupX Full Stack Developer

## Current CV Assessment
Analyzed existing CV for completeness and impact. Identified areas for improvement in content structure and keyword optimization.

## Recommended Improvements
1. **Professional Summary**: Add metrics and specific achievements
2. **Skills Section**: Include modern technologies and frameworks
3. **Experience**: Use action verbs and quantify accomplishments`,
                    createdAt: yesterday,
                    updatedAt: now,
                    jobId: "job-2",
                },
            ],
        },
        {
            id: "job-3",
            title: "DevOps Engineer - CloudTech",
            editedDate: lastWeek,
            status: "applied",
            createdAt: lastWeek,
            updatedAt: lastWeek,
            uploads: mockUploadedFiles["job-3"],
            jobMaterials: [
                {
                    id: "mat-3",
                    type: "cover-letter-specialist",
                    title: "Cover Letter - CloudTech DevOps",
                    description: "Generated personalized cover letter for CloudTech DevOps Engineer position",
                    content: `# Cover Letter: DevOps Engineer Position

Dear Hiring Manager,

I am writing to express my strong interest in the DevOps Engineer position at CloudTech. With over 6 years of experience in cloud infrastructure and automation, I am excited about the opportunity to contribute to your innovative team.

## Key Qualifications:
- Extensive AWS and Kubernetes experience
- CI/CD pipeline implementation and management
- Infrastructure as Code using Terraform
- Monitoring and logging solutions expertise

I am particularly drawn to CloudTech's reputation for cutting-edge cloud solutions and would welcome the opportunity to discuss how my background and skills align with your needs.

Best regards,
[Candidate Name]`,
                    createdAt: lastWeek,
                    updatedAt: lastWeek,
                    jobId: "job-3",
                },
            ],
        },
    ]
})()
