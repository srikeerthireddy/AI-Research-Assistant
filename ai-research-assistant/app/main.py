"""
Main entry point for the AI Research Assistant application
FastAPI backend server

**IMPORTANT: Heavy model loading is deferred to lazy initialization**
This allows the server to start quickly and become ready for health checks.
Models are only loaded when first requested.
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from app.config import API_HOST, API_PORT, OPENAI_API_KEY
from app.services.document_service import DocumentService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("⏳ FastAPI server starting...")

# Initialize FastAPI app
app = FastAPI(
    title="AI Research Assistant",
    description="Production-grade Multi-Agent RAG System",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Lazy Loading for Heavy Services ====================
# These are initialized on-demand to avoid startup freeze
_services_cache = {
    "pdf_parser": None,
    "text_processor": None,
    "rag_workflow": None,
}

# Light-weight service (initialized immediately)
document_service = DocumentService()

def get_pdf_parser():
    """Lazy load PDF parser"""
    if _services_cache["pdf_parser"] is None:
        logger.info("📄 Loading PDF Parser...")
        from app.services.pdf_parser import PDFParser
        _services_cache["pdf_parser"] = PDFParser()
    return _services_cache["pdf_parser"]

def get_text_processor():
    """Lazy load text processor"""
    if _services_cache["text_processor"] is None:
        logger.info("✂️ Loading Text Processor...")
        from app.services.chunker import TextProcessor
        _services_cache["text_processor"] = TextProcessor()
    return _services_cache["text_processor"]

def get_rag_workflow():
    """Lazy load RAG workflow (heavy - loads all models)"""
    if _services_cache["rag_workflow"] is None:
        logger.info("🤖 Loading RAG Workflow (models will be initialized)...")
        from app.rag.workflow import RAGWorkflow
        _services_cache["rag_workflow"] = RAGWorkflow()
        logger.info("✅ RAG Workflow loaded successfully")
    return _services_cache["rag_workflow"]

# Check OpenAI API key
if not OPENAI_API_KEY:
    logger.warning("⚠️  OPENAI_API_KEY not set in .env file")


# ==================== Request Models ====================
class QueryRequest(BaseModel):
    """Request model for asking questions"""
    query: str
    document_id: str = None
    top_k: int = 5


class QuizRequest(BaseModel):
    """Request model for quiz generation"""
    document_id: str
    num_questions: int = 5
    require_approval: bool = True


class SummaryRequest(BaseModel):
    """Request model for summarization"""
    document_id: str = None
    query: str = None
    length: str = "moderate"


class CitationRequest(BaseModel):
    """Request model for citations"""
    query: str
    document_id: str = None


class AnalyzeRequest(BaseModel):
    """Request model for document analysis and chunking"""
    query: str = None
    chunk_size: int = 2000
    chunk_overlap: int = 200
    method: str = "fixed"
    compute_embeddings: bool = False
    preview_count: int = 3


class QuizApprovalRequest(BaseModel):
    """Request model for quiz approval"""
    approved: bool
    reason: str = ""


# ==================== Health & Utility ====================
@app.get("/")
async def health_check():
    """
    Fast health check endpoint - returns immediately without loading models.
    This allows Render to verify the server is up and accepting requests.
    """
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "service": "AI Research Assistant",
        "version": "0.1.0",
        "message": "Server is running. Models load on first request.",
        "agents": ["research", "summarizer", "quiz", "citation"]
    }

print("✅ FastAPI server ready! Health endpoint available at /")


# ==================== Document Management ====================
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or TXT)
    
    Returns:
    {
        "document_id": "uuid",
        "filename": "document.pdf",
        "size": 1024,
        "upload_time": "2026-05-08T10:30:00",
        "status": "uploaded"
    }
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Validate upload
        is_valid, error_msg = document_service.validate_upload(file.filename, len(contents))
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Save document
        metadata = document_service.save_document(file.filename, contents)
        document_id = metadata["document_id"]
        
        # Parse and embed document
        logger.info(f"Processing document for RAG: {document_id}")
        pdf_parser = get_pdf_parser()
        rag_workflow = get_rag_workflow()
        text_content = pdf_parser.extract_text(contents, file.filename)
        success = rag_workflow.process_document(document_id, text_content)
        
        if not success:
            logger.warning(f"Warning: Failed to process document for embeddings")
        
        logger.info(f"Document uploaded successfully: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": metadata["original_filename"],
            "size": metadata["file_size"],
            "upload_time": metadata["upload_time"],
            "status": "processed" if success else "uploaded",
            "ready_for_queries": success
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = document_service.list_documents()
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get document metadata"""
    try:
        metadata = document_service.get_document(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        success = document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": f"Document {document_id} deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RAG Pipeline Endpoints ====================

@app.post("/api/documents/{document_id}/analyze")
async def analyze_document(document_id: str, request: AnalyzeRequest | None = None):
    """
    Analyze a document and optionally return chunk previews for the frontend.

    If the request body is omitted, returns the Phase 2 text analysis payload.
    If chunking parameters are provided, returns chunking metrics and previews
    alongside the analysis payload.
    """
    try:
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")

        pdf_parser = get_pdf_parser()
        parsed_data = pdf_parser.extract_text(str(file_path))
        full_text = parsed_data.get("full_text", "")

        if parsed_data.get("ocr_error"):
            logger.warning(
                f"OCR fallback failed for document {document_id}: {parsed_data.get('ocr_error')}"
            )
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "document_id": document_id,
                    "error": "OCR fallback unavailable for this document",
                    "ocr_error": parsed_data.get("ocr_error"),
                    "extraction_quality": parsed_data.get("extraction_quality", {}),
                },
            )

        logger.debug(
            f"Analyze requested for {document_id} file={file_path} chars={len(full_text)}"
        )
        try:
            logger.debug(f"Parsed keys: {list(parsed_data.keys())}")
            logger.debug(f"Extraction quality: {parsed_data.get('extraction_quality')}")
        except Exception:
            logger.debug("Parsed data diagnostics unavailable")

        if not full_text or not full_text.strip():
            logger.warning(f"No text extracted for document {document_id}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "document_id": document_id,
                    "error": "No text extracted from document",
                    "extraction_quality": parsed_data.get("extraction_quality", {}),
                },
            )

        text_processor = get_text_processor()
        analysis = text_processor.process_text(full_text)

        if request is None:
            return {
                "success": True,
                "document_id": document_id,
                "analysis": analysis,
            }

        method = (request.method or "fixed").lower()
        preview_count = max(1, int(request.preview_count or 1))

        if method == "semantic":
            chunk_result = text_processor.split_into_semantic_chunks(
                text=full_text,
                target_chunk_size=max(200, int(request.chunk_size)),
                min_chunk_size=max(100, int(request.chunk_overlap) or 100),
                overlap=max(0, int(request.chunk_overlap)),
                respect_headers=True,
            )
            chunks = chunk_result.get("chunks", [])
            chunk_metadata = chunk_result.get("metadata", {})
        else:
            chunks = text_processor.split_into_chunks(
                full_text,
                chunk_size=max(1, int(request.chunk_size)),
                overlap=max(0, int(request.chunk_overlap)),
            )
            chunk_metadata = {
                "chunk_size": int(request.chunk_size),
                "chunk_overlap": int(request.chunk_overlap),
                "method": method,
            }

        preview_chunks = chunks[:preview_count]
        average_chunk_length = (
            round(sum(chunk.get("length", 0) for chunk in chunks) / len(chunks), 2)
            if chunks
            else 0
        )

        logger.info(f"Text analysis completed for document: {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "analysis": analysis,
            "metrics": {
                "num_chunks": len(chunks),
                "avg_chunk_length": average_chunk_length,
                "embeddings_computed": bool(request.compute_embeddings),
                "text_length": len(full_text),
                "word_count": analysis.get("statistics", {}).get("words", 0),
                "method": method,
                "chunk_metadata": chunk_metadata,
            },
            "preview_chunks": preview_chunks,
            "message": "Analysis complete" + (" with chunk previews" if request else ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
async def ask_question(request: QueryRequest):
    """
    Ask a question across documents using RAG
    
    Phase 6-7: Retrieval-Augmented Generation
    Returns answer with citations
    """
    try:
        logger.info(f"Question: {request.query[:80]}")
        
        rag_workflow = get_rag_workflow()
        result = rag_workflow.answer_question(request.query, request.document_id)
        
        return {
            "success": result.get("result", {}).get("status") == "success",
            "query": request.query,
            "answer": result.get("result", {}).get("answer"),
            "sources": result.get("result", {}).get("sources", []),
            "retrieved_chunks": result.get("result", {}).get("retrieved_chunks", 0)
        }
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Agent Endpoints ====================

@app.post("/api/summary")
async def generate_summary(request: SummaryRequest):
    """
    Generate document summary
    
    Uses SummarizerAgent (Phase 8)
    """
    try:
        logger.info(f"Generating summary for document")
        
        rag_workflow = get_rag_workflow()
        result = rag_workflow.summarize(request.document_id)
        
        return {
            "success": result.get("result", {}).get("status") == "success",
            "document_id": request.document_id,
            "summary": result.get("result", {}).get("summary", ""),
            "length": request.length
        }
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quiz")
async def generate_quiz(request: QuizRequest):
    """
    Generate quiz from document
    
    Uses QuizAgent with Human-in-the-Loop (Phase 8)
    """
    try:
        logger.info(f"Generating quiz for document: {request.document_id}")
        
        rag_workflow = get_rag_workflow()
        result = rag_workflow.generate_quiz(
            request.document_id,
            request.num_questions,
            request.require_approval
        )
        
        return {
            "success": result.get("status") in ["success", "pending_approval"],
            "status": result.get("status"),
            "document_id": request.document_id,
            "quiz_id": result.get("quiz_id"),
            "preview_questions": result.get("preview_questions"),
            "message": result.get("message", "Quiz generated successfully")
        }
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quiz/pending")
async def get_pending_quizzes():
    """
    Get all pending quiz approvals
    
    Human-in-the-Loop feature (Phase 8)
    """
    try:
        rag_workflow = get_rag_workflow()
        result = rag_workflow.quiz_agent.get_pending_quizzes()
        return result
    except Exception as e:
        logger.error(f"Error fetching pending quizzes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/quiz/{quiz_id}/approve")
async def approve_quiz(quiz_id: str, request: QuizApprovalRequest):
    """
    Approve quiz for release
    
    Human-in-the-Loop feature (Phase 8)
    """
    try:
        rag_workflow = get_rag_workflow()
        if request.approved:
            result = rag_workflow.quiz_agent.approve_quiz(quiz_id)
            logger.info(f"✅ Quiz approved: {quiz_id}")
        else:
            result = rag_workflow.quiz_agent.reject_quiz(quiz_id, request.reason)
            logger.info(f"Quiz rejected: {quiz_id}")
        
        return {
            "success": result.get("status") in ["approved", "rejected"],
            "status": result.get("status"),
            "quiz_id": quiz_id,
            "message": result.get("message", "")
        }
    except Exception as e:
        logger.error(f"Error processing quiz approval: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/citations")
async def get_citations(request: CitationRequest):
    """
    Get citations for query results
    
    Uses CitationAgent (Phase 8)
    """
    try:
        logger.info(f"Fetching citations for query")
        
        rag_workflow = get_rag_workflow()
        result = rag_workflow.get_citations(request.query, request.document_id)
        
        return {
            "success": result.get("result", {}).get("status") == "success",
            "query": request.query,
            "citation_count": result.get("result", {}).get("citation_count", 0),
            "citations": result.get("result", {}).get("citations", [])
        }
    except Exception as e:
        logger.error(f"Error fetching citations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Error Handlers ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )



@app.post("/api/documents/{document_id}/parse")
async def parse_document(document_id: str):
    """
    Parse a document to extract text
    
    Returns:
    {
        "full_text": "...",
        "pages": [...],
        "metadata": {...},
        "total_characters": 5000
    }
    """
    try:
        # Get document file path
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse document
        pdf_parser = get_pdf_parser()
        parsed_data = pdf_parser.extract_text(str(file_path))
        
        logger.info(f"Document parsed successfully: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "data": parsed_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{document_id}/chunks")
async def get_text_chunks(document_id: str, chunk_size: int = 1000, overlap: int = 100):
    """
    Split document text into chunks for processing
    
    Parameters:
    - chunk_size: Size of each chunk in characters
    - overlap: Character overlap between chunks
    
    Returns list of text chunks with metadata
    """
    try:
        # Get document file path
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse document
        parsed_data = pdf_parser.extract_text(str(file_path))
        full_text = parsed_data.get("full_text", "")
        
        # Split into chunks
        chunks = text_processor.split_into_chunks(full_text, chunk_size, overlap)
        
        logger.info(f"Created {len(chunks)} chunks for document: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "total_chunks": len(chunks),
            "chunk_size": chunk_size,
            "overlap": overlap,
            "chunks": chunks
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error chunking document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{document_id}/chunks/intelligent")
async def get_intelligent_chunks(
    document_id: str,
    target_chunk_size: int = 1000,
    min_chunk_size: int = 350,
    overlap: int = 120,
    respect_headers: bool = True,
):
    """
    Phase 3 intelligent chunking endpoint.

    Parameters:
    - target_chunk_size: Preferred chunk size in characters
    - min_chunk_size: Minimum chunk size before forced split
    - overlap: Character overlap copied from previous chunk tail
    - respect_headers: Keep heading boundaries when possible
    """
    try:
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")

        parsed_data = pdf_parser.extract_text(str(file_path))
        full_text = parsed_data.get("full_text", "")

        result = text_processor.split_into_semantic_chunks(
            text=full_text,
            target_chunk_size=target_chunk_size,
            min_chunk_size=min_chunk_size,
            overlap=overlap,
            respect_headers=respect_headers,
        )

        chunks = result.get("chunks", [])

        logger.info(f"Created {len(chunks)} intelligent chunks for document: {document_id}")

        return {
            "success": True,
            "document_id": document_id,
            "strategy": result.get("strategy", "semantic_v1"),
            "metadata": result.get("metadata", {}),
            "chunks": chunks,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in intelligent chunking: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/summary")
async def get_text_summary(document_id: str, sentences: int = 3):
    """
    Get an extractive summary of the document
    
    Parameters:
    - sentences: Number of sentences in summary
    
    Returns summary text and analysis
    """
    try:
        # Get document file path
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse document
        parsed_data = pdf_parser.extract_text(str(file_path))
        full_text = parsed_data.get("full_text", "")
        
        # Generate summary
        analysis = text_processor.process_text(full_text)
        summary = analysis.get("summary", "")
        
        logger.info(f"Summary generated for document: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "summary": summary,
            "statistics": analysis.get("statistics", {}),
            "section_count": len(analysis.get("sections", []))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", str(API_PORT)))
    uvicorn.run(
        app,
        host=API_HOST,
        port=port,
        log_level="info"
    )

