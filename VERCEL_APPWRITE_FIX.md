# Fixing "Failed to fetch" Error on Vercel

## 🔍 The Problem

The "Failed to fetch" error means your frontend can't connect to **Appwrite** (your authentication/database service). This is happening during account registration.

## ✅ Quick Fix Checklist

### 1. Check Vercel Environment Variables

Go to your Vercel project → **Settings** → **Environment Variables** and verify these are set:

```
VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
VITE_APPWRITE_PROJECT_ID=692598380015d5816b7e
```

⚠️ **Important:** Make sure:
- No trailing slashes (`/v1` not `/v1/`)
- No quotes around values
- Values match exactly (case-sensitive)

### 2. Redeploy After Adding Variables

**After adding/changing environment variables:**
1. Go to **Deployments** tab
2. Click **⋯** (three dots) on latest deployment
3. Click **Redeploy**
4. Wait for build to complete

**Why?** Environment variables are only available after a new deployment.

---

## 🔧 Detailed Troubleshooting

### Issue 1: Environment Variables Not Set

**Symptoms:**
- Error: "Failed to fetch"
- Appwrite calls fail

**Fix:**
1. Go to Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
2. Add these variables:
   ```
   VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
   VITE_APPWRITE_PROJECT_ID=692598380015d5816b7e
   VITE_APPWRITE_DATABASE_ID=job-market-db
   ```
3. Make sure they're set for **Production** environment
4. Redeploy

### Issue 2: Wrong Appwrite Configuration

**Check your Appwrite console:**
1. Go to [cloud.appwrite.io](https://cloud.appwrite.io)
2. Verify your Project ID matches `692598380015d5816b7e`
3. Verify your endpoint is `https://fra.cloud.appwrite.io/v1`

**If different:**
- Update environment variables in Vercel
- Use your actual values

### Issue 3: CORS Issues

**If Appwrite is blocking requests:**

1. Go to Appwrite Console → Your Project → **Settings** → **Domains**
2. Add your Vercel domain:
   ```
   job-market-agent.vercel.app
   *.vercel.app
   ```
3. Save changes

### Issue 4: Appwrite Services Not Enabled

**Verify in Appwrite Console:**
1. **Authentication** → Make sure Email/Password is enabled
2. **Databases** → Make sure database exists
3. **Storage** → Make sure buckets exist

---

## 🎯 Step-by-Step Fix

### Step 1: Verify Appwrite Configuration

In your Appwrite dashboard:
1. Check Project ID
2. Check Endpoint URL
3. Check that services are enabled

### Step 2: Set Environment Variables in Vercel

1. Go to: `vercel.com/dashboard/[your-project]/settings/environment-variables`
2. Add each variable:
   - Key: `VITE_APPWRITE_ENDPOINT`
   - Value: `https://fra.cloud.appwrite.io/v1`
   - Environment: `Production` (and Preview/Development if needed)
3. Repeat for:
   - `VITE_APPWRITE_PROJECT_ID` = `692598380015d5816b7e`
   - `VITE_APPWRITE_DATABASE_ID` = `job-market-db`

### Step 3: Add CORS in Appwrite

1. Appwrite Console → Settings → Domains
2. Add: `job-market-agent.vercel.app`
3. Add: `*.vercel.app` (for preview deployments)

### Step 4: Redeploy

1. Vercel → Deployments
2. Click **⋯** → **Redeploy**
3. Wait for completion

---

## 🔍 Debugging

### Check Browser Console

1. Open your app: `job-market-agent.vercel.app`
2. Press `F12` to open DevTools
3. Go to **Console** tab
4. Try registering again
5. Look for error messages

**Common errors:**
- `NetworkError` → CORS issue or wrong endpoint
- `401 Unauthorized` → Wrong project ID
- `404 Not Found` → Wrong endpoint URL

### Check Network Tab

1. DevTools → **Network** tab
2. Try registering
3. Look for failed requests (red)
4. Click on failed request
5. Check:
   - **Request URL** - Should be Appwrite endpoint
   - **Status Code** - Tells you what's wrong
   - **Response** - Error message

---

## ✅ Verification

After fixing, test:

1. ✅ Open app: `job-market-agent.vercel.app`
2. ✅ Open browser console (F12)
3. ✅ Try to register
4. ✅ Should see successful requests (no errors)
5. ✅ Account should be created

---

## 🆘 Common Issues

### "VITE_APPWRITE_ENDPOINT is undefined"

**Cause:** Environment variable not set or not deployed  
**Fix:** Add variable in Vercel and redeploy

### "Network request failed"

**Cause:** CORS or wrong endpoint  
**Fix:** Add domain in Appwrite settings + verify endpoint URL

### "Invalid project ID"

**Cause:** Wrong project ID in environment variables  
**Fix:** Update `VITE_APPWRITE_PROJECT_ID` with correct value

---

## 📝 Quick Reference

**Environment Variables Needed:**
```
VITE_APPWRITE_ENDPOINT=https://fra.cloud.appwrite.io/v1
VITE_APPWRITE_PROJECT_ID=692598380015d5816b7e
VITE_APPWRITE_DATABASE_ID=job-market-db
```

**Appwrite Settings:**
- Add domain: `job-market-agent.vercel.app`
- Enable Email/Password auth
- Create database and collections

---

**Need more help?** Check the browser console for specific error messages!



