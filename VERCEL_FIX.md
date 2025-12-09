# Fixing Vercel 404 Error

## 🔧 Quick Fix for Your 404 Error

Your Vercel deployment is showing a 404 because the project settings need to be configured correctly. Here's how to fix it:

### ⚠️ IMPORTANT: During Initial Setup

If you're importing the project for the first time, you'll see a configuration page. Make sure to:

1. **Change Framework Preset**
   - Currently shows: `Flask` ❌
   - Change to: `Vite` or `Other` ✅
   
2. **Change Root Directory**
   - Currently shows: `./` ❌
   - Click "Edit" and change to: `frontend` ✅
   - This tells Vercel to deploy from the `frontend` folder

### Step 1: Update Vercel Project Settings

1. **Go to Vercel Dashboard**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click on your `job-market-agent` project

2. **Navigate to Settings**
   - Click on the **Settings** tab
   - Scroll down to **Build & Development Settings**

3. **Configure Root Directory**
   - Set **Root Directory** to: `frontend`
   - This tells Vercel to treat the `frontend` folder as the project root

4. **Verify Build Settings**
   - **Framework Preset**: `Vite` (should auto-detect)
   - **Build Command**: `npm run build` (should auto-fill)
   - **Output Directory**: `dist` (should auto-fill)
   - **Install Command**: `npm install` (should auto-fill)

5. **Save Changes**
   - Click **Save** at the bottom

### Step 2: Verify Environment Variables

1. Go to **Settings** → **Environment Variables**
2. Make sure you have these set:
   ```
   VITE_API_URL=https://your-backend-url.railway.app/api
   VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
   VITE_APPWRITE_PROJECT_ID=your_project_id
   VITE_APPWRITE_DATABASE_ID=your_database_id
   ```
   ⚠️ Replace `your-backend-url` with your actual backend URL

### Step 3: Redeploy

1. Go to the **Deployments** tab
2. Click the **⋯** (three dots) menu on the latest deployment
3. Click **Redeploy**
4. Wait for the build to complete

---

## ✅ What Changed

I've updated `vercel.json` to work correctly when the Root Directory is set to `frontend`. The configuration now:

- Uses relative paths (since root is already `frontend`)
- Adds a rewrite rule to serve `index.html` for all routes (needed for React Router)
- Includes security headers

---

## 🎯 Visual Guide

**In Vercel Settings → Build & Development Settings:**

```
Root Directory:        frontend
Framework Preset:      Vite
Build Command:         npm run build
Output Directory:      dist
Install Command:       npm install
```

---

## 🔍 If Still Not Working

### Check Build Logs

1. Go to **Deployments** tab
2. Click on the failed/latest deployment
3. Check the **Build Logs** section
4. Look for errors like:
   - "Cannot find module"
   - "Build failed"
   - "Output directory not found"

### Common Issues

**Issue 1: Build Command Failing**
- Make sure `package.json` is in the `frontend` directory
- Verify all dependencies are listed in `package.json`

**Issue 2: Output Directory Not Found**
- The build should create `frontend/dist` directory
- Check if TypeScript compilation is failing

**Issue 3: Environment Variables Missing**
- Frontend might fail silently if env vars are missing
- Check the browser console for API errors

### Manual Fix Steps

If automatic detection isn't working:

1. **Delete and Recreate Project** (last resort)
   - Delete the current Vercel project
   - Create a new one from the same GitHub repo
   - During setup, manually set Root Directory to `frontend`

2. **Check Repository Structure**
   - Verify your repo structure matches:
     ```
     Job-Market-Agent/
     ├── frontend/
     │   ├── package.json
     │   ├── vite.config.ts
     │   └── ...
     └── vercel.json
     ```

---

## 📝 Summary

The main fix is:
1. ✅ Set **Root Directory** to `frontend` in Vercel project settings
2. ✅ Verify environment variables are set
3. ✅ Redeploy

After these steps, your app should work! 🚀

---

## 🆘 Still Need Help?

Check:
- [Vercel Documentation](https://vercel.com/docs)
- [Vite Deployment Guide](https://vitejs.dev/guide/static-deploy.html#vercel)

Or check your deployment logs for specific error messages.

