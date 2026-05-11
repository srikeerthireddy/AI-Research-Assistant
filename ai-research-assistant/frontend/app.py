"""
Streamlit Frontend for AI Research Assistant
Complete Multi-Agent RAG System Interface
Production-grade UI with all phases integrated
"""
import json
from datetime import datetime
import time
import streamlit as st
import requests
from typing import Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT_SHORT = 10
TIMEOUT_LONG = 180

# Page Config
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== Custom Styling ====================
st.markdown(
    """
<style>
    :root {
        --bg: #f5f1e8;
        --panel: rgba(255, 255, 255, 0.78);
        --panel-strong: rgba(255, 255, 255, 0.94);
        --text: #0b1220;
        --muted: #4b5563;
        --line: rgba(31, 41, 55, 0.10);
        --accent: #0f766e;
        --accent-2: #b45309;
        --accent-3: #1d4ed8;
        --shadow: 0 20px 60px rgba(15, 23, 42, 0.10);
        --radius: 22px;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(15, 118, 110, 0.12), transparent 30%),
            radial-gradient(circle at top right, rgba(180, 83, 9, 0.10), transparent 32%),
            linear-gradient(180deg, #fffaf2 0%, var(--bg) 100%);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(14, 116, 144, 0.08), rgba(255, 255, 255, 0.86));
        border-right: 1px solid var(--line);
    }

    .sidebar-shell {
        background: linear-gradient(180deg, rgba(15, 118, 110, 0.10), rgba(255, 255, 255, 0.72));
        border: 1px solid rgba(31, 41, 55, 0.08);
        border-radius: 22px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .hero {
        background: linear-gradient(135deg, rgba(15, 118, 110, 0.95), rgba(180, 83, 9, 0.92));
        color: white;
        border-radius: 30px;
        padding: 2.2rem 2.3rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
        margin-bottom: 1.25rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.8rem;
        line-height: 1.02;
        font-weight: 800;
    }

    .hero p {
        max-width: 820px;
        margin-top: 0.85rem;
        margin-bottom: 0;
        font-size: 1.03rem;
        color: rgba(255,255,255,0.92);
    }

    .section-card, .metric-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
        color: var(--text);
        padding: 1.3rem;
    }

    .metric-card {
        padding: 1rem;
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.35rem;
    }

    .stat-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--text);
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        background: rgba(15, 118, 110, 0.12);
        color: #0f766e;
        font-size: 0.82rem;
        font-weight: 700;
        margin-right: 0.45rem;
        margin-bottom: 0.45rem;
    }

    .subtle {
        color: var(--muted);
    }

    .stButton > button {
        border-radius: 999px;
        border: none;
        font-weight: 700;
        padding: 0.78rem 1.1rem;
        background: linear-gradient(135deg, var(--accent), #115e59);
        color: white;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        filter: brightness(1.04);
        transform: translateY(-1px);
    }

    .response-box {
        background: var(--panel-strong);
        border-left: 4px solid var(--accent);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .error-box {
        background: var(--panel-strong);
        border-left: 4px solid #dc2626;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }

    .success-box {
        background: var(--panel-strong);
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==================== API Helper Functions ====================
@st.cache_resource
def get_session():
    return requests.Session()

def api_get(path: str, timeout: int = TIMEOUT_SHORT):
    try:
        return get_session().get(f"{API_BASE_URL}{path}", timeout=timeout)
    except requests.exceptions.ConnectionError:
        return None

def api_post(path: str, timeout: int = TIMEOUT_LONG, **kwargs):
    try:
        return get_session().post(f"{API_BASE_URL}{path}", timeout=timeout, **kwargs)
    except requests.exceptions.ConnectionError:
        return None

def api_delete(path: str, timeout: int = TIMEOUT_SHORT):
    try:
        return get_session().delete(f"{API_BASE_URL}{path}", timeout=timeout)
    except requests.exceptions.ConnectionError:
        return None

@st.cache_data(ttl=10)
def get_documents():
    response = api_get("/api/documents", timeout=TIMEOUT_SHORT)
    if response and response.status_code == 200:
        return response.json().get("documents", []), response.json().get("count", 0)
    return [], 0

def check_api_connection():
    response = api_get("/", timeout=TIMEOUT_SHORT)
    return response is not None and response.status_code == 200

# ==================== UI Components ====================
def render_hero(title: str, subtitle: str, badges: list):
    badge_html = "".join(f'<span class="pill">{badge}</span>' for badge in badges)
    st.markdown(
        f'''
        <div class="hero">
            <div style="text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.72rem; opacity: 0.8; margin-bottom: 0.5rem;">AI Research Workspace</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div style="margin-top: 1rem;">{badge_html}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

def render_metric_card(label: str, value: str, desc: str):
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
            <div class="subtle">{desc}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

# ==================== Sidebar Navigation ====================
with st.sidebar:
    st.markdown(
        '''
        <div class="sidebar-shell">
            <div style="font-size: 1.05rem; font-weight: 800; margin-bottom: 0.35rem;">AI Research Assistant</div>
            <div class="subtle">Complete RAG system with multi-agent orchestration</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    page = st.radio(
        "Navigation",
        ["Dashboard", "Upload", "Manage Docs", "Ask Question", "Summarize", "Generate Quiz", "Citations", "About"],
        label_visibility="collapsed",
    )

    st.divider()
    
    # API Status
    st.markdown("#### System Status")
    api_connected = check_api_connection()
    if api_connected:
        st.success("Backend Online ✅")
    else:
        st.error("Backend Offline ❌")
    
    st.caption("Backend: FastAPI :8000")
    st.caption("Frontend: Streamlit")

# ==================== Get Cache Data ====================
documents, doc_count = get_documents()
api_connected = check_api_connection()

# ==================== Main Page Content ====================
if page == "Dashboard":
    render_hero(
        "AI Research Assistant",
        "Production-grade Multi-Agent RAG System. Upload PDFs, ask questions, generate summaries, and create quizzes with human approval.",
        ["Phase 4-8", "Multi-Agent", "LangGraph Orchestrated"],
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card("Documents", str(doc_count), "Processed and indexed")
    with col2:
        render_metric_card("Agents", "4", "Research, Summarizer, Quiz, Citation")
    with col3:
        render_metric_card("Features", "6", "Q&A, Summary, Quiz, Citations, Compare, Analyze")
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📋 Quick Actions")
        st.write("""
        - **Upload**: Add new PDFs/TXT files
        - **Ask**: Query documents with RAG
        - **Summarize**: Auto-generate summaries
        - **Quiz**: Create quizzes with approval workflow
        """)
    
    with col2:
        st.markdown("### 🎯 System Phases")
        st.write("""
        - ✅ Phase 4: Embeddings (sentence-transformers)
        - ✅ Phase 5: Vector DB (Chroma)
        - ✅ Phase 6: Retrieval (semantic search)
        - ✅ Phase 7: Generation (context-only LLM)
        - ✅ Phase 8: Multi-Agent (LangGraph)
        """)
    
    st.divider()
    
    if documents:
        st.markdown("### 📁 Recent Documents")
        for doc in documents[-3:]:
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.write(f"**{doc['original_filename']}**")
            with cols[1]:
                st.caption(f"{doc['file_size'] / (1024*1024):.2f} MB")
            with cols[2]:
                st.caption(doc['upload_time'][:10])
    else:
        st.info("No documents yet. Start by uploading a PDF or TXT file.")

elif page == "Upload":
    st.header("📤 Upload Documents")
    st.write("Upload PDF or TXT files to add them to the research database.")
    
    if not api_connected:
        st.error("❌ Backend is offline. Please start the API server.")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Upload File")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["pdf", "txt"],
                help="Max 50MB (configurable in backend)",
            )
            
            if uploaded_file:
                col_name, col_size = st.columns(2)
                with col_name:
                    st.metric("Filename", uploaded_file.name)
                with col_size:
                    st.metric("Size", f"{uploaded_file.size / (1024*1024):.2f} MB")
                
                if st.button("Upload & Process", use_container_width=True, type="primary"):
                    try:
                        with st.spinner("⏳ Uploading and embedding document..."):
                            files = {"file": (uploaded_file.name, uploaded_file.getbuffer())}
                            response = api_post("/api/documents/upload", files=files, timeout=TIMEOUT_LONG)
                        
                        if response and response.status_code == 200:
                            result = response.json()
                            st.markdown(
                                f'''
                                <div class="success-box">
                                    <strong>✅ Upload Successful!</strong><br>
                                    Document ID: {result['document_id']}<br>
                                    Status: {result['status']}<br>
                                    Ready for queries: {result['ready_for_queries']}
                                </div>
                                ''',
                                unsafe_allow_html=True,
                            )
                            st.json(result)
                            st.cache_data.clear()
                        else:
                            error_msg = response.text if response else "Connection failed"
                            st.markdown(
                                f'''
                                <div class="error-box">
                                    <strong>❌ Upload Failed</strong><br>
                                    {error_msg}
                                </div>
                                ''',
                                unsafe_allow_html=True,
                            )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            st.markdown("#### Info")
            st.info("✓ Supports PDF & TXT\n✓ Auto-embedded\n✓ Chunked & indexed")
            st.metric("Indexed", f"{doc_count} documents")

elif page == "Manage Docs":
    st.header("📁 Manage Documents")
    
    if not api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("No documents. Upload one to get started.")
    else:
        st.write(f"Managing {doc_count} documents")
        
        for doc in documents:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**{doc['original_filename']}**")
                    st.caption(f"ID: {doc['document_id']}")
                
                with col2:
                    st.metric("Size", f"{doc['file_size'] / (1024*1024):.2f} MB")
                    st.caption(f"Uploaded: {doc['upload_time'][:10]}")
                
                with col3:
                    if st.button("Delete", key=f"del_{doc['document_id']}", use_container_width=True):
                        response = api_delete(f"/api/documents/{doc['document_id']}")
                        if response and response.status_code == 200:
                            st.success("Deleted")
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()

elif page == "Ask Question":
    st.header("❓ Ask a Question")
    st.write("Ask questions about your documents. Answers are retrieved from the indexed content only (no hallucination).")
    
    if not api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("Upload documents first")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_area("Your question:", placeholder="What are the main topics covered?", height=100)
        
        with col2:
            st.markdown("#### Options")
            selected_doc_name = st.selectbox(
                "Filter by document (optional)",
                ["All documents"] + [d['original_filename'] for d in documents],
                label_visibility="collapsed"
            )
            doc_id = None
            if selected_doc_name != "All documents":
                doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc_name), None)
            
            top_k = st.slider("Results to retrieve", 1, 10, 5, label_visibility="collapsed")
        
        if query and st.button("Get Answer", use_container_width=True, type="primary"):
            try:
                with st.spinner("🔍 Searching and generating answer..."):
                    payload = {
                        "query": query,
                        "document_id": doc_id,
                        "top_k": top_k
                    }
                    response = api_post("/api/ask", json=payload, timeout=TIMEOUT_LONG)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        st.markdown(
                            f'''
                            <div class="response-box">
                                <strong>📝 Answer:</strong><br>
                                {result['answer']}
                            </div>
                            ''',
                            unsafe_allow_html=True,
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Chunks Retrieved", result['retrieved_chunks'])
                        with col2:
                            st.metric("Sources", len(result['sources']))
                        
                        if result['sources']:
                            st.markdown("#### 📚 Sources")
                            for source in result['sources']:
                                st.caption(f"[{source['index']}] {source['document_id']} (Similarity: {source['similarity']})")
                    else:
                        st.warning("No answer found")
                else:
                    st.error(f"Failed: {response.text if response else 'Connection error'}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "Summarize":
    st.header("📄 Generate Summary")
    st.write("Automatically summarize documents or query results.")
    
    if not api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("Upload documents first")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_doc_name = st.selectbox("Select document:", [d['original_filename'] for d in documents])
            doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc_name), None)
        
        with col2:
            length = st.radio("Summary length:", ["concise", "moderate", "detailed"], horizontal=True)
        
        if st.button("Generate Summary", use_container_width=True, type="primary"):
            try:
                with st.spinner("✍️ Generating summary..."):
                    payload = {"document_id": doc_id, "length": length}
                    response = api_post("/api/summary", json=payload, timeout=TIMEOUT_LONG)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        st.markdown(
                            f'''
                            <div class="response-box">
                                <strong>📝 Summary:</strong><br>
                                {result['summary']}
                            </div>
                            ''',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("Could not generate summary")
                else:
                    st.error(f"Failed: {response.text if response else 'Connection error'}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "Generate Quiz":
    st.header("🎓 Generate Quiz")
    st.write("Generate multiple-choice quiz questions with human-in-the-loop approval.")
    
    if not api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("Upload documents first")
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_doc_name = st.selectbox("Select document:", [d['original_filename'] for d in documents])
            doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc_name), None)
        
        with col2:
            num_questions = st.slider("Number of questions:", 1, 20, 5)
            require_approval = st.checkbox("Require approval", value=True, help="Human-in-the-Loop feature")
        
        if st.button("Generate Quiz", use_container_width=True, type="primary"):
            try:
                with st.spinner("🎓 Generating quiz..."):
                    payload = {
                        "document_id": doc_id,
                        "num_questions": num_questions,
                        "require_approval": require_approval
                    }
                    response = api_post("/api/quiz", json=payload, timeout=TIMEOUT_LONG)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['status'] == "pending_approval":
                        st.warning("⏳ Quiz generated and awaiting approval")
                        st.write(f"Quiz ID: {result['quiz_id']}")
                        
                        if result.get('preview_questions'):
                            st.markdown("**Preview Questions:**")
                            for i, q in enumerate(result['preview_questions'][:1], 1):
                                st.write(f"Q{i}: {q.get('question')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Approve Quiz", use_container_width=True):
                                approve_resp = api_post(
                                    f"/api/quiz/{result['quiz_id']}/approve",
                                    json={"approved": True}
                                )
                                if approve_resp and approve_resp.status_code == 200:
                                    st.success("Quiz approved!")
                        with col2:
                            if st.button("❌ Reject Quiz", use_container_width=True):
                                reject_resp = api_post(
                                    f"/api/quiz/{result['quiz_id']}/approve",
                                    json={"approved": False, "reason": "Quality check"}
                                )
                                if reject_resp and reject_resp.status_code == 200:
                                    st.warning("Quiz rejected")
                    
                    elif result['status'] == "success":
                        st.success("✅ Quiz generated successfully!")
                        st.write(f"Total questions: {result['num_questions']}")
                        
                        if result.get('questions'):
                            for i, q in enumerate(result['questions'], 1):
                                with st.container(border=True):
                                    st.write(f"**Q{i}: {q.get('question')}**")
                                    options = q.get('options', {})
                                    for key, opt in options.items():
                                        st.write(f"  {key}. {opt}")
                                    st.caption(f"Answer: {q.get('correct_answer')} - {q.get('explanation')}")
                else:
                    st.error(f"Failed: {response.text if response else 'Connection error'}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "Citations":
    st.header("📚 Get Citations")
    st.write("Retrieve citations for query results from your documents.")
    
    if not api_connected:
        st.error("❌ Backend offline")
    elif doc_count == 0:
        st.info("Upload documents first")
    else:
        query = st.text_area("Query for citations:", placeholder="Enter your search query")
        
        selected_doc_name = st.selectbox(
            "Filter by document (optional)",
            ["All documents"] + [d['original_filename'] for d in documents],
        )
        doc_id = None
        if selected_doc_name != "All documents":
            doc_id = next((d['document_id'] for d in documents if d['original_filename'] == selected_doc_name), None)
        
        if query and st.button("Get Citations", use_container_width=True, type="primary"):
            try:
                with st.spinner("🔍 Retrieving citations..."):
                    payload = {"query": query, "document_id": doc_id}
                    response = api_post("/api/citations", json=payload, timeout=TIMEOUT_LONG)
                
                if response and response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        st.write(f"Found {result['citation_count']} citations")
                        
                        for citation in result['citations']:
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"**[{citation['number']}]** {citation['snippet']}")
                                    st.caption(f"Document: {citation['document_id']}")
                                with col2:
                                    st.metric("Relevance", citation['relevance'])
                    else:
                        st.info("No citations found")
                else:
                    st.error(f"Failed: {response.text if response else 'Connection error'}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif page == "About":
    st.header("ℹ️ About")
    
    st.markdown("""
    ### AI Research Assistant
    
    A production-grade Multi-Agent RAG (Retrieval-Augmented Generation) system built for students and professionals.
    
    #### Phases Implemented
    
    - **Phase 4**: Embeddings using sentence-transformers (all-MiniLM-L6-v2)
    - **Phase 5**: Vector Database (Chroma DB) for semantic search
    - **Phase 6**: Retrieval System for context-based document search
    - **Phase 7**: Generation with OpenAI (context-only to prevent hallucination)
    - **Phase 8**: Multi-Agent System with LangGraph orchestration
    
    #### Features
    
    - 📤 **Document Upload**: PDF and TXT file support
    - ❓ **Question Answering**: RAG-powered semantic search
    - 📄 **Summarization**: Auto-generate document summaries
    - 🎓 **Quiz Generation**: MCQ creation with human approval
    - 📚 **Citations**: Source tracking and bibliography generation
    - 🔗 **Document Comparison**: Compare information across documents
    
    #### Agents
    
    1. **Research Agent**: Answer questions, compare documents, cross-document search
    2. **Summarizer Agent**: Generate summaries, extract key points
    3. **Quiz Agent**: Generate quizzes with human-in-the-loop approval
    4. **Citation Agent**: Manage citations and references
    
    #### Tech Stack
    
    - **Backend**: FastAPI, LangGraph, OpenAI
    - **Vector DB**: Chroma DB
    - **Embeddings**: sentence-transformers
    - **Frontend**: Streamlit
    - **Orchestration**: LangGraph (StateGraph)
    
    #### API Endpoints
    
    - `POST /api/documents/upload` - Upload & embed document
    - `POST /api/documents/{id}/analyze` - Full RAG analysis
    - `POST /api/ask` - Ask question with citations
    - `POST /api/summary` - Generate summary
    - `POST /api/quiz` - Generate quiz
    - `POST /api/citations` - Get citations
    
    #### Features Highlights
    
    ✅ **Hallucination Prevention**: Answers only from retrieved context  
    ✅ **Human-in-the-Loop**: Quiz approval before release  
    ✅ **Multi-Agent**: Specialized agents for different tasks  
    ✅ **LangGraph Orchestration**: State-based workflow management  
    ✅ **Semantic Search**: Context-aware document retrieval  
    ✅ **Citation Tracking**: Full source attribution  
    """)
    
    st.divider()
    st.caption("Built for education and research • 2026")
