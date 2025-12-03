# Deployment Guide for Job Market Agent

This guide covers deployment options for your full-stack application:
- **Backend**: Python Flask API (Gunicorn on port 8000)
- **Frontend**: React + TypeScript + Vite
- **Database**: Appwrite (external managed service)

---

## 🎯 Recommended Deployment Options

### Option 1: Separate Deployments (Recommended for Best Performance)

**Frontend: Vercel or Netlify**  
**Backend: Railway or Render**

#### Why This Approach?
- ✅ Frontend gets CDN benefits (fast global delivery)
- ✅ Backend can scale independently
- ✅ Easy to update each part separately
- ✅ Free tier available for both

---

### Option 2: Combined Deployment (Simpler Setup)

**Platform: Render.com or Railway**

#### Why This Approach?
- ✅ Single platform to manage everything
- ✅ Simpler configuration
- ✅ Good for getting started quickly

---

## 📦 Detailed Setup Instructions

### **Option 1A: Frontend on Vercel + Backend on Railway**

#### Frontend Deployment (Vercel)

1. **Build Configuration**
   - Connect your GitHub repository to Vercel
   - Set root directory to `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
   - Install command: `npm install`

2. **Environment Variables** (in Vercel dashboard)
   ```
   VITE_APPWRITE_ENDPOINT=your_appwrite_endpoint
   VITE_APPWRITE_PROJECT_ID=your_project_id
   VITE_API_URL=https://your-backend-url.up.railway.app
   ```

3. **Deploy**
   - Vercel auto-deploys on git push
   - Free tier includes unlimited deployments

#### Backend Deployment (Railway)

1. **Create Railway Project**
   - Go to [railway.app](https://railway.app)
   - Connect GitHub repository
   - Create new project from repo

2. **Configure Service**
   - Railway auto-detects Python/Dockerfile
   - Set start command: `gunicorn api_server:app --bind 0.0.0.0:$PORT`
   - Port is automatically set by Railway

3. **Environment Variables**
   ```
   PORT=8000
   GOOGLE_API_KEY=your_key
   APPWRITE_API_ENDPOINT=your_endpoint
   APPWRITE_PROJECT_ID=your_project_id
   APPWRITE_API_KEY=your_api_key
   ```

4. **Deploy**
   - Railway auto-deploys on push
   - Get your backend URL (e.g., `https://your-app.up.railway.app`)

**Cost**: Free tier available (limited hours), then ~$5-20/month

---

### **Option 1B: Frontend on Netlify + Backend on Render**

#### Frontend Deployment (Netlify)

1. **Build Settings**
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`

2. **Environment Variables**
   ```
   VITE_APPWRITE_ENDPOINT=your_appwrite_endpoint
   VITE_APPWRITE_PROJECT_ID=your_project_id
   VITE_API_URL=https://your-backend.onrender.com
   ```

#### Backend Deployment (Render)

1. **Create Web Service**
   - Connect GitHub repo
   - Environment: Python 3
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn api_server:app --bind 0.0.0.0:$PORT`

2. **Environment Variables** (same as Railway)

**Cost**: Render free tier available (spins down after inactivity), paid ~$7/month

---

### **Option 2: Combined Deployment on Render**

1. **Create Two Services**

   **Service 1: Backend (Web Service)**
   - Environment: Python 3
   - Root directory: `.` (root)
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn api_server:app --bind 0.0.0.0:$PORT`

   **Service 2: Frontend (Static Site)**
   - Root directory: `frontend`
   - Build: `npm install && npm run build`
   - Publish: `dist`

2. **Update Frontend to Proxy API**
   - In `vite.config.ts`, add proxy config:
   ```typescript
   server: {
     proxy: {
       '/api': {
         target: 'https://your-backend-service.onrender.com',
         changeOrigin: true
       }
     }
   }
   ```

---

### **Option 3: Docker-Based Deployment (Most Flexible)**

#### Platform Options:
- **Fly.io** - Great Docker support, global edge locations
- **DigitalOcean App Platform** - Simple, reliable
- **AWS App Runner** - AWS ecosystem integration
- **Google Cloud Run** - Pay per use, auto-scaling

#### Setup for Fly.io:

1. **Create Dockerfile for Combined Deployment**
   See `Dockerfile.combined` (needs to be created)

2. **Create fly.toml**
   ```toml
   app = "your-app-name"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile.combined"

   [[services]]
     internal_port = 8000
     protocol = "tcp"
     [[services.ports]]
       handlers = ["http"]
       port = 80
     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443
   ```

3. **Deploy**
   ```bash
   flyctl deploy
   ```

---

## 🔧 Required Configuration Updates

### 1. Update Frontend API URL

Create/update `frontend/.env.production`:
```env
VITE_API_URL=https://your-backend-url.railway.app
VITE_APPWRITE_ENDPOINT=https://cloud.appwrite.io/v1
VITE_APPWRITE_PROJECT_ID=your_project_id
```

### 2. Update Backend CORS Settings

In `api_server.py`, update CORS to allow your frontend domain:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-frontend.vercel.app", "http://localhost:5173"]
    }
})
```

### 3. Update Dockerfile (if needed)

Your current Dockerfile only handles backend. You may want a combined one or separate builds.

---

## 🌟 Recommended Choice for Quick Start

**Best for beginners**: **Vercel (frontend) + Railway (backend)**

**Reasons**:
- ✅ Easiest setup (both have excellent GitHub integration)
- ✅ Free tiers are generous
- ✅ Automatic SSL certificates
- ✅ Great developer experience
- ✅ Good documentation

**Estimated Setup Time**: 15-30 minutes

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Vercel** | ✅ Excellent | $20/month | Frontend hosting |
| **Netlify** | ✅ Excellent | $19/month | Frontend hosting |
| **Railway** | ⚠️ Limited hours | $5-20/month | Backend hosting |
| **Render** | ⚠️ Spins down | $7/month | Full-stack hosting |
| **Fly.io** | ⚠️ Limited | Pay-as-you-go | Docker/Global edge |

---

## 📝 Pre-Deployment Checklist

- [ ] Build frontend locally: `cd frontend && npm run build`
- [ ] Test backend API: `python api_server.py` (locally)
- [ ] Set up Appwrite project and get credentials
- [ ] Configure all environment variables
- [ ] Update CORS settings for production domain
- [ ] Test API endpoints with frontend
- [ ] Set up error monitoring (optional: Sentry)

---

## 🚀 Quick Deploy Commands

### Vercel (Frontend)
```bash
cd frontend
npm i -g vercel
vercel
```

### Railway (Backend)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

---

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Use platform secrets management
3. **CORS**: Restrict to your production domains only
4. **Rate Limiting**: Consider adding rate limits for public APIs
5. **SSL**: All modern platforms provide SSL by default

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)
- [Fly.io Documentation](https://fly.io/docs)

---

## 🆘 Troubleshooting

### Frontend can't reach backend
- Check CORS settings
- Verify API URL in frontend env vars
- Check backend is running and accessible

### Backend won't start
- Verify all environment variables are set
- Check Python version compatibility (3.11)
- Review platform logs for errors

### Build failures
- Ensure all dependencies are in `package.json` (frontend) and `requirements.txt` (backend)
- Check Node.js version compatibility
- Verify build commands are correct

---

**Need help?** Check platform-specific documentation or open an issue!

