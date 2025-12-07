# Vercel Setup - Step by Step Guide

## 🎯 What You're Looking At

This is Vercel's **project configuration page** where you configure how your app gets deployed. You need to fix two things before clicking "Deploy".

---

## ✅ Correct Settings

### 1. Framework Preset

**Current:** `Flask` ❌  
**Change to:** `Vite` ✅

**How:**
- Click the dropdown next to "Framework Preset"
- Select **"Vite"** (or "Other" if Vite isn't in the list)
- This tells Vercel you're using Vite (which is correct for your React app)

### 2. Root Directory ⭐ MOST IMPORTANT

**Current:** `./` ❌  
**Change to:** `frontend` ✅

**How:**
1. Click the **"Edit"** button next to "Root Directory"
2. Change the value from `./` to `frontend`
3. Press Enter or click outside the field

**Why:** Your frontend code is in the `frontend` folder, not the root directory.

### 3. Build and Output Settings

After changing Root Directory, expand this section (click the arrow) and verify:

- **Build Command:** `npm run build` (should auto-fill)
- **Output Directory:** `dist` (should auto-fill)
- **Install Command:** `npm install` (should auto-fill)

If these don't auto-fill, manually enter:
```
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### 4. Environment Variables

Expand this section and add:

```
VITE_API_URL=https://your-backend-url.railway.app/api
VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
VITE_APPWRITE_PROJECT_ID=692598380015d5816b7e
VITE_APPWRITE_DATABASE_ID=job-market-db
```

⚠️ **Note:** Replace `your-backend-url` with your actual backend URL once it's deployed.

For now, you can:
- Skip this step and add them later in Settings
- Or use placeholder: `VITE_API_URL=http://localhost:8000/api`

---

## 📸 Visual Checklist

Before clicking "Deploy", verify:

```
✅ Framework Preset: Vite (not Flask)
✅ Root Directory: frontend (not ./)
✅ Build Command: npm run build
✅ Output Directory: dist
✅ Install Command: npm install
```

---

## 🚀 After Configuration

1. **Click "Deploy"** button at the bottom
2. Wait 1-2 minutes for the build
3. Your app will be live!

---

## 🔍 If Something Goes Wrong

If you've already deployed with wrong settings:

1. Go to **Settings** → **General**
2. Find **Root Directory** setting
3. Change it to `frontend`
4. Go to **Deployments** tab
5. Click **⋯** (three dots) → **Redeploy**

---

## ⚠️ Important Notes

- **Don't deploy with Root Directory as `./`** - This will cause 404 errors
- **Don't use Flask preset** - Your frontend is React/Vite, not Flask
- **You can add environment variables later** - They can be added after deployment in Settings

---

## 🎉 Once Deployed

Your app will be available at:
`https://job-market-agent.vercel.app`

(Or whatever URL Vercel assigns)

Good luck! 🚀



