# API Key Setup Instructions

## 🚨 Application Failed Due to Missing API Key

The Job Market AI Analyzer requires a **Google Gemini API key** to function. The application tried to run but failed because no valid API key was provided.

## 🔧 Quick Fix

### Option 1: Use the Setup Script (Recommended)

```bash
python setup_api_keys.py
```

This will:
- Guide you through getting an API key
- Create the required `.env` file
- Validate your setup

### Option 2: Manual Setup

1. **Get a Google Gemini API Key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with your Google account
   - Create a new API key
   - Copy the key

2. **Create a `.env` file** in the project root:
   ```bash
   # Create the file
   notepad .env  # or use your preferred editor
   ```

3. **Add your API key to `.env`**:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   CV_FILE_PATH=cvs/CV.pdf
   ```

## 🧪 Test Your Setup

After setting up the API key, test it:

```bash
python main.py
```

## 💡 What the API Key Does

The Google Gemini API key enables:
- 🤖 **AI Profile Analysis** - Analyzes your CV and creates career insights
- 📝 **Cover Letter Generation** - Creates personalized cover letters
- 🎯 **ATS Optimization** - Optimizes resumes for applicant tracking systems
- 💬 **Interview Preparation** - Generates interview questions and responses

## 🆘 Still Having Issues?

If you continue to have problems:

1. **Check your API key is valid** - Test it at https://makersuite.google.com/
2. **Verify the `.env` file** - Make sure it's in the project root directory
3. **Check file permissions** - Ensure the application can read the `.env` file
4. **Restart your terminal/command prompt** - Environment variables need to reload

## 🔒 Security Note

- Never commit your `.env` file to version control
- Keep your API key secret
- The `.env` file is already in `.gitignore`

## 🎯 Next Steps

Once your API key is set up:
1. Run `python main.py` to start the application
2. Upload your CV (or use the sample one)
3. Get AI-powered job matching and career insights!

---

**Need help?** Check the main [README.md](README.md) for more details.
