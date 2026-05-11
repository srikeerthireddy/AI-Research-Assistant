"""
Main entry point for the AI Research Assistant application
FastAPI backend server
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os

from app.config import API_HOST, API_PORT, OPENAI_API_KEY
from app.services.document_service import DocumentService
from app.services.pdf_parser import PDFParser
from app.services.chunker import TextProcessor
from app.rag.workflow import RAGWorkflow

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# Initialize services
document_service = DocumentService()
pdf_parser = PDFParser()
text_processor = TextProcessor()
rag_workflow = RAGWorkflow()

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


class QuizApprovalRequest(BaseModel):
    """Request model for quiz approval"""
    approved: bool
    reason: str = ""


# ==================== Health & Utility ====================
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Research Assistant",
        "version": "0.1.0",
        "agents": ["research", "summarizer", "quiz", "citation"]
    }


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
async def analyze_document(document_id: str, request: QueryRequest):
    """
    Comprehensive document analysis using RAG pipeline
    
    Phase 4-7: Embeddings → Retrieval → Generation
    """
    try:
        logger.info(f"Analyzing document: {document_id}")
        
        # Use RAG workflow
        result = rag_workflow.answer_question(request.query, document_id)
        
        return {
            "success": result.get("result", {}).get("status") == "success",
            "document_id": document_id,
            "query": request.query,
            "result": result.get("result", {})
        }
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


# ============================================
# Phase 2: Advanced Parsing & Text Analysis
# ============================================

@app.post("/api/documents/{document_id}/analyze")
async def analyze_text(document_id: str):
    """
    Analyze extracted text for structure and content quality
    
    Returns detailed analysis of document structure, sections, and quality metrics
    """
    try:
        # Get document file path
        file_path = document_service.get_document_path(document_id)
        if not file_path:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Parse document first
        parsed_data = pdf_parser.extract_text(str(file_path))
        full_text = parsed_data.get("full_text", "")

        if parsed_data.get("ocr_error"):
            logger.warning(f"OCR fallback failed for document {document_id}: {parsed_data.get('ocr_error')}")
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

        # Diagnostic logging for debugging analyze flow
        logger.debug(f"Analyze requested for {document_id} file={file_path} chars={len(full_text)}")
        try:
            logger.debug(f"Parsed keys: {list(parsed_data.keys())}")
            logger.debug(f"Extraction quality: {parsed_data.get('extraction_quality')}" )
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

        # Analyze text
        analysis = text_processor.process_text(full_text)
        
        logger.info(f"Text analysis completed for document: {document_id}")
        
        return {
            "success": True,
            "document_id": document_id,
            "analysis": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
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
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )

