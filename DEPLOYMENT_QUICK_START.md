# Quick Start Deployment Guide

## 🚀 Fastest Path to Production

**Recommended: Vercel (Frontend) + Railway (Backend)**

### Step 1: Deploy Backend (Railway) - ~10 minutes

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment Variables**
   In Railway dashboard → Variables tab, add:
   ```
   PORT=8000
   GOOGLE_API_KEY=your_google_api_key
   APPWRITE_API_ENDPOINT=https://fra.cloud.appwrite.io/v1
   APPWRITE_PROJECT_ID=692598380015d5816b7e
   APPWRITE_API_KEY=your_appwrite_key
   ```

4. **Get Your Backend URL**
   - Railway will auto-deploy
   - Get URL from the service (e.g., `https://your-app.up.railway.app`)
   - Copy this URL for frontend config

---

### Step 2: Deploy Frontend (Vercel) - ~5 minutes

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Import Project**
   - Click "Add New" → "Project"
   - Import your GitHub repository
   - Set root directory: `frontend`

3. **Configure Build Settings**
   - Framework Preset: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

4. **Add Environment Variables**
   ```
   VITE_API_URL=https://your-backend-url.up.railway.app/api
   VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
   VITE_APPWRITE_PROJECT_ID=692598380015d5816b7e
   VITE_APPWRITE_DATABASE_ID=job-market-db
   ```
   ⚠️ **Important**: Replace `your-backend-url` with your actual Railway URL from Step 1

5. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Your app will be live! 🎉

---

## ✅ Verify Deployment

1. **Check Backend Health**
   - Visit: `https://your-backend-url.up.railway.app/health`
   - Should return: `{"status": "healthy"}`

2. **Check Frontend**
   - Visit your Vercel URL
   - Should load the React app

3. **Test Full Flow**
   - Upload a CV
   - Search for jobs
   - Generate applications

---

## 🔧 Alternative: Single Platform (Render)

If you prefer one platform for everything:

### Render.com Setup

1. **Create Two Services in Render**

   **Service 1: Backend**
   - Type: Web Service
   - Environment: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn api_server:app --bind 0.0.0.0:$PORT`

   **Service 2: Frontend**
   - Type: Static Site
   - Build: `cd frontend && npm install && npm run build`
   - Publish: `frontend/dist`

2. **Environment Variables** (same as above)

3. **Update Frontend API URL** to point to Render backend URL

---

## 📝 Pre-Deployment Checklist

- [ ] Appwrite project is set up and accessible
- [ ] Google API key is ready
- [ ] All environment variables documented
- [ ] Tested locally first
- [ ] CORS settings updated (if needed)

---

## 🆘 Common Issues

### Backend won't start
- ✅ Check all environment variables are set
- ✅ Verify Python version (3.11)
- ✅ Check Railway/Render logs

### Frontend can't reach backend
- ✅ Verify `VITE_API_URL` includes `/api` at the end
- ✅ Check CORS settings in `api_server.py`
- ✅ Ensure backend is running and accessible

### Build fails
- ✅ Check Node.js version (18+)
- ✅ Ensure all dependencies are in `package.json`
- ✅ Review build logs for specific errors

---

## 🔗 Useful Links

- [Railway Dashboard](https://railway.app/dashboard)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Render Dashboard](https://dashboard.render.com)

---

**Total Deployment Time**: ~15 minutes  
**Cost**: Free tier available on both platforms

Good luck! 🚀



