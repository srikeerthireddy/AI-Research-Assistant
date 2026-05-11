# AI Research Assistant - Complete Setup Guide

## 🎯 Overview
Production-grade Multi-Agent RAG System with Phases 4-8 fully implemented.

## 📋 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Frontend (Port 8501)              │
│  Dashboard | Upload | Q&A | Summarize | Quiz | Citations   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
├─────────────────────────────────────────────────────────────┤
│ API Endpoints:                                              │
│ • /api/documents/upload     → Document ingestion            │
│ • /api/ask                  → Question answering            │
│ • /api/summary              → Document summarization        │
│ • /api/quiz                 → Quiz generation               │
│ • /api/citations            → Citation management           │
└────────────┬──────────────────────────────────┬─────────────┘
             │                                  │
             ▼                                  ▼
┌──────────────────────────────┐    ┌─────────────────────────┐
│     LangGraph Workflow       │    │  Vector Database        │
├──────────────────────────────┤    │  (Chroma DB)            │
│ Orchestration:               │    ├─────────────────────────┤
│ • Parse Request              │    │ Storage:                │
│ • Route to Agent             │    │ • ./chroma_db           │
│ • Research Agent             │    │ • Persistent storage    │
│ • Summarizer Agent           │    │ • Cosine similarity     │
│ • Quiz Agent (approval)      │    │ • 384-dim embeddings    │
│ • Citation Agent             │    │ • Full-text search      │
│ • Format Output              │    └─────────────────────────┘
└────────┬──────────────────┬──┘
         │                  │
         ▼                  ▼
    ┌────────────┐    ┌──────────────────┐
    │ Retriever  │    │ Embeddings       │
    │ (Semantic) │    │ (sentence-       │
    │ Search     │    │  transformers)   │
    └────────────┘    └──────────────────┘
         │                  │
         └─────────┬────────┘
                   ▼
          ┌─────────────────┐
          │  OpenAI GPT     │
          │  (Generation)   │
          └─────────────────┘
```

## 🚀 Quick Start

### 1️⃣ Install Dependencies
```bash
cd S:\AI-Research-Assistant\ai-research-assistant
pip install -r requirements.txt
```

### 2️⃣ Configure Environment
Create `.env` file:
```
OPENAI_API_KEY=your_key_here
API_HOST=127.0.0.1
API_PORT=8000
FRONTEND_PORT=8501
MAX_FILE_SIZE_MB=50
```

### 3️⃣ Start Backend (Terminal 1)
```bash
cd S:\AI-Research-Assistant\ai-research-assistant
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### 4️⃣ Start Frontend (Terminal 2)
```bash
cd S:\AI-Research-Assistant\ai-research-assistant
streamlit run frontend/app.py
```

Browser will open to: http://localhost:8501

## 📋 Phases Implemented

### ✅ Phase 4: Embeddings
- **Service**: `EmbeddingsService` (app/services/embeddings.py)
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Methods**:
  - `embed_text()` - Single text embedding
  - `embed_texts()` - Batch embedding
  - `similarity()` - Cosine similarity

### ✅ Phase 5: Vector Database
- **Service**: `ChromaVectorDB` (app/database/chroma_db.py)
- **Storage**: ./chroma_db (persistent)
- **Methods**:
  - `add_chunks()` - Store embeddings
  - `search()` - Semantic search
  - `delete_document()` - Document removal

### ✅ Phase 6: Retrieval
- **Service**: `RetrieverService` (app/services/retriever.py)
- **Features**:
  - `retrieve()` - Get top-k relevant chunks
  - `retrieve_and_format()` - Format for LLM
  - `retrieve_batch()` - Multiple queries

### ✅ Phase 7: Generation
- **Service**: `GeneratorService` (app/services/generator.py)
- **Features**:
  - `generate_answer()` - Context-constrained generation
  - `generate_summary()` - Auto-summarization
  - `generate_quiz_questions()` - MCQ generation
  - `extract_topics()` - Topic extraction
- **Hallucination Prevention**: Only answers from retrieved context

### ✅ Phase 8: Multi-Agent System
- **Research Agent**: Answer queries, compare docs, cross-document search
- **Summarizer Agent**: Document summaries, key point extraction
- **Quiz Agent**: Quiz generation with **human-in-the-loop** approval
- **Citation Agent**: Citation management and bibliography

## 🎯 Frontend Navigation

### Dashboard
- System status
- Quick stats (docs, agents, features)
- Recent documents
- Quick action guide

### Upload
- Upload PDF/TXT files
- Auto-embedding to vector DB
- Status tracking

### Manage Docs
- List all documents
- View metadata (size, upload date)
- Delete documents

### Ask Question
- Semantic search with RAG
- Document filtering (optional)
- Retrieve top-k results
- Citation tracking
- Similarity scores

### Summarize
- Select document
- Choose length (concise/moderate/detailed)
- Auto-generate summary

### Generate Quiz
- Select document
- Set number of questions
- Human-in-the-loop approval workflow
- Preview questions
- Approve/reject functionality

### Citations
- Query-based citation retrieval
- Source tracking
- Relevance scoring

### About
- System information
- Tech stack details
- Feature highlights

## 🔌 API Endpoints

### Document Management
```
POST   /api/documents/upload
GET    /api/documents
GET    /api/documents/{document_id}
DELETE /api/documents/{document_id}
```

### RAG Pipeline
```
POST   /api/documents/{document_id}/analyze    # Full analysis
POST   /api/ask                                 # Q&A with citations
POST   /api/summary                             # Summarization
POST   /api/quiz                                # Quiz generation
GET    /api/quiz/pending                        # Pending approvals
POST   /api/quiz/{quiz_id}/approve              # Approval workflow
POST   /api/citations                           # Citation retrieval
```

## 📝 Example Usage

### 1. Upload Document
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf"
```

### 2. Ask Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics?",
    "document_id": "optional-doc-id",
    "top_k": 5
  }'
```

### 3. Generate Summary
```bash
curl -X POST http://localhost:8000/api/summary \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-doc-id",
    "length": "moderate"
  }'
```

### 4. Generate Quiz
```bash
curl -X POST http://localhost:8000/api/quiz \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "your-doc-id",
    "num_questions": 5,
    "require_approval": true
  }'
```

### 5. Approve Quiz
```bash
curl -X POST http://localhost:8000/api/quiz/quiz_id/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/
```

### List Documents
```bash
curl http://localhost:8000/api/documents
```

### Test Q&A (Python)
```python
import requests
import time

base = 'http://127.0.0.1:8000'
doc_id = 'your-document-id'

# Ask question
response = requests.post(
    f'{base}/api/ask',
    json={
        "query": "What are the main topics?",
        "document_id": doc_id,
        "top_k": 5
    },
    timeout=180
)

print(response.json())
```

## 📊 System Performance

- **Embedding**: ~100ms per chunk
- **Retrieval**: ~50ms for semantic search
- **Generation**: ~2-5s per answer (LLM dependent)
- **Total Q&A latency**: ~2-6s
- **Quiz generation**: ~5-10s

## 🔐 Security Notes

- All API endpoints have CORS enabled (configurable)
- Max file size: 50MB (configurable in .env)
- No authentication required (add in production)
- Document storage: ./uploads/
- Vector DB: ./chroma_db/

## 🚀 Deployment

### Production Checklist
- [ ] Set strong `OPENAI_API_KEY`
- [ ] Disable CORS for production domains
- [ ] Configure MAX_FILE_SIZE_MB
- [ ] Setup database backups (chroma_db/)
- [ ] Add authentication/authorization
- [ ] Enable HTTPS/SSL
- [ ] Configure rate limiting
- [ ] Setup monitoring & logging
- [ ] Deploy backend to Render/Railway
- [ ] Deploy frontend to Streamlit Cloud/Vercel

### Render Deployment (Backend)
```bash
# Create render.yaml
services:
  - type: web
    name: ai-research-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        scope: run
```

### Streamlit Cloud Deployment (Frontend)
```bash
# Commit to GitHub, connect to Streamlit Cloud
# Set secrets in Streamlit dashboard
```

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python version
python --version  # Requires 3.9+

# Check dependencies
pip install -r requirements.txt --upgrade

# Check port
netstat -an | findstr :8000
```

### Frontend Can't Connect
```bash
# Ensure backend is running
curl http://localhost:8000/

# Check CORS
# Check API_BASE_URL in frontend/app.py
```

### Quiz Approval Not Working
```bash
# Check pending quizzes
curl http://localhost:8000/api/quiz/pending

# Approve quiz
curl -X POST http://localhost:8000/api/quiz/{quiz_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### Embeddings Not Generated
```bash
# Check sentence-transformers installation
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Check chroma_db directory
ls -la ./chroma_db/
```

## 📚 Key Files

```
app/
├── main.py                 # FastAPI entry point
├── config.py              # Configuration
├── agents/                # Multi-agent system
│   ├── research_agent.py
│   ├── summarizer_agent.py
│   ├── quiz_agent.py
│   └── citation_agent.py
├── services/              # Core services
│   ├── embeddings.py      # Phase 4
│   ├── retriever.py       # Phase 6
│   ├── generator.py       # Phase 7
│   ├── pdf_parser.py
│   ├── chunker.py
│   └── document_service.py
├── database/
│   └── chroma_db.py       # Phase 5
└── rag/
    └── workflow.py        # Phase 8 - LangGraph

frontend/
└── app.py                 # Streamlit UI

requirements.txt           # Python dependencies
```

## 🎓 Learning Path

1. **Start**: Upload a PDF document
2. **Explore**: Manage documents, view storage
3. **Learn**: Ask questions about content
4. **Summarize**: Generate automatic summaries
5. **Create**: Build quizzes with approval
6. **Track**: View citations and sources
7. **Extend**: Add custom agents/workflows

## 💡 Next Steps

1. **Data Visualization**: Add charts for retrieval stats
2. **Web Search**: Integrate web search tools
3. **Streaming**: Add streaming responses
4. **Multilingual**: Add translation support
5. **Voice**: Add speech-to-text input
6. **Document Comparison**: Add advanced comparison features
7. **Analytics**: Add usage analytics dashboard

## 📞 Support

- Check logs: Backend logs in terminal
- Frontend errors: Browser console (F12)
- API errors: Check response JSON for error details
- Rate limiting: Check request timeouts (TIMEOUT_LONG)

---

**Version**: 1.0  
**Last Updated**: May 2026  
**Status**: Production Ready
