# Deployment & Configuration Guide

## ⚠️ SECURITY ALERT

**EXPOSED API KEY DETECTED IN .env FILE**

If you've already committed or deployed with an exposed OpenAI API key, follow these steps immediately:

1. **Revoke the compromised key:**
   - Go to https://platform.openai.com/api-keys
   - Find and delete any exposed keys (check Git history or `.env` backups)

2. **Generate a new API key:**
   - Create a new key at the same link above
   - Update your `.env` file with the new key

3. **Clear Git history (if necessary):**
   ```bash
   # If pushed to GitHub with exposed key, use git-filter-repo
   git filter-repo --replace-text <(echo "old-key==>new-key")
   ```

---

## Configuration Setup

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env` file:**
   ```bash
   # Copy from .env.example (if available) or create new:
   API_BASE_URL=http://localhost:8000
   OPENAI_API_KEY=your-new-api-key-here
   CHROMA_DB_PATH=./chroma_db
   CHROMA_COLLECTION_NAME=research_documents
   API_HOST=127.0.0.1
   API_PORT=8000
   FRONTEND_PORT=8501
   ```

3. **Start the backend:**
   ```bash
   python app/main.py
   # or with uvicorn:
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Start the Streamlit frontend (in another terminal):**
   ```bash
   streamlit run frontend/app_enhanced.py --server.port 8501
   ```

### Production Deployment (Render/Heroku/Railway)

#### Step 1: Backend Deployment

**On Render:**
1. Connect your GitHub repo
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - `CHROMA_DB_PATH=/tmp/chroma_db`
   - `OPENAI_API_KEY=your-new-key`
6. Deploy

**Backend URL example:** `https://ai-research-assistant-backend.onrender.com`

#### Step 2: Frontend Deployment

**On Render (Streamlit):**
1. Create another Web Service
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `streamlit run frontend/app_enhanced.py --server.port $PORT --server.address 0.0.0.0`
4. Add environment variables:
   - `API_BASE_URL=https://ai-research-assistant-backend.onrender.com`
   - `STREAMLIT_SERVER_PORT=8501`

**Or use Streamlit Cloud (recommended for Streamlit apps):**
1. Push code to GitHub
2. Go to https://share.streamlit.io/
3. Deploy repo
4. Add secrets in Streamlit dashboard:
   ```
   # .streamlit/secrets.toml
   API_BASE_URL = "https://your-backend-url.onrender.com"
   OPENAI_API_KEY = "your-new-key"
   ```

---

## API Configuration Reference

| Environment Variable | Local | Production | Purpose |
|---|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | `https://your-api-url.onrender.com` | Backend API endpoint |
| `OPENAI_API_KEY` | `sk-your-new-key` | `sk-your-new-key` | OpenAI authentication |
| `CHROMA_DB_PATH` | `./chroma_db` | `/tmp/chroma_db` | Vector database storage |
| `API_PORT` | `8000` | `$PORT` | Backend port |
| `FRONTEND_PORT` | `8501` | `$PORT` | Streamlit port |

---

## Troubleshooting Upload/Chunk/Analyze/Embed Issues

### Issue: "Backend Offline" Error

**Solution:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8000
   ```

2. Check `API_BASE_URL` in `.env` is correct

3. For deployed version, ensure:
   - Frontend `API_BASE_URL` points to correct backend URL
   - Backend is publicly accessible
   - No CORS issues

### Issue: Upload Fails

**Check:**
- File size < 50MB (configurable in `.env`)
- File type is `.pdf` or `.txt`
- Backend `/api/v1/documents/upload` endpoint is working:
  ```bash
  curl -X POST http://localhost:8000/api/v1/documents/upload
  ```

### Issue: Chunk/Analyze/Embed Not Working

**Solution:**
1. Ensure document was uploaded successfully
2. Check backend logs for errors
3. Verify document ID is valid
4. Test endpoints directly:
   ```bash
   # Chunk document
   curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/chunk
   
   # Analyze document
   curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/analyze
   ```

### Issue: Streamlit can't find modules

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## Docker Deployment

**Build and run with Docker Compose:**
```bash
docker-compose up --build
```

**Environment variables:** Edit `.env` file before building, or pass via `docker-compose.override.yml`

---

## Quick Checklist

- [ ] Revoked exposed API key from OpenAI
- [ ] Generated new API key and updated `.env`
- [ ] `.env` file is in `.gitignore` (not committed)
- [ ] `python-dotenv` is installed (`pip install python-dotenv`)
- [ ] Backend runs on `http://localhost:8000`
- [ ] Frontend loads `.env` variables with `load_dotenv()`
- [ ] API responses are tested with curl/Postman
- [ ] Frontend and backend can communicate

---

## Next Steps

1. Update `.env` with your new API key
2. Test locally first
3. Deploy backend
4. Deploy frontend with correct `API_BASE_URL`
5. Test all features (Upload → Chunk → Analyze → Embed → Ask)
