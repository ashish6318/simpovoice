# 🚀 Deploying SimploVoice to Streamlit Cloud

## Quick Deploy Steps

### 1. **Push Latest Changes to GitHub**
```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### 2. **Go to Streamlit Cloud**
Visit: https://share.streamlit.io/

### 3. **Sign In**
- Click "Sign in" with your GitHub account
- Authorize Streamlit to access your repositories

### 4. **Deploy New App**
- Click "New app" button
- Select:
  - **Repository:** `ashish6318/simpovoice`
  - **Branch:** `main`
  - **Main file path:** `app.py`

### 5. **Add Secrets (Important!)**
Before deploying, add your environment variables:
- Click "Advanced settings"
- In the "Secrets" section, add:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```
*(Replace with your actual Groq API key from your `.env` file)*

### 6. **Deploy!**
- Click "Deploy" button
- Wait 2-3 minutes for deployment
- Your app will be live at: `https://simpovoice.streamlit.app`

---

## Important Notes

### ✅ Works on Streamlit Cloud:
- Web Speech API (voice input in browser)
- Text-to-Speech (Edge-TTS)
- Database (SQLite)
- All NLU and response features
- Analytics dashboard

### ⚠️ Limitations:
- PyAudio removed (not needed - using Web Speech API)
- Voice input requires Chrome/Edge browser
- Users need to allow microphone permissions

### 🔧 If Deployment Fails:
1. Check "Manage app" → "Logs" for errors
2. Verify `requirements.txt` has correct package names
3. Ensure `.env` secrets are added in Streamlit Cloud settings
4. Check that `app.py` is in root directory

---

## Post-Deployment Checklist

- [ ] Test voice input (click microphone icon)
- [ ] Verify TTS audio plays
- [ ] Check database queries work
- [ ] Test all 9 intents
- [ ] Verify analytics dashboard loads
- [ ] Share link with Simplotel! 🎉

---

## Custom Domain (Optional)

Once deployed, you can set up a custom domain:
1. Go to app settings
2. Click "Custom domain"
3. Follow DNS configuration steps

---

**Your app will be live at:**
`https://simpovoice.streamlit.app` (or custom URL you choose)

**Deployment time:** ~2-3 minutes ⚡
