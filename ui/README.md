# Job Market Agent UI

A modern, AI-powered job application management platform that transforms the chaotic job search process into an organized, data-driven workflow.

## 🚀 Features

### **Dual-Purpose Workspace**
- **Job Discovery**: Search across 20+ job platforms simultaneously (LinkedIn, Indeed, Glassdoor, Monster, Dice, etc.)
- **Application Management**: Track and manage all your job applications in one place

### **AI-Powered Job Materials (7 Specialized Agents)**

#### **🖥️ ATS Optimizer**
- Analyzes CVs against Applicant Tracking Systems
- Scores compatibility (0-100) with major ATS platforms
- Identifies missing keywords and suggests improvements
- Provides format compliance checking

#### **📝 CV Rewriter**
- Enhances existing CVs with better content and formatting
- Targets specific job descriptions for tailored improvements
- Provides before/after comparisons with quantifiable metrics

#### **💼 Cover Letter Specialist**
- Generates personalized cover letters based on job descriptions
- Integrates company research and candidate profiles
- Offers multiple tone options (formal, casual, confident)

#### **🎭 Interview Copilot**
- Real-time interview assistance during live interviews
- Provides STAR method frameworks and suggested responses
- Includes response timer and follow-up suggestions

#### **📚 Interview Prep Agent**
- Creates comprehensive interview preparation plans
- Generates question banks categorized by type
- Includes practice sessions with performance tracking

#### **📋 Notes**
- General note-taking and organization for job applications
- Tracks important details, follow-ups, and reminders

#### **🔍 Research**
- Company intelligence and background information
- Role analysis with responsibilities and salary data
- Competitive intelligence and market positioning

## 🏗️ Architecture

### **Tech Stack**
- **Frontend**: React 19 + TypeScript + React Router
- **Styling**: Tailwind CSS + Custom Design System
- **State Management**: Custom Redux-like store with middleware
- **Testing**: Vitest + Playwright E2E
- **Build Tool**: Vite
- **Code Quality**: Biome (linter + formatter)

### **Project Structure**
```
ui/
├── app/                    # React Router application
│   ├── routes/            # Page routes
│   ├── components/        # Reusable UI components
│   ├── services/          # API and business logic
│   ├── hooks/            # Custom React hooks
│   ├── mocks/            # Mock data for development
│   └── utils/            # Utility functions
├── public/               # Static assets
├── tests/               # Test files
└── *.config.*          # Configuration files
```

## 🚀 Getting Started

### **Prerequisites**
- Node.js 20+
- npm or pnpm

### **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd job-market-agent/ui

# Install dependencies
npm install

# Start development server
npm run dev
```

### **Environment Setup**
Create a `.env` file with the following variables:
```env
VITE_JOB_MARKET_API_URL=http://localhost:8000/job-market/api/v1
VITE_OAUTH_PROVIDER_URL=http://localhost:8083
VITE_SESSION_SECRET=your-secure-session-secret
VITE_MODE=development
```

### **Available Scripts**
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run check        # Run linting and type checking
npm run test         # Run unit and E2E tests
npm run format       # Format code with Biome
```

## 🎯 User Journey

### **Phase 1: Discovery & Authentication**
1. **Landing Page** → Compelling value proposition
2. **Registration** → Progressive onboarding with professional details
3. **Workspace** → Personalized dashboard redirect

### **Phase 2: Job Application Management**
1. **Job Discovery** → Universal search across 20+ platforms
2. **Application Creation** → One-click application from discovered jobs
3. **Material Development** → AI-powered content generation
4. **Progress Tracking** → Status updates and success metrics

### **Phase 3: Interview & Follow-up**
1. **Interview Preparation** → Comprehensive prep with AI assistance
2. **Live Interview Support** → Real-time copilot during interviews
3. **Follow-up Management** → Automated reminders and status updates

## 🔧 Development

### **Code Quality**
- **Linting**: Biome configuration with custom rules
- **Formatting**: Consistent code style across the project
- **Type Safety**: Full TypeScript coverage
- **Testing**: Unit tests with Vitest, E2E with Playwright

### **Contributing**
1. Follow the existing code style and patterns
2. Add tests for new features
3. Update documentation as needed
4. Ensure all checks pass before submitting

### **Deployment**
The application is containerized and can be deployed using Docker:

```bash
# Build the Docker image
docker build -t job-market-agent-ui .

# Run the container
docker run -p 80:80 job-market-agent-ui
```

## 📄 Documentation

- **[UI Flow](./UI-Flow.md)** - Complete user journey and page descriptions
- **[API Documentation](./api-docs.md)** - Backend integration details
- **[Component Library](./components.md)** - Reusable component documentation

## 📝 License

Copyright (c) 2025, Adrian Friedman. All rights reserved.

## 🤝 Support

For support or questions, please refer to the project documentation or create an issue in the repository.
