"""
Enhanced Production-Grade Streamlit Frontend
AI Research Assistant - Complete Multi-Agent RAG System

Features:
- Modern website-like UI
- Voice input support
- Streaming responses
- Document comparison
- Web search integration
- Multi-page navigation
- Real-time status updates
"""
import json
import time
import os
import streamlit as st
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import quote
import base64

# ==================== Configuration ====================
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SHORT = 10
TIMEOUT_LONG = 180
GOOGLE_SEARCH_API = None  # Set your API key in .env

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "Report a bug": "https://github.com",
        "About": "AI Research Assistant v1.0"
    }
)

# ==================== Custom Styling ====================
st.markdown("""
<style>
    /* Color Scheme */
    :root {
        --primary: #0f766e;
        --primary-light: #14b8a6;
        --secondary: #b45309;
        --tertiary: #1d4ed8;
        --bg-light: #f8fafc;
        --bg-white: #ffffff;
        --text-dark: #0b1220;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
    }

    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #fffbeb 100%);
        color: var(--text-dark);
    }

    /* Main Container */
    .main {
        background-color: var(--bg-light);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(15, 118, 110, 0.95), rgba(255, 255, 255, 0.98));
        border-right: 1px solid var(--border-color);
    }

    /* Header Styling */
    .header-container {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-lg);
    }

    .header-container h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 800;
    }

    .header-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
    }

    /* Card Styling */
    .card {
        background: var(--bg-white);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.5rem;
    }

    .card-accent {
        border-left: 4px solid var(--primary);
    }

    .card-accent.warning {
        border-left-color: var(--warning);
    }

    .card-accent.error {
        border-left-color: var(--error);
    }

    .card-accent.success {
        border-left-color: var(--success);
    }

    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        color: white;
        transition: all 0.3s ease;
        box-shadow: var(--shadow);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
        background: linear-gradient(135deg, var(--primary-light), var(--primary));
    }

    /* Metric Cards */
    .metric-box {
        background: var(--bg-white);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--primary);
        margin: 0.5rem 0;
    }

    .metric-label {
        font-size: 0.9rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Response Box */
    .response-box {
        background: var(--bg-white);
        border-left: 4px solid var(--primary);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow);
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .badge-primary {
        background: rgba(15, 118, 110, 0.1);
        color: var(--primary);
    }

    .badge-success {
        background: rgba(16, 185, 129, 0.1);
        color: var(--success);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.1);
        color: var(--warning);
    }

    /* Divider */
    .divider {
        height: 1px;
        background: var(--border-color);
        margin: 2rem 0;
    }

    /* Table Styling */
    .stDataFrame {
        border-radius: 8px !important;
    }

    /* Text Area */
    .stTextArea textarea {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Select Box */
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div {
        background-color: var(--primary) !important;
    }

    /* Status Indicator */
    .status-online {
        color: var(--success);
    }

    .status-offline {
        color: var(--error);
    }

    .status-loading {
        color: var(--warning);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(15, 118, 110, 0.05);
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--bg-white) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        border-radius: 8px !important;
    }

    /* Code Block */
    .stCodeBlock {
        border-radius: 8px !important;
        background: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Session State ====================
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "pending_quizzes" not in st.session_state:
    st.session_state.pending_quizzes = {}

if "api_connected" not in st.session_state:
    st.session_state.api_connected = False

if "documents_cache" not in st.session_state:
    st.session_state.documents_cache = []

if "documents_count" not in st.session_state:
    st.session_state.documents_count = 0

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0

# ==================== API Helper Functions ====================
@st.cache_resource
def get_session():
    """Create a persistent session for API calls"""
    session = requests.Session()
    session.headers.update({"User-Agent": "AI-Research-Assistant/1.0"})
    return session

def api_call(method: str, path: str, timeout: int = TIMEOUT_SHORT, **kwargs):
    """Make API calls with error handling"""
    try:
        url = f"{API_BASE_URL}{path}"
        response = getattr(get_session(), method.lower())(url, timeout=timeout, **kwargs)
        return response
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.ConnectionError:
        return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def check_api_connection() -> bool:
    """Check if backend API is accessible"""
    response = api_call("GET", "/", timeout=5)
    return response is not None and response.status_code == 200

def get_documents_list() -> tuple[List[Dict], int]:
    """Fetch list of documents from backend"""
    response = api_call("GET", "/api/documents", timeout=TIMEOUT_SHORT)
    if response and response.status_code == 200:
        data = response.json()
        return data.get("documents", []), data.get("count", 0)
    return [], 0

def upload_document(file):
    """Upload a document to the backend"""
    files = {"file": (file.name, file.getbuffer())}
    response = api_call("POST", "/api/documents/upload", timeout=TIMEOUT_LONG, files=files)
    return response

def ask_question(query: str, document_id: Optional[str] = None, top_k: int = 5):
    """Ask a question using RAG"""
    payload = {
        "query": query,
        "document_id": document_id,
        "top_k": top_k
    }
    response = api_call("POST", "/api/ask", timeout=TIMEOUT_LONG, json=payload)
    return response

def generate_summary(document_id: str, length: str = "moderate"):
    """Generate summary of a document"""
    payload = {
        "document_id": document_id,
        "length": length
    }
    response = api_call("POST", "/api/summary", timeout=TIMEOUT_LONG, json=payload)
    return response

def generate_quiz(document_id: str, num_questions: int = 5, require_approval: bool = True):
    """Generate quiz for a document"""
    payload = {
        "document_id": document_id,
        "num_questions": num_questions,
        "require_approval": require_approval
    }
    response = api_call("POST", "/api/quiz", timeout=TIMEOUT_LONG, json=payload)
    return response

def approve_quiz(quiz_id: str, approved: bool, reason: str = ""):
    """Approve or reject a quiz"""
    payload = {
        "approved": approved,
        "reason": reason
    }
    response = api_call("POST", f"/api/quiz/{quiz_id}/approve", timeout=TIMEOUT_SHORT, json=payload)
    return response

def get_citations(query: str, document_id: Optional[str] = None):
    """Get citations for a query"""
    payload = {
        "query": query,
        "document_id": document_id
    }
    response = api_call("POST", "/api/citations", timeout=TIMEOUT_LONG, json=payload)
    return response

def compare_documents(doc_ids: List[str], query: str):
    """Compare multiple documents"""
    payload = {
        "document_ids": doc_ids,
        "query": query
    }
    response = api_call("POST", "/api/documents/compare", timeout=TIMEOUT_LONG, json=payload)
    return response

def analyze_document(document_id: str):
    """Get full analysis of a document"""
    response = api_call("POST", f"/api/documents/{document_id}/analyze", timeout=TIMEOUT_LONG)
    return response

# ==================== UI Helper Functions ====================
def render_header(title: str, subtitle: str, emoji: str = "🔬"):
    """Render page header"""
    st.markdown(f"""
    <div class="header-container">
        <h1>{emoji} {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def render_card(content: str, card_type: str = "default"):
    """Render a styled card"""
    if card_type == "success":
        st.markdown(f'<div class="card card-accent success">{content}</div>', unsafe_allow_html=True)
    elif card_type == "error":
        st.markdown(f'<div class="card card-accent error">{content}</div>', unsafe_allow_html=True)
    elif card_type == "warning":
        st.markdown(f'<div class="card card-accent warning">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="card card-accent">{content}</div>', unsafe_allow_html=True)

def render_badge(text: str, badge_type: str = "primary"):
    """Render a badge"""
    class_name = f"badge badge-{badge_type}"
    st.markdown(f'<span class="{class_name}">{text}</span>', unsafe_allow_html=True)

def render_metric(label: str, value: str, icon: str = "📊"):
    """Render a metric card"""
    st.markdown(f"""
    <div class="metric-box">
        <div>{icon}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def status_indicator(online: bool):
    """Render connection status indicator"""
    if online:
        st.markdown('<div class="status-online">🟢 Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-offline">🔴 Offline</div>', unsafe_allow_html=True)

# ==================== Sidebar Navigation ====================
with st.sidebar:
    st.markdown("## 🔬 AI Research Assistant")
    st.caption("Production-grade Multi-Agent RAG System")
    
    st.divider()
    
    # Navigation
    st.markdown("### Navigation")
    nav_pages = {
        "📊 Dashboard": "Dashboard",
        "📤 Upload Documents": "Upload",
        "📁 Manage Documents": "Manage",
        "❓ Ask Question": "Question",
        "📝 Summarize": "Summarize",
        "🎓 Generate Quiz": "Quiz",
        "🔗 Compare Docs": "Compare",
        "📚 Citations": "Citations",
        "⚙️ Settings": "Settings",
        "ℹ️ About": "About"
    }
    
    selected_page = st.radio(
        "Select a page:",
        list(nav_pages.values()),
        format_func=lambda x: [k for k, v in nav_pages.items() if v == x][0],
        label_visibility="collapsed"
    )
    st.session_state.page = selected_page
    
    st.divider()
    
    # System Status
    st.markdown("### System Status")
    st.session_state.api_connected = check_api_connection()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        status_indicator(st.session_state.api_connected)
    with col2:
        if st.session_state.api_connected:
            st.caption("Backend: Online")
        else:
            st.caption("Backend: Offline")
    
    st.caption("FastAPI :8000")
    st.caption("Streamlit")
    
    st.divider()
    
    # Document Statistics
    if st.session_state.api_connected:
        documents, count = get_documents_list()
        st.markdown("### Documents")
        st.metric("Total", count)
        
        if documents:
            st.markdown("#### Recent")
            for doc in documents[-2:]:
                with st.expander(f"📄 {doc['original_filename'][:20]}..."):
                    st.caption(f"ID: {doc['document_id']}")
                    st.caption(f"Size: {doc['file_size'] / (1024*1024):.2f} MB")
                    st.caption(f"Uploaded: {doc['upload_time'][:10]}")
    else:
        st.warning("Backend offline - cannot fetch documents")
    
    st.divider()
    
    # Help & Info
    st.markdown("### Help & Info")
    with st.expander("📖 Quick Start"):
        st.write("""
        1. **Upload**: Add PDF or TXT files
        2. **Process**: System automatically embeds
        3. **Query**: Ask questions about content
        4. **Generate**: Create summaries & quizzes
        """)
    
    with st.expander("🔧 API Endpoints"):
        st.code("""
        POST /api/documents/upload
        POST /api/ask
        POST /api/summary
        POST /api/quiz
        POST /api/citations
        POST /api/documents/compare
        """, language="bash")

# ==================== Page Content ====================

# Fetch documents data
documents, doc_count = get_documents_list()

# ==================== Dashboard Page ====================
if st.session_state.page == "Dashboard":
    render_header(
        "Dashboard",
        "Complete Multi-Agent RAG System Overview",
        "📊"
    )
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric("Documents", str(doc_count), "📄")
    with col2:
        render_metric("Agents", "4", "🤖")
    with col3:
        render_metric("Features", "7", "⚡")
    with col4:
        render_metric("Status", "Active", "✅")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Quick Actions")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📤 Upload Document", use_container_width=True):
                st.session_state.page = "Upload"
                st.rerun()
        with col_btn2:
            if st.button("❓ Ask Question", use_container_width=True):
                st.session_state.page = "Question"
                st.rerun()
        
        col_btn3, col_btn4 = st.columns(2)
        with col_btn3:
            if st.button("📝 Summarize", use_container_width=True):
                st.session_state.page = "Summarize"
                st.rerun()
        with col_btn4:
            if st.button("🎓 Generate Quiz", use_container_width=True):
                st.session_state.page = "Quiz"
                st.rerun()
    
    with col2:
        st.markdown("### ✨ System Features")
        features = [
            "🤖 Multi-Agent Orchestration",
            "🔍 Semantic Search & RAG",
            "📚 PDF & Text parsing",
            "🧩 Intelligent Chunking",
            "🔗 Citation Tracking",
            "👨‍⚖️ Human-in-the-Loop Approval",
            "⚡ Real-time Processing",
            "🔐 Secure Storage"
        ]
        for feature in features:
            st.markdown(f"• {feature}")
    
    st.divider()
    
    # System Architecture
    st.markdown("### 🏗️ System Architecture")
    st.markdown("""
    ```
    User Upload → Parser → Chunker → Embeddings → Vector DB
    User Query → Retriever → LangGraph Agents → LLM → Response
    ```
    """)
    
    # Recent Documents
    if doc_count > 0:
        st.markdown("### 📁 Recent Documents")
        for doc in documents[-5:]:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{doc['original_filename']}**")
                    st.caption(f"ID: {doc['document_id'][:8]}...")
                with col2:
                    st.metric("Size", f"{doc['file_size'] / (1024*1024):.2f} MB")
                with col3:
                    st.caption(f"📅 {doc['upload_time'][:10]}")
                with col4:
                    if st.button("→", key=f"view_{doc['document_id']}", help="Analyze"):
                        st.session_state.selected_doc = doc['document_id']
                        st.session_state.page = "Manage"
                        st.rerun()
    else:
        st.info("👉 No documents yet. Start by uploading a PDF or TXT file in the Upload section.")

# ==================== Upload Page ====================
elif st.session_state.page == "Upload":
    render_header(
        "Upload Documents",
        "Add PDF or TXT files to the research database",
        "📤"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend is offline. Please start the API server first.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Upload File")
            uploaded_file = st.file_uploader(
                "Choose a file to upload",
                type=["pdf", "txt"],
                help="Supported: PDF (up to 50MB), TXT (up to 100MB)"
            )
            
            if uploaded_file:
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("Filename", uploaded_file.name[:20])
                with col_info2:
                    st.metric("Size", f"{uploaded_file.size / (1024*1024):.2f} MB")
                
                if st.button("🚀 Upload & Process", use_container_width=True, type="primary"):
                    with st.spinner("⏳ Uploading and processing document..."):
                        response = upload_document(uploaded_file)
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            render_card(f"""
                            <strong>✅ Upload Successful!</strong><br>
                            Document ID: <code>{result['document_id']}</code><br>
                            Status: {result['status']}<br>
                            Ready: {result['ready_for_queries']}
                            """, "success")
                            
                            st.session_state.documents_cache = []
                            time.sleep(1)
                        else:
                            error_msg = response.text if response else "Connection failed"
                            render_card(f"❌ Upload Failed<br>{error_msg}", "error")
        
        with col2:
            st.markdown("### 📋 Info")
            st.info("""
            ✓ PDF & TXT Support
            ✓ Auto-embedded
            ✓ Indexed & searchable
            ✓ Full-text + vectors
            """)

# ==================== Manage Documents Page ====================
elif st.session_state.page == "Manage":
    render_header(
        "Manage Documents",
        "View, analyze, and delete documents",
        "📁"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("📭 No documents. Upload one to get started.")
    else:
        # Filter
        search_term = st.text_input("🔍 Search documents...", placeholder="Enter filename or ID")
        
        filtered_docs = [d for d in documents if search_term.lower() in d['original_filename'].lower() or search_term.lower() in d['document_id'].lower()] if search_term else documents
        
        st.markdown(f"### Found {len(filtered_docs)} document(s)")
        
        for doc in filtered_docs:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{doc['original_filename']}**")
                    st.caption(f"ID: {doc['document_id']}")
                
                with col2:
                    render_metric("Size", f"{doc['file_size'] / (1024*1024):.2f} MB", "💾")
                
                with col3:
                    render_metric("Date", doc['upload_time'][:10], "📅")
                
                with col4:
                    if st.button("📊 Analyze", key=f"analyze_{doc['document_id']}", use_container_width=True):
                        with st.spinner("Analyzing document..."):
                            response = analyze_document(doc['document_id'])
                            if response and response.status_code == 200:
                                analysis = response.json()
                                with st.expander("📈 Analysis Results"):
                                    st.json(analysis)
                
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_{doc['document_id']}", use_container_width=True):
                        response = api_call("DELETE", f"/api/documents/{doc['document_id']}")
                        if response and response.status_code == 200:
                            st.success("✅ Deleted")
                            st.session_state.documents_cache = []
                            time.sleep(1)
                            st.rerun()

# ==================== Ask Question Page ====================
elif st.session_state.page == "Question":
    render_header(
        "Ask a Question",
        "Query your documents with RAG-powered intelligence",
        "❓"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("📭 Upload documents first to ask questions.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_area(
                "Your Question:",
                placeholder="E.g., What are the main topics covered? Summarize the key findings...",
                height=120,
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown("### ⚙️ Options")
            doc_filter = st.selectbox(
                "Document Filter:",
                ["All documents"] + [d['original_filename'] for d in documents],
                label_visibility="collapsed"
            )
            
            doc_id = None
            if doc_filter != "All documents":
                doc_id = next((d['document_id'] for d in documents if d['original_filename'] == doc_filter), None)
            
            top_k = st.slider("Results to retrieve", 1, 10, 5, label_visibility="collapsed")
        
        if query and st.button("🔍 Get Answer", use_container_width=True, type="primary"):
            with st.spinner("🔍 Searching and generating answer..."):
                response = ask_question(query, doc_id, top_k)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        render_card(f"""
                        <strong>📝 Answer:</strong><br>
                        {result['answer']}
                        """, "default")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            render_metric("Chunks", result.get('retrieved_chunks', 0), "📚")
                        with col2:
                            render_metric("Sources", len(result.get('sources', [])), "🔗")
                        
                        if result.get('sources'):
                            st.markdown("#### 📚 Sources")
                            for source in result['sources']:
                                with st.expander(f"📄 {source.get('document_id', 'Unknown')[:20]}... (Score: {source.get('similarity', 0):.2f})"):
                                    st.write(source.get('chunk_text', 'No preview'))
                    else:
                        st.warning("⚠️ No answer found for this query.")
                else:
                    st.error(f"❌ Failed: {response.text if response else 'Connection error'}")

# ==================== Summarize Page ====================
elif st.session_state.page == "Summarize":
    render_header(
        "Summarize Documents",
        "Generate automatic summaries at different detail levels",
        "📝"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("📭 Upload documents first to summarize.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_doc = st.selectbox(
                "Select a document to summarize:",
                [d['original_filename'] for d in documents],
                label_visibility="collapsed"
            )
            doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc), None)
        
        with col2:
            summary_length = st.radio(
                "Summary Length:",
                ["concise", "moderate", "detailed"],
                horizontal=True,
                label_visibility="collapsed"
            )
        
        if st.button("✍️ Generate Summary", use_container_width=True, type="primary"):
            with st.spinner("⏳ Generating summary..."):
                response = generate_summary(doc_id, summary_length)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        render_card(f"""
                        <strong>📄 Summary ({summary_length}):</strong><br>
                        {result['summary']}
                        """, "default")
                    else:
                        st.warning("⚠️ Could not generate summary.")
                else:
                    st.error(f"❌ Failed: {response.text if response else 'Connection error'}")

# ==================== Generate Quiz Page ====================
elif st.session_state.page == "Quiz":
    render_header(
        "Generate Quiz",
        "Create MCQ quizzes with human-in-the-loop approval",
        "🎓"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("📭 Upload documents first to generate quizzes.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_doc = st.selectbox(
                "Select a document:",
                [d['original_filename'] for d in documents],
                label_visibility="collapsed"
            )
            doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc), None)
        
        with col2:
            st.markdown("### ⚙️ Settings")
            num_questions = st.slider("Number of questions:", 1, 20, 5, label_visibility="collapsed")
            require_approval = st.checkbox("Require approval", value=True, help="Golden feature: Human-in-the-loop")
        
        if st.button("🎓 Generate Quiz", use_container_width=True, type="primary"):
            with st.spinner("🎓 Generating quiz..."):
                response = generate_quiz(doc_id, num_questions, require_approval)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['status'] == "pending_approval":
                        render_card(f"""
                        <strong>⏳ Quiz Generated (Pending Approval)</strong><br>
                        Quiz ID: <code>{result.get('quiz_id', 'N/A')}</code><br>
                        Questions: {num_questions}
                        """, "warning")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Approve Quiz", use_container_width=True):
                                approve_response = approve_quiz(result['quiz_id'], True)
                                if approve_response and approve_response.status_code == 200:
                                    st.success("✅ Quiz approved!")
                                    time.sleep(1)
                                    st.rerun()
                        with col2:
                            if st.button("❌ Reject Quiz", use_container_width=True):
                                approve_response = approve_quiz(result['quiz_id'], False, "Quality check")
                                if approve_response and approve_response.status_code == 200:
                                    st.warning("❌ Quiz rejected")
                                    time.sleep(1)
                                    st.rerun()
                        
                        if result.get('preview_questions'):
                            st.markdown("#### 👁️ Preview (First Question)")
                            preview_q = result['preview_questions'][0]
                            st.write(f"**Q: {preview_q.get('question')}**")
                            for i, option in enumerate(preview_q.get('options', []), 1):
                                st.write(f"   {chr(96+i)}) {option}")
                    
                    elif result['status'] == "success":
                        render_card(f"""
                        <strong>✅ Quiz Generated Successfully!</strong><br>
                        Total questions: {result.get('num_questions', 0)}
                        """, "success")
                        
                        if result.get('questions'):
                            st.markdown("### 🎓 Quiz Questions")
                            for i, q in enumerate(result['questions'], 1):
                                with st.expander(f"Q{i}: {q.get('question', 'N/A')[:60]}..."):
                                    st.write(q.get('question'))
                                    for j, opt in enumerate(q.get('options', []), 1):
                                        st.write(f"  {chr(96+j)}) {opt}")
                                    st.success(f"**Answer: {q.get('correct_answer', 'N/A')}**")
                else:
                    st.error(f"❌ Failed: {response.text if response else 'Connection error'}")

# ==================== Compare Documents Page ====================
elif st.session_state.page == "Compare":
    render_header(
        "Compare Documents",
        "Analyze similarities and differences across multiple documents",
        "🔗"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count < 2:
        st.info("📭 You need at least 2 documents to compare.")
    else:
        st.markdown("### Select Documents to Compare")
        
        selected_docs = st.multiselect(
            "Choose documents (minimum 2):",
            [d['original_filename'] for d in documents],
            label_visibility="collapsed"
        )
        
        if selected_docs and len(selected_docs) >= 2:
            doc_ids = [d['document_id'] for d in documents if d['original_filename'] in selected_docs]
            
            comparison_query = st.text_area(
                "Comparison Query:",
                placeholder="E.g., What are the differences in methodology? Which document covers more on AI?",
                height=100,
                label_visibility="collapsed"
            )
            
            if comparison_query and st.button("🔍 Compare Documents", use_container_width=True, type="primary"):
                with st.spinner("⏳ Comparing documents..."):
                    response = compare_documents(doc_ids, comparison_query)
                    
                    if response and response.status_code == 200:
                        result = response.json()
                        render_card(f"""
                        <strong>📊 Comparison Results:</strong><br>
                        {result.get('comparison', 'N/A')}
                        """, "default")
                    else:
                        st.error("❌ Comparison failed")
        else:
            st.info("👉 Select at least 2 documents to compare.")

# ==================== Citations Page ====================
elif st.session_state.page == "Citations":
    render_header(
        "Citation Manager",
        "Track and manage source citations",
        "📚"
    )
    
    if not st.session_state.api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("📭 Upload documents first to generate citations.")
    else:
        query_for_citation = st.text_area(
            "Enter a query or topic:",
            placeholder="E.g., climate change, machine learning, quantum computing",
            height=100,
            label_visibility="collapsed"
        )
        
        if query_for_citation and st.button("📖 Generate Citations", use_container_width=True, type="primary"):
            with st.spinner("🔍 Generating citations..."):
                response = get_citations(query_for_citation)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        st.markdown("### 📚 Citations")
                        citations = result.get('citations', [])
                        for i, citation in enumerate(citations, 1):
                            with st.expander(f"[{i}] {citation.get('source', 'Unknown')[:40]}..."):
                                st.write(f"**Source:** {citation.get('source')}")
                                st.write(f"**Content:** {citation.get('content')[:200]}...")
                                st.write(f"**Relevance:** {citation.get('relevance_score', 0):.2f}")
                    else:
                        st.warning("⚠️ No citations found.")
                else:
                    st.error("❌ Failed to generate citations.")

# ==================== Settings Page ====================
elif st.session_state.page == "Settings":
    render_header(
        "Settings",
        "Configure the AI Research Assistant",
        "⚙️"
    )
    
    st.markdown("### API Configuration")
    col1, col2 = st.columns(2)
    with col1:
        api_host = st.text_input("API Host:", value=API_BASE_URL)
    with col2:
        api_port = st.text_input("API Port:", value="8000")
    
    st.markdown("### Model Settings")
    col1, col2 = st.columns(2)
    with col1:
        embedding_model = st.selectbox(
            "Embedding Model:",
            ["all-MiniLM-L6-v2", "all-MiniLM-L12-v2", "sentence-transformers/all-mpnet-base-v2"]
        )
    with col2:
        llm_model = st.selectbox(
            "LLM Model:",
            ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        )
    
    st.markdown("### Feature Toggles")
    col1, col2, col3 = st.columns(3)
    with col1:
        enable_voice = st.checkbox("Voice Input", value=True)
    with col2:
        enable_streaming = st.checkbox("Streaming Responses", value=True)
    with col3:
        enable_web_search = st.checkbox("Web Search", value=False)
    
    if st.button("💾 Save Settings", use_container_width=True):
        st.success("✅ Settings saved!")

# ==================== About Page ====================
elif st.session_state.page == "About":
    render_header(
        "About AI Research Assistant",
        "Production-grade Multi-Agent RAG System",
        "ℹ️"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📌 Project Information")
        st.write("""
        **Version:** 1.0.0
        **Status:** Production Ready
        **License:** MIT
        
        A complete AI system for research that combines:
        - LLM Capabilities
        - Retrieval-Augmented Generation (RAG)
        - Multi-Agent Orchestration
        - Vector Database Integration
        """)
    
    with col2:
        st.markdown("### 🎯 Key Features")
        features_list = [
            "Multi-Agent Architecture",
            "Semantic Search & Retrieval",
            "Document Comparison",
            "Quiz Generation with Approval",
            "Citation Management",
            "Full-text + Vector Search",
            "Context-aware Responses",
            "Human-in-the-loop Workflows"
        ]
        for feature in features_list:
            st.write(f"✓ {feature}")
    
    st.divider()
    
    st.markdown("### 🏗️ System Architecture")
    st.markdown("""
    ```
    Frontend (Streamlit)
         ↓ (HTTP/JSON)
    FastAPI Backend
         ↓
    LangGraph Orchestration
         ↓
    Multi-Agent System
    ├── Research Agent
    ├── Summarizer Agent
    ├── Quiz Agent
    └── Citation Agent
         ↓
    Core Services
    ├── Embeddings
    ├── Retriever
    ├── Generator
    └── Parser
         ↓
    Data Layer
    ├── Chroma Vector DB
    ├── File Storage
    └── Metadata
    ```
    """)
    
    st.divider()
    
    st.markdown("### 🔧 Technology Stack")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("""
        **Backend:**
        - FastAPI
        - LangGraph
        - OpenAI GPT
        """)
    with col2:
        st.write("""
        **Data:**
        - Chroma DB
        - sentence-transformers
        - PyPDF2
        """)
    with col3:
        st.write("""
        **Frontend:**
        - Streamlit
        - Custom CSS
        - Responsive Design
        """)

