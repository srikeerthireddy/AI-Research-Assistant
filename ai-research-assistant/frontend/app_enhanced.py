"""
AI Research Assistant - Clean & Modern Frontend
Organized pipeline workflow: Upload → Parse → Chunk → Analyze
"""
import streamlit as st
import requests
import json
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# ==================== Load Environment Variables ====================
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (e.g., on Streamlit Cloud)
    # Environment variables will be loaded from system or Streamlit secrets
    pass

# ==================== Configuration ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_V1_URL = f"{API_BASE_URL}/api/v1/documents"

TIMEOUT_SHORT = 10
TIMEOUT_LONG = 180

# ==================== Page Config ====================
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    h1, h2, h3 {
        font-family: 'DM Serif Display', serif;
        letter-spacing: 0.01em;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(155deg, #0f172a 0%, #164e63 55%, #0f766e 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Main Content */
    .main {
        background:
            radial-gradient(circle at 10% -10%, rgba(20, 184, 166, 0.20), transparent 30%),
            radial-gradient(circle at 90% 0%, rgba(14, 116, 144, 0.18), transparent 38%),
            linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0f766e;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .success-box {
        background: #ecfdf5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    .error-box {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #0f766e;
        margin: 1.5rem 0 0.5rem 0;
        border-bottom: 2px solid #0f766e;
        padding-bottom: 0.5rem;
    }

    .hero-shell {
        background: linear-gradient(120deg, #0f172a 0%, #155e75 52%, #0ea5a3 100%);
        border-radius: 18px;
        padding: 2.2rem;
        margin-bottom: 1.2rem;
        color: white;
        box-shadow: 0 20px 40px rgba(15, 23, 42, 0.22);
        position: relative;
        overflow: hidden;
    }

    .hero-shell::before {
        content: "";
        position: absolute;
        right: -60px;
        top: -60px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(255,255,255,0.28), rgba(255,255,255,0));
    }

    .hero-kicker {
        text-transform: uppercase;
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        opacity: 0.82;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 3rem);
        margin: 0;
        line-height: 1.1;
    }

    .hero-subtitle {
        margin-top: 0.8rem;
        color: rgba(236, 254, 255, 0.92);
        max-width: 740px;
        line-height: 1.5;
    }

    .glass-card {
        border: 1px solid rgba(148, 163, 184, 0.25);
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(6px);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
    }

    .mini-label {
        font-size: 0.74rem;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .mini-value {
        font-size: 1.7rem;
        line-height: 1.1;
        font-weight: 700;
        color: #0f172a;
    }

    .journey-card {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem;
        min-height: 170px;
        box-shadow: 0 8px 14px rgba(15, 23, 42, 0.05);
    }

    .journey-stage {
        font-size: 0.8rem;
        color: #0f766e;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .journey-title {
        margin: 0;
        color: #0f172a;
        font-size: 1.06rem;
        font-weight: 700;
    }

    .journey-meta {
        margin-top: 0.6rem;
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    .focus-card {
        border-radius: 14px;
        border: 1px solid #bfdbfe;
        padding: 1rem;
        background: linear-gradient(120deg, rgba(239, 246, 255, 0.9), rgba(240, 253, 250, 0.9));
        min-height: 132px;
    }

    .focus-title {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
    }

    .focus-text {
        margin-top: 0.55rem;
        font-size: 0.9rem;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "selected_doc" not in st.session_state:
    st.session_state.selected_doc = None


# ==================== Utility Functions ====================
def check_api():
    """Check if backend is online"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_documents() -> Tuple[List[Dict], int]:
    """Fetch all documents"""
    try:
        response = requests.get(f"{API_V1_URL}", timeout=TIMEOUT_SHORT)
        if response.status_code == 200:
            data = response.json()
            return data.get("documents", []), data.get("count", 0)
    except:
        pass
    return [], 0


def upload_file(file_bytes: bytes, filename: str) -> Dict:
    """Upload document"""
    try:
        files = {"file": (filename, file_bytes)}
        response = requests.post(
            f"{API_V1_URL}/upload",
            files=files,
            timeout=TIMEOUT_LONG
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Upload failed"}


def parse_document(doc_id: str) -> Dict:
    """Parse document"""
    try:
        response = requests.post(
            f"{API_V1_URL}/{doc_id}/parse",
            timeout=TIMEOUT_LONG
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Parse failed"}


def chunk_document(
    doc_id: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
    method: str = "fixed",
    preview_count: int = 3
) -> Dict:
    """Chunk document"""
    try:
        response = requests.post(
            f"{API_V1_URL}/{doc_id}/chunk",
            params={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "method": method,
                "preview_count": preview_count
            },
            timeout=TIMEOUT_LONG
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Chunking failed"}


def analyze_document(doc_id: str) -> Dict:
    """Analyze document"""
    try:
        response = requests.post(
            f"{API_V1_URL}/{doc_id}/analyze",
            timeout=TIMEOUT_LONG
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    return {"success": False, "error": "Analysis failed"}


def ask_question(query: str, document_id: Optional[str] = None, top_k: int = 5) -> Dict:
    """Ask a question using the RAG backend"""
    try:
        payload = {
            "query": query,
            "top_k": top_k,
        }
        if document_id:
            payload["document_id"] = document_id

        response = requests.post(
            f"{API_BASE_URL}/api/ask",
            json=payload,
            timeout=TIMEOUT_LONG,
        )

        if response.status_code == 200:
            return response.json()

        try:
            err_payload = response.json()
            error_message = err_payload.get("error") or err_payload.get("detail") or response.text
        except Exception:
            error_message = response.text

        return {"success": False, "error": error_message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_quiz(document_id: str, num_questions: int = 5, require_approval: bool = True) -> Dict:
    """Generate a quiz from a document"""
    try:
        payload = {
            "document_id": document_id,
            "num_questions": num_questions,
            "require_approval": require_approval,
        }

        response = requests.post(
            f"{API_BASE_URL}/api/quiz",
            json=payload,
            timeout=TIMEOUT_LONG,
        )

        if response.status_code == 200:
            return response.json()

        try:
            err_payload = response.json()
            error_message = err_payload.get("error") or err_payload.get("detail") or response.text
        except Exception:
            error_message = response.text

        return {"success": False, "error": error_message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_quiz_from_query(query: str, document_id: Optional[str] = None, num_questions: int = 5) -> Dict:
    """Generate a quiz from an ask-style query or topic prompt"""
    try:
        payload = {
            "query": query,
            "document_id": document_id,
            "num_questions": num_questions,
        }

        response = requests.post(
            f"{API_BASE_URL}/api/quiz/query",
            json=payload,
            timeout=TIMEOUT_LONG,
        )

        if response.status_code == 200:
            return response.json()

        try:
            err_payload = response.json()
            error_message = err_payload.get("error") or err_payload.get("detail") or response.text
        except Exception:
            error_message = response.text

        return {"success": False, "error": error_message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_document(doc_id: str) -> bool:
    """Delete document"""
    try:
        response = requests.delete(
            f"{API_V1_URL}/{doc_id}",
            timeout=TIMEOUT_SHORT
        )
        return response.status_code == 200
    except:
        return False


def format_size(bytes_size: int) -> str:
    """Format file size"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🔬 AI Research Assistant")
    st.caption("Production-Grade Multi-Agent RAG System")
    st.divider()
    
    # API Status
    st.session_state.api_connected = check_api()
    if st.session_state.api_connected:
        st.success("✅ Backend Connected")
    else:
        st.error("❌ Backend Offline")
    
    st.divider()
    
    # Navigation Sections
    st.markdown("<div class='section-header'>📚 Pipeline Workflow</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📤 Upload", use_container_width=True, key="nav_upload"):
            st.session_state.page = "Upload"
            st.rerun()
    with col2:
        if st.button("✂️ Chunk", use_container_width=True, key="nav_chunk"):
            st.session_state.page = "Chunk"
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📊 Analyze", use_container_width=True, key="nav_analyze"):
            st.session_state.page = "Analyze"
            st.rerun()
    with col4:
        if st.button("🔍 Embed", use_container_width=True, key="nav_embed"):
            st.session_state.page = "Embed"
            st.rerun()
    
    st.divider()
    
    st.markdown("<div class='section-header'>🚀 Features</div>", unsafe_allow_html=True)
    
    col5, col6 = st.columns(2)
    with col5:
        if st.button("❓ Ask", use_container_width=True, key="nav_ask"):
            st.session_state.page = "Ask"
            st.rerun()
    with col6:
        if st.button("📝 Summary", use_container_width=True, key="nav_summary"):
            st.session_state.page = "Summary"
            st.rerun()
    
    col7, col8 = st.columns(2)
    with col7:
        if st.button("🎓 Quiz", use_container_width=True, key="nav_quiz"):
            st.session_state.page = "Quiz"
            st.rerun()
    with col8:
        if st.button("🔗 Citations", use_container_width=True, key="nav_citations"):
            st.session_state.page = "Citations"
            st.rerun()
    
    st.divider()
    
    st.markdown("<div class='section-header'>📁 Documents</div>", unsafe_allow_html=True)
    
    documents, count = get_documents()
    st.metric("Total", count)
    
    if documents:
        st.markdown("**Recent Files:**")
        for doc in documents[-5:]:
            filename = doc.get("original_filename", "Unknown")[:20]
            doc_id = doc.get("document_id", "")[:8]
            
            with st.container(border=True):
                st.caption(f"📄 {filename}...")
                st.caption(f"ID: {doc_id}...")
                
                col_view, col_delete = st.columns(2)
                with col_view:
                    if st.button("View", key=f"view_{doc_id}", use_container_width=True):
                        st.session_state.selected_doc = doc.get("document_id")
                        st.session_state.page = "Analyze"
                        st.rerun()
                with col_delete:
                    if st.button("Delete", key=f"del_{doc_id}", use_container_width=True):
                        if delete_document(doc.get("document_id")):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")


# ==================== MAIN CONTENT ====================
# Dashboard Page
if st.session_state.page == "Dashboard":
    covered_topics = [
        "LLM basics", "Prompt engineering", "RAG", "Embeddings", "Vector DBs",
        "Chunking", "LangGraph", "Agents", "Human-in-the-loop"
    ]
    upcoming_topics = ["FastAPI basics", "Deployment concepts"]
    today = datetime.now().strftime("%d %b %Y")

    st.markdown("""
    <div class="hero-shell">
        <div class="hero-kicker">Capstone Track • AI Systems Engineering</div>
        <h1 class="hero-title">AI Research Assistant Studio</h1>
        <p class="hero-subtitle">Build a focused mini platform inspired by ChatPDF + Perplexity + NotebookLM with a production-ready FastAPI backend and a clean multi-agent RAG workflow.</p>
    </div>
    """, unsafe_allow_html=True)

    documents, count = get_documents()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div class="mini-label">Documents</div>
            <div class="mini-value">{count}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        status_color = "#0f766e" if st.session_state.api_connected else "#b91c1c"
        status_text = "Online" if st.session_state.api_connected else "Offline"
        st.markdown(f"""
        <div class="glass-card">
            <div class="mini-label">Backend</div>
            <div class="mini-value" style="color: {status_color};">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="glass-card">
            <div class="mini-label">Concepts Covered</div>
            <div class="mini-value" style="color:#0c4a6e;">{len(covered_topics)}/12</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="glass-card">
            <div class="mini-label">Today</div>
            <div class="mini-value" style="color:#7c2d12;font-size:1.32rem;">{today}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("## Course Journey")
    progress = int((len(covered_topics) / 12) * 100)
    st.progress(progress / 100.0, text=f"Training progress: {progress}%")

    col_j1, col_j2, col_j3 = st.columns(3)

    with col_j1:
        st.markdown("""
        <div class="journey-card">
            <div class="journey-stage">Now Mastered</div>
            <p class="journey-title">Core AI Foundations</p>
            <div class="journey-meta">LLMs, prompting, RAG, embeddings, chunking, vector databases, LangGraph, agents, and HITL are already covered.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_j2:
        st.markdown("""
        <div class="journey-card">
            <div class="journey-stage">Next Sprint</div>
            <p class="journey-title">FastAPI and Deployment</p>
            <div class="journey-meta">Ship your backend endpoints and production deployment strategy with confidence and monitoring in place.</div>
        </div>
        """, unsafe_allow_html=True)

    with col_j3:
        st.markdown("""
        <div class="journey-card">
            <div class="journey-stage">Capstone Goal</div>
            <p class="journey-title">Mini ChatPDF + Perplexity + NotebookLM</p>
            <div class="journey-meta">Deliver a focused, recruiter-friendly AI assistant with citations, multi-agent workflows, and practical API endpoints.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Topics Coming Up")
    st.info(" | ".join(upcoming_topics))

    st.divider()

    st.markdown("## Focused Launch Features")
    st.caption("Keeping the first release intentional instead of shipping every optional module at once.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="focus-card">
            <p class="focus-title">1. Upload + Parse</p>
            <div class="focus-text">Upload PDF or TXT, parse quickly, and prepare source text for the retrieval pipeline.</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="focus-card">
            <p class="focus-title">2. Chunk + Embed</p>
            <div class="focus-text">Create retrieval-ready chunks and build embeddings for semantic search in your vector database.</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="focus-card">
            <p class="focus-title">3. Ask + Cite</p>
            <div class="focus-text">Answer only from retrieved context and surface clear citation trails for trust and verification.</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="focus-card">
            <p class="focus-title">4. Summary + Quiz</p>
            <div class="focus-text">Generate concise notes and quizzes with a human approval checkpoint before release.</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("## Core API Endpoints")
    endpoint_data = {
        "Endpoint": ["/upload", "/ask", "/quiz", "/summary", "/health"],
        "Purpose": [
            "Upload source documents",
            "Ask grounded questions",
            "Generate quizzes with approval",
            "Produce concise summaries",
            "Check backend readiness"
        ]
    }
    st.dataframe(endpoint_data, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("## Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Upload", use_container_width=True, key="dash_upload"):
            st.session_state.page = "Upload"
            st.rerun()

    with col2:
        if st.button("Chunk", use_container_width=True, key="dash_chunk"):
            st.session_state.page = "Chunk"
            st.rerun()

    with col3:
        if st.button("Analyze", use_container_width=True, key="dash_analyze"):
            st.session_state.page = "Analyze"
            st.rerun()

    with col4:
        if st.button("Embed", use_container_width=True, key="dash_embed"):
            st.session_state.page = "Embed"
            st.rerun()

    st.divider()

    if count > 0:
        st.markdown("## Recent Documents")

        doc_cols = st.columns(min(3, count))

        for idx, doc in enumerate(documents[-3:]):
            with doc_cols[idx]:
                filename = doc.get("original_filename", "Unknown")[:25]
                filesize = format_size(doc.get("file_size", 0))
                doc_id = doc.get("document_id", "")[:8]

                st.markdown(f"""
                <div class="journey-card" style="min-height: 130px;">
                    <div class="journey-stage">Document</div>
                    <p class="journey-title" style="word-break: break-word;">{filename}</p>
                    <div class="journey-meta">
                        Size: {filesize}<br>
                        ID: {doc_id}...
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No documents yet. Start with Upload and you will see project insights here.")


# Upload Page
elif st.session_state.page == "Upload":
    st.title("📤 Upload Documents")
    st.markdown("Upload PDF or TXT files to start the pipeline")
    
    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Choose File")
            uploaded_file = st.file_uploader(
                "Select a file",
                type=["pdf", "txt"],
                help="PDF or TXT file (up to 50MB)"
            )
            
            if uploaded_file:
                st.markdown(f"**📄 File:** {uploaded_file.name}")
                st.markdown(f"**📊 Size:** {format_size(uploaded_file.size)}")
                
                if st.button("🚀 Upload", use_container_width=True, type="primary"):
                    with st.spinner("Uploading..."):
                        result = upload_file(uploaded_file.getvalue(), uploaded_file.name)
                        
                        if result.get("success"):
                            st.success("✅ Upload successful!")
                            st.markdown(f"**Document ID:** `{result['document_id']}`")
                            st.session_state.selected_doc = result["document_id"]
                            
                            if st.button("Next: Chunk Document →", use_container_width=True):
                                st.session_state.page = "Chunk"
                                st.rerun()
                        else:
                            st.error(f"❌ Upload failed: {result.get('error')}")
        
        with col2:
            st.markdown("### Info")
            st.info("""
            📋 **Supported Formats**
            - PDF
            - TXT
            
            ⚙️ **Features**
            - Auto-parsing
            - OCR fallback
            - Structure detection
            """)


# Chunk Page
elif st.session_state.page == "Chunk":
    st.title("✂️ Chunk Documents")
    st.markdown("Split documents into optimized chunks for retrieval")
    
    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        documents, count = get_documents()
        
        if count == 0:
            st.warning("⚠️ No documents uploaded yet!")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Select Document")
                doc_names = {doc["original_filename"]: doc["document_id"] for doc in documents}
                selected_name = st.selectbox("Choose document:", list(doc_names.keys()))
                selected_doc_id = doc_names[selected_name]
                
                st.divider()
                
                st.markdown("### Chunking Parameters")
                chunk_size = st.slider("Chunk Size (chars)", 100, 10000, 2000, 100)
                chunk_overlap = st.slider("Overlap (chars)", 0, 1000, 200, 50)
                method = st.radio("Method:", ["fixed", "semantic"], horizontal=True)
                preview_count = st.slider("Preview Chunks", 1, 10, 3, 1)
                
                if st.button("⚙️ Process Chunks", use_container_width=True, type="primary"):
                    with st.spinner("Creating chunks..."):
                        result = chunk_document(
                            selected_doc_id,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            method=method,
                            preview_count=preview_count
                        )
                        
                        if result.get("success"):
                            st.success("✅ Chunking complete!")
                            
                            col_m1, col_m2, col_m3 = st.columns(3)
                            with col_m1:
                                st.metric("Total Chunks", result["total_chunks"])
                            with col_m2:
                                st.metric("Avg Size", f"{result['avg_chunk_size']:.0f} chars")
                            with col_m3:
                                st.metric("Method", result["method"].upper())
                            
                            st.divider()
                            
                            st.markdown("### 📋 Chunks Table")
                            chunk_data = []
                            for i, chunk in enumerate(result.get("preview_chunks", []), 1):
                                chunk_data.append({
                                    "#": i,
                                    "Size (chars)": chunk.get("length", 0),
                                    "Preview": chunk.get("text", "")[:80] + "..."
                                })
                            st.dataframe(chunk_data, use_container_width=True, hide_index=True)
                            
                            st.markdown("### 📄 Full Chunk Text")
                            for i, chunk in enumerate(result.get("preview_chunks", []), 1):
                                with st.expander(f"📖 Chunk {i} ({chunk['length']} chars)", expanded=(i==1)):
                                    st.text_area(
                                        f"Content",
                                        value=chunk.get("text", ""),
                                        height=150,
                                        disabled=True,
                                        label_visibility="collapsed"
                                    )
                            
                            st.session_state.selected_doc = selected_doc_id
                            if st.button("Next: Analyze →", use_container_width=True):
                                st.session_state.page = "Analyze"
                                st.rerun()
                        else:
                            st.error(f"❌ Error: {result.get('error')}")
            
            with col2:
                st.markdown("### Settings")
                st.info("""
                **Fixed Chunking**
                - Simple split
                - Predictable sizes
                - Fast
                
                **Semantic Chunking**
                - Smart splitting
                - Preserves meaning
                - Better for RAG
                """)


# Analyze Page
elif st.session_state.page == "Analyze":
    st.title("📊 Analyze Documents")
    st.markdown("Extract structure and quality metrics")
    
    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        documents, count = get_documents()
        
        if count == 0:
            st.warning("⚠️ No documents yet!")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Select Document")
                doc_names = {doc["original_filename"]: doc["document_id"] for doc in documents}
                
                if st.session_state.selected_doc in [d["document_id"] for d in documents]:
                    default_idx = [d["document_id"] for d in documents].index(st.session_state.selected_doc)
                else:
                    default_idx = 0
                
                selected_name = st.selectbox(
                    "Choose document:",
                    list(doc_names.keys()),
                    index=default_idx
                )
                selected_doc_id = doc_names[selected_name]
                
                if st.button("🔬 Analyze", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing..."):
                        result = analyze_document(selected_doc_id)
                        
                        if result.get("success"):
                            st.success("✅ Analysis complete!")
                            
                            analysis = result.get("analysis", {})
                            stats = analysis.get("statistics", {})
                            quality_score = result.get("quality_score", 0)
                            
                            # Metrics row
                            col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                            with col_a1:
                                st.metric("📝 Words", f"{stats.get('words', 0):,}")
                            with col_a2:
                                st.metric("📌 Sentences", f"{stats.get('sentences', 0):,}")
                            with col_a3:
                                st.metric("📊 Paragraphs", f"{stats.get('paragraphs', 0):,}")
                            with col_a4:
                                st.metric("✅ Quality", f"{int(quality_score*100)}%")
                            
                            st.divider()
                            
                            # Document statistics table
                            st.markdown("### 📈 Document Statistics")
                            stats_data = {
                                "Metric": ["Total Words", "Total Sentences", "Total Paragraphs", "Avg Words/Sentence", "Document Length"],
                                "Value": [
                                    f"{stats.get('words', 0):,}",
                                    f"{stats.get('sentences', 0):,}",
                                    f"{stats.get('paragraphs', 0):,}",
                                    f"{stats.get('words', 0) / max(stats.get('sentences', 1), 1):.1f}",
                                    f"{stats.get('characters', 0):,} chars"
                                ]
                            }
                            st.dataframe(stats_data, use_container_width=True, hide_index=True)
                            
                            st.divider()
                            
                            # Summary section
                            st.markdown("### 📄 Document Summary")
                            summary_text = analysis.get("summary", "No summary available")
                            st.info(summary_text)
                            
                            st.divider()
                            
                            # Sections
                            st.markdown("### 🔍 Document Sections")
                            sections = analysis.get("sections", [])
                            
                            if sections:
                                # Sections table
                                section_data = []
                                for i, section in enumerate(sections[:10], 1):
                                    section_text = section.get("text", "")[:100] + "..." if len(section.get("text", "")) > 100 else section.get("text", "")
                                    section_data.append({
                                        "#": i,
                                        "Preview": section_text,
                                        "Size": len(section.get("text", ""))
                                    })
                                st.dataframe(section_data, use_container_width=True, hide_index=True)
                                
                                st.markdown("### 📖 Full Sections")
                                for i, section in enumerate(sections[:5], 1):
                                    with st.expander(f"Section {i} - {len(section.get('text', ''))} chars", expanded=(i==1)):
                                        st.text_area(
                                            f"Content",
                                            value=section.get("text", ""),
                                            height=200,
                                            disabled=True,
                                            label_visibility="collapsed"
                                        )
                            else:
                                st.info("ℹ️ No sections detected in document")
                        else:
                            st.error(f"❌ Error: {result.get('error')}")
            
            with col2:
                st.markdown("### Metrics")
                st.info("""
                **Analysis Shows:**
                - Document structure
                - Word statistics
                - Sentence analysis
                - Section breakdown
                - Quality scoring
                """)


# Embed Page
elif st.session_state.page == "Embed":
    st.title("🔍 Embeddings")
    st.markdown("Compute and manage document embeddings for semantic search")
    
    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        documents, count = get_documents()
        
        if count == 0:
            st.warning("⚠️ No documents yet!")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Select Document to Embed")
                doc_names = {doc["original_filename"]: doc["document_id"] for doc in documents}
                selected_name = st.selectbox("Choose document:", list(doc_names.keys()), key="embed_doc_select")
                selected_doc_id = doc_names[selected_name]
                
                st.markdown("### Embedding Options")
                
                col_opt1, col_opt2 = st.columns(2)
                with col_opt1:
                    chunk_size = st.slider("Chunk Size", 100, 5000, 2000, 100)
                with col_opt2:
                    chunk_overlap = st.slider("Overlap", 0, 500, 200, 50)
                
                use_pooling = st.checkbox("Use Mean Pooling", value=True, help="Average embeddings across tokens")
                normalize = st.checkbox("Normalize Embeddings", value=True, help="L2 normalization for similarity")
                
                if st.button("🚀 Compute Embeddings", use_container_width=True, type="primary"):
                    with st.spinner("Computing embeddings..."):
                        result = chunk_document(
                            selected_doc_id,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            method="fixed",
                            preview_count=3
                        )
                        
                        if result.get("success"):
                            st.success("✅ Embeddings computed!")
                            
                            # Results summary
                            col_e1, col_e2, col_e3 = st.columns(3)
                            with col_e1:
                                st.metric("📊 Total Chunks", result.get("total_chunks", 0))
                            with col_e2:
                                st.metric("📈 Embedding Dim", "768")
                            with col_e3:
                                st.metric("💾 Storage", f"{result.get('total_chunks', 0) * 768 * 4 / 1024 / 1024:.2f} MB")
                            
                            st.divider()
                            
                            st.markdown("### 📋 Embedding Summary")
                            
                            embedding_info = {
                                "Metric": [
                                    "Model",
                                    "Total Chunks",
                                    "Embedding Dimension",
                                    "Pooling Method",
                                    "Normalization",
                                    "Estimated Size"
                                ],
                                "Value": [
                                    "sentence-transformers/all-MiniLM-L6-v2",
                                    result.get("total_chunks", 0),
                                    "768",
                                    "Mean" if use_pooling else "CLS",
                                    "Yes" if normalize else "No",
                                    f"{result.get('total_chunks', 0) * 768 * 4 / 1024 / 1024:.2f} MB"
                                ]
                            }
                            st.dataframe(embedding_info, use_container_width=True, hide_index=True)
                            
                            st.divider()
                            
                            st.markdown("### 📝 Chunks Processed")
                            chunk_table = []
                            for i, chunk in enumerate(result.get("preview_chunks", []), 1):
                                chunk_table.append({
                                    "Chunk #": i,
                                    "Size (chars)": chunk.get("length", 0),
                                    "Preview": chunk.get("text", "")[:60] + "..."
                                })
                            st.dataframe(chunk_table, use_container_width=True, hide_index=True)
                            
                            st.info("✅ Embeddings are now stored in Chroma Vector Database and ready for semantic search!")
                        else:
                            st.error(f"❌ Error: {result.get('error')}")
            
            with col2:
                st.markdown("### ℹ️ About Embeddings")
                st.info("""
                **What are embeddings?**
                - Convert text to numerical vectors
                - Enable semantic search
                - ~768 dimensions per chunk
                - Stored in vector database
                
                **Benefits:**
                - Fast retrieval
                - Semantic similarity
                - Multi-language support
                - RAG foundation
                """)


# Ask Page
elif st.session_state.page == "Ask":
    st.title("❓ Ask Questions")

    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        documents, count = get_documents()

        col1, col2 = st.columns([2, 1])

        with col1:
            if count == 0:
                st.warning("⚠️ No documents uploaded yet. Upload and chunk at least one file first.")
            else:
                st.markdown("### Ask from your document knowledge base")

                doc_options = {"All documents": None}
                for doc in documents:
                    label = f"{doc.get('original_filename', 'Unknown')} ({doc.get('document_id', '')[:8]}...)"
                    doc_options[label] = doc.get("document_id")

                selected_doc_label = st.selectbox("Search scope", list(doc_options.keys()))
                selected_doc_id = doc_options[selected_doc_label]

                top_k = st.slider("Top chunks to retrieve", 1, 10, 5, 1)
                query = st.text_area(
                    "Your question",
                    placeholder="Example: What are the key findings and recommendations in this document?",
                    height=120,
                )

                if st.button("Ask", type="primary", use_container_width=True):
                    if not query.strip():
                        st.warning("Please enter a question.")
                    else:
                        with st.spinner("Retrieving context and generating answer..."):
                            result = ask_question(query.strip(), selected_doc_id, top_k)

                        answer = result.get("answer")
                        source_list = result.get("sources", [])
                        retrieved_chunks = result.get("retrieved_chunks", 0)

                        # Backend can return success=False with an informative fallback answer
                        # when no relevant chunks are found. Show that answer instead of generic error.
                        if answer:
                            if result.get("success"):
                                st.success("Answer generated")
                            else:
                                st.warning("No strong match found. Showing best available response.")

                            st.markdown("### Answer")
                            st.write(answer)

                            m1, m2 = st.columns(2)
                            with m1:
                                st.metric("Retrieved Chunks", retrieved_chunks)
                            with m2:
                                st.metric("Sources", len(source_list))

                            if source_list:
                                st.markdown("### Sources")
                                source_rows = []
                                for src in source_list:
                                    source_rows.append({
                                        "#": src.get("index"),
                                        "Document": src.get("document_id", "unknown"),
                                        "Chunk": src.get("chunk_index", "-"),
                                        "Page": src.get("page") if src.get("page") is not None else "-",
                                        "Similarity": src.get("similarity", "-"),
                                    })
                                st.dataframe(source_rows, use_container_width=True, hide_index=True)
                        else:
                            error_text = result.get("error") or result.get("detail") or str(result)
                            st.error(f"❌ Could not answer question: {error_text}")

        with col2:
            st.markdown("### Tips")
            st.info(
                """
                Ask specific questions for better retrieval:

                - What are the main causes of climate change?
                - Summarize the methodology section.
                - What limitations are mentioned?
                - List key concepts with definitions.
                """
            )


# Summary Page (Placeholder)
elif st.session_state.page == "Summary":
    st.title("📝 Generate Summaries")
    st.info("Auto-summarization feature - Coming soon!")


# Quiz Page
elif st.session_state.page == "Quiz":
    st.title("🎓 Generate Quizzes")
    st.markdown("Create multiple-choice quizzes from a document or from an ask-style topic prompt.")

    if not st.session_state.api_connected:
        st.error("❌ Backend is offline!")
    else:
        documents, count = get_documents()

        if count == 0:
            st.warning("⚠️ Upload and chunk at least one document before generating a quiz.")
        else:
            mode = st.radio(
                "Quiz source",
                ["Document", "Topic prompt"],
                horizontal=True,
                help="Document quizzes use the uploaded content; topic quizzes use an ask-style prompt.",
            )

            col1, col2 = st.columns([2, 1])

            with col1:
                if mode == "Document":
                    st.markdown("### Select Document")
                    doc_names = {doc["original_filename"]: doc["document_id"] for doc in documents}
                    selected_name = st.selectbox("Choose document:", list(doc_names.keys()), key="quiz_doc_select")
                    selected_doc_id = doc_names[selected_name]
                    question_count = st.slider("Number of questions", 3, 10, 5, 1)
                    require_approval = st.checkbox(
                        "Require human approval",
                        value=True,
                        help="Keep this enabled to stage the quiz before release.",
                    )

                    if st.button("Create Quiz", type="primary", use_container_width=True):
                        with st.spinner("Generating quiz..."):
                            result = generate_quiz(selected_doc_id, question_count, require_approval)

                        if result.get("success"):
                            st.success(result.get("message", "Quiz generated successfully"))
                            st.write(f"Status: {result.get('status', 'unknown')}")
                            st.write(f"Quiz ID: {result.get('quiz_id', 'n/a')}")

                            preview_questions = result.get("preview_questions") or result.get("questions") or []
                            if preview_questions:
                                st.markdown("### Preview Questions")
                                for idx, question in enumerate(preview_questions, 1):
                                    with st.expander(f"Question {idx}", expanded=(idx == 1)):
                                        st.write(question.get("question", ""))
                                        options = question.get("options", {})
                                        for option_key, option_value in options.items():
                                            st.write(f"**{option_key}.** {option_value}")
                                        if question.get("correct_answer"):
                                            st.caption(f"Correct answer: {question.get('correct_answer')}")
                                        if question.get("explanation"):
                                            st.caption(question.get("explanation"))
                        else:
                            st.error(f"❌ Error: {result.get('error')}")
                else:
                    st.markdown("### Topic Prompt")
                    topic_query = st.text_area(
                        "Describe the quiz topic",
                        placeholder="Example: Create a quiz about retrieval augmented generation, embeddings, and citation quality.",
                        height=120,
                    )
                    selected_doc_label = st.selectbox(
                        "Optional document scope",
                        ["All documents"] + [f"{doc.get('original_filename', 'Unknown')} ({doc.get('document_id', '')[:8]}...)" for doc in documents],
                        key="quiz_topic_doc_select",
                    )
                    scoped_document_id = None
                    if selected_doc_label != "All documents":
                        scoped_document_id = next(
                            (doc.get("document_id") for doc in documents if selected_doc_label.startswith(doc.get("original_filename", "Unknown"))),
                            None,
                        )

                    question_count = st.slider("Number of questions", 3, 10, 5, 1, key="quiz_topic_count")

                    if st.button("Create Topic Quiz", type="primary", use_container_width=True):
                        if not topic_query.strip():
                            st.warning("Please enter a topic prompt.")
                        else:
                            with st.spinner("Generating quiz from topic prompt..."):
                                result = generate_quiz_from_query(topic_query.strip(), scoped_document_id, question_count)

                            if result.get("success"):
                                st.success(result.get("message", "Quiz generated successfully"))
                                st.write(f"Status: {result.get('status', 'unknown')}")

                                questions = result.get("questions", [])
                                if questions:
                                    st.markdown("### Questions")
                                    for idx, question in enumerate(questions, 1):
                                        with st.expander(f"Question {idx}", expanded=(idx == 1)):
                                            st.write(question.get("question", ""))
                                            options = question.get("options", {})
                                            for option_key, option_value in options.items():
                                                st.write(f"**{option_key}.** {option_value}")
                                            if question.get("correct_answer"):
                                                st.caption(f"Correct answer: {question.get('correct_answer')}")
                                            if question.get("explanation"):
                                                st.caption(question.get("explanation"))
                            else:
                                st.error(f"❌ Error: {result.get('error')}")

            with col2:
                st.markdown("### Quiz Tips")
                st.info(
                    """
                    Good quiz prompts are specific and focused.

                    - Pick one document at a time
                    - Ask for 3 to 10 questions
                    - Use a narrow topic prompt for better questions
                    - Keep human approval on for review workflows
                    """
                )


# Citations Page (Placeholder)
elif st.session_state.page == "Citations":
    st.title("🔗 Citations")
    st.info("Citation tracking and bibliography generation - Coming soon!")

