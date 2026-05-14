# Streamlit Cloud Deployment Guide

## ✅ Fixed: ModuleNotFoundError

The app now gracefully handles missing `python-dotenv` module. Environment variables can be loaded via:
1. `.streamlit/secrets.toml` (Streamlit Cloud recommended)
2. System environment variables
3. Local `.env` file (development only)

---

## Step-by-Step Streamlit Cloud Deployment

### 1. Prepare Your Repository

Ensure these files exist in your GitHub repo:

```
ai-research-assistant/
├── .streamlit/
│   ├── config.toml           ✅ Created
│   └── secrets.toml          ✅ Created
├── frontend/
│   └── app_enhanced.py       ✅ Fixed for Cloud
├── requirements.txt          ✅ Has python-dotenv
└── README.md
```

### 2. Deploy on Streamlit Cloud

1. Go to: https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `srikeerthireddy/AI-Research-Assistant`
5. Select branch: `main` (or your branch)
6. Set main file path: `ai-research-assistant/frontend/app_enhanced.py`
7. Click "Deploy"

### 3. Add Secrets (CRITICAL)

**On Streamlit Cloud Dashboard:**

1. Click your app → Settings (gear icon) → Secrets
2. Add these secrets:

```toml
# Backend API Configuration
API_BASE_URL = "https://your-backend-url.onrender.com"

# OpenAI Configuration
OPENAI_API_KEY = "sk-your-new-key-here"

# Chroma Configuration
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "research_documents"
```

**Replace:**
- `https://your-backend-url.onrender.com` with your actual backend URL
- `sk-your-new-key-here` with your new OpenAI API key

### 4. Verify Deployment

After deployment:
1. Check "Logs" for any errors
2. Reload the app
3. Verify sidebar shows "✅ Backend Connected"
4. Test Upload → Chunk → Analyze workflow

---

## Troubleshooting Streamlit Cloud

### "Backend Offline" Error

**Check:**
1. Backend URL is correct in Secrets
2. Backend service is running and publicly accessible
3. No CORS issues between frontend and backend

**Test:**
```bash
curl https://your-backend-url.onrender.com
```

### Import Errors

**Solution:**
- Requirements are installed from `requirements.txt` automatically
- If specific packages fail, add them to a `packages.txt` file (system packages)

**Example `packages.txt`:**
```
libpdf
libpq-dev
```

### File Upload Not Working

**Check:**
1. `MAX_FILE_SIZE_MB` in secrets
2. Backend `/api/v1/documents/upload` endpoint is accessible
3. File size is under 50MB limit

### Streamlit Won't Load

**Solution:**
1. Check "Advanced Settings" → Python version (recommend 3.11)
2. Restart app from dashboard
3. Check logs for detailed error messages

---

## Best Practices

### ✅ DO:
- Use `.streamlit/secrets.toml` for sensitive data on Streamlit Cloud
- Keep `.env` in `.gitignore` (never commit it)
- Use environment-specific configurations
- Test locally before deploying

### ❌ DON'T:
- Commit `.env` to GitHub
- Hardcode API keys in source code
- Use Secrets for non-sensitive configs (use `config.toml` instead)
- Deploy without testing locally first

---

## Environment Variables

| Variable | Local Dev | Streamlit Cloud | Source |
|---|---|---|---|
| `API_BASE_URL` | `.env` | Secrets | Backend URL |
| `OPENAI_API_KEY` | `.env` | Secrets | OpenAI Platform |
| `CHROMA_DB_PATH` | `.env` | Secrets | Local path |
| Other config | `.env` or `config.toml` | `config.toml` or Secrets | App settings |

---

## Quick Deployment Checklist

- [ ] Backend is deployed and running
- [ ] Backend URL is accessible from public internet
- [ ] New OpenAI API key generated (old one revoked)
- [ ] `.streamlit/secrets.toml` updated with production URLs
- [ ] GitHub repo pushed with all changes
- [ ] Streamlit Cloud app created and linked
- [ ] Secrets added to Streamlit Cloud dashboard
- [ ] App deployed successfully
- [ ] Sidebar shows "✅ Backend Connected"
- [ ] Upload/Chunk/Analyze features tested end-to-end

---

## Useful Links

- **Streamlit Docs:** https://docs.streamlit.io
- **Secrets Management:** https://docs.streamlit.io/develop/api-reference/app-configuration/st.secrets
- **Deployment FAQ:** https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- **Common Issues:** https://docs.streamlit.io/deploy/streamlit-community-cloud/troubleshoot

---

## Need More Help?

1. **Local Testing:** Run `streamlit run frontend/app_enhanced.py`
2. **API Testing:** Postman or curl to test backend endpoints
3. **Logs:** Check Streamlit Cloud "Logs" for error details
4. **Community:** https://discuss.streamlit.io/

