# Environment Setup Quick Reference

## CRITICAL: Revoke Compromised API Key ⚠️

Your OpenAI API key was previously exposed. **Revoke it immediately:**

1. **Visit:** https://platform.openai.com/api-keys
2. **Delete:** Any exposed API keys (check Git history for details)
3. **Create:** A new API key
4. **Update:** `.env` file with the new key

```bash
# Update .env with NEW key:
OPENAI_API_KEY=sk-your-new-key-here
```

---

## Local Development Setup

### 1. Install Requirements
```bash
cd ai-research-assistant
pip install -r requirements.txt
```

### 2. Verify Environment Variables

**Check your `.env` file includes:**
```env
API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-your-new-key-here
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=research_documents
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_PORT=8501
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,txt
```

### 3. Start Backend
```bash
# Terminal 1
cd ai-research-assistant
python app/main.py

# Or with explicit port:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Start Frontend (New Terminal)
```bash
# Terminal 2
cd ai-research-assistant
streamlit run frontend/app_enhanced.py --server.port 8501
```

### 5. Access Application
- **Frontend:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Production Deployment (Render/Railway/Heroku)

### Backend Setup (Render Example)

1. **Create Web Service**
   - Connect GitHub repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Add Environment Variables**
   ```
   CHROMA_DB_PATH=/tmp/chroma_db
   OPENAI_API_KEY=sk-your-new-key-here
   ```

3. **Deploy**
   - Note the backend URL: `https://ai-research-assistant-backend.onrender.com`

### Frontend Setup (Streamlit Cloud Recommended)

1. **Push `.streamlit/secrets.toml` to GitHub** (contains sensitive config)
   ```toml
   API_BASE_URL = "https://ai-research-assistant-backend.onrender.com"
   OPENAI_API_KEY = "sk-your-new-key-here"
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Connect GitHub repo
   - Select `frontend/app_enhanced.py` as main file
   - Streamlit automatically reads `.streamlit/secrets.toml`

3. **Or Deploy on Render**
   - Create Web Service
   - Set start command: `streamlit run frontend/app_enhanced.py --server.port $PORT --server.address 0.0.0.0`
   - Add env vars same as local

---

## Troubleshooting

### "Backend Offline" in Streamlit

**Fix:**
1. Check backend is running: `curl http://localhost:8000`
2. Verify `API_BASE_URL` in `.env` matches backend URL
3. For cloud: ensure backend URL is accessible (no 404/403)

### Upload/Chunk/Analyze Not Working

**Debug steps:**
```bash
# Test backend health
curl http://localhost:8000/

# Test upload endpoint
curl -X POST http://localhost:8000/api/v1/documents/upload -F "file=@test.pdf"

# Test with document ID (get from upload response)
curl -X POST http://localhost:8000/api/v1/documents/{doc_id}/chunk

# View API docs in browser
# http://localhost:8000/docs
```

### Streamlit can't load dotenv

**Fix:**
```bash
# Reinstall python-dotenv
pip install --upgrade python-dotenv

# Force reinstall all packages
pip install -r requirements.txt --force-reinstall
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
python app/main.py --port 8001
streamlit run frontend/app_enhanced.py --server.port 8502
```

---

## File Structure

```
ai-research-assistant/
├── .env                      # ← Configuration (NEVER commit!)
├── .env.example             # ← Template for .env
├── .gitignore               # ← Includes .env
├── .streamlit/
│   └── secrets.toml         # ← Streamlit Cloud secrets
├── requirements.txt         # ← All dependencies
├── app/
│   ├── main.py             # ← FastAPI backend entry
│   ├── api/
│   │   └── documents_routes.py
│   ├── services/
│   │   ├── pdf_parser.py
│   │   ├── chunker.py
│   │   └── document_service.py
│   └── ...
├── frontend/
│   └── app_enhanced.py     # ← Streamlit frontend entry
└── DEPLOYMENT_SETUP.md     # ← Full deployment guide
```

---

## Environment Variables Reference

| Variable | Local | Production | Notes |
|---|---|---|---|
| `API_BASE_URL` | `http://localhost:8000` | `https://your-api.onrender.com` | **Critical:** Must be correct for features to work |
| `OPENAI_API_KEY` | `sk-your-key` | `sk-your-key` | **Do NOT commit** |
| `CHROMA_DB_PATH` | `./chroma_db` | `/tmp/chroma_db` | Vector DB storage |
| `MAX_FILE_SIZE_MB` | `50` | `50` | Upload size limit |

---

## Testing Upload/Chunk/Analyze Workflow

```bash
# 1. Start backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. In new terminal, test upload
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample.pdf"

# Response example:
# {
#   "success": true,
#   "document_id": "abc123...",
#   "original_filename": "sample.pdf"
# }

# 3. Test chunk (use document_id from response)
curl -X POST http://localhost:8000/api/v1/documents/abc123.../chunk \
  -H "Content-Type: application/json"

# 4. Test analyze
curl -X POST http://localhost:8000/api/v1/documents/abc123.../analyze \
  -H "Content-Type: application/json"

# 5. Now start Streamlit and test UI
streamlit run frontend/app_enhanced.py --server.port 8501
```

---

## Final Checklist Before Deployment

- [ ] Revoked exposed API key at https://platform.openai.com/api-keys
- [ ] Generated new API key and updated `.env`
- [ ] `.env` is in `.gitignore` (verify with `git status`)
- [ ] `.streamlit/secrets.toml` has production backend URL
- [ ] Backend runs locally without errors
- [ ] Frontend connects to backend (shows "✅ Backend Connected")
- [ ] Upload feature works end-to-end
- [ ] All endpoints tested with curl/Postman
- [ ] No secrets committed to GitHub

---

## Support & Next Steps

1. **Local Development:** Follow "Local Development Setup" above
2. **Deployment:** See `DEPLOYMENT_SETUP.md` for detailed cloud instructions
3. **Issues:** Check `SYSTEM_OVERVIEW.md` for architecture details
4. **API Docs:** Run backend and visit http://localhost:8000/docs

