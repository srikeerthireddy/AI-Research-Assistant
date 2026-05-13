"""
Clean API Endpoints for Upload → Chunking → Analyze Pipeline
Refactored from main.py for better organization
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import logging

from app.services.pipeline import DocumentPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Initialize pipeline (will be shared across requests)
pipeline = None

def get_pipeline() -> DocumentPipeline:
    """Lazy load pipeline"""
    global pipeline
    if pipeline is None:
        logger.info("Initializing DocumentPipeline...")
        pipeline = DocumentPipeline()
    return pipeline


# ==================== UPLOAD ENDPOINT ====================
@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF or TXT)
    
    Returns:
    {
        "success": True,
        "document_id": "uuid",
        "filename": "document.pdf",
        "size": 1024,
        "upload_time": "2026-05-13T10:30:00",
        "status": "uploaded"
    }
    """
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Read file
        contents = await file.read()
        
        # Process
        pipeline_service = get_pipeline()
        result = pipeline_service.upload_document(file.filename, contents)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PARSE ENDPOINT ====================
@router.post("/{document_id}/parse")
async def parse_document(document_id: str):
    """
    Extract text from document
    
    Returns:
    {
        "success": True,
        "document_id": "uuid",
        "full_text": "...",
        "total_characters": 5000,
        "pages": 5
    }
    """
    try:
        logger.info(f"Parsing document: {document_id}")
        
        pipeline_service = get_pipeline()
        result = pipeline_service.parse_document(document_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CHUNK ENDPOINT ====================
@router.post("/{document_id}/chunk")
async def chunk_document(
    document_id: str,
    chunk_size: int = Query(2000, ge=100, le=10000),
    chunk_overlap: int = Query(200, ge=0, le=1000),
    method: str = Query("fixed", regex="^(fixed|semantic)$"),
    preview_count: int = Query(3, ge=1, le=10)
):
    """
    Split document into chunks
    
    Parameters:
    - chunk_size: Size of each chunk (100-10000 chars)
    - chunk_overlap: Overlap between chunks (0-1000 chars)
    - method: 'fixed' or 'semantic'
    - preview_count: Number of chunks to preview (1-10)
    
    Returns:
    {
        "success": True,
        "document_id": "uuid",
        "total_chunks": 10,
        "method": "fixed",
        "avg_chunk_size": 1950,
        "preview_chunks": [...],
        "metadata": {...}
    }
    """
    try:
        logger.info(f"Chunking document: {document_id}")
        
        pipeline_service = get_pipeline()
        result = pipeline_service.chunk_document(
            document_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            method=method,
            preview_count=preview_count
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chunking error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYZE ENDPOINT ====================
@router.post("/{document_id}/analyze")
async def analyze_document(document_id: str):
    """
    Analyze document structure and content quality
    
    Returns:
    {
        "success": True,
        "document_id": "uuid",
        "analysis": {
            "sections": [...],
            "summary": "...",
            "statistics": {...}
        },
        "quality_score": 0.85
    }
    """
    try:
        logger.info(f"Analyzing document: {document_id}")
        
        pipeline_service = get_pipeline()
        result = pipeline_service.analyze_document(document_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FULL PIPELINE ENDPOINT ====================
@router.post("/{document_id}/pipeline")
async def full_pipeline(
    document_id: str,
    chunk_size: int = Query(2000, ge=100, le=10000),
    chunk_overlap: int = Query(200, ge=0, le=1000),
    method: str = Query("fixed", regex="^(fixed|semantic)$")
):
    """
    Execute full pipeline: Parse → Chunk → Analyze
    
    Returns results from all stages combined
    """
    try:
        logger.info(f"Running full pipeline: {document_id}")
        
        pipeline_service = get_pipeline()
        result = pipeline_service.process_full_pipeline(
            document_id,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            method=method
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== LIST DOCUMENTS ====================
@router.get("")
async def list_documents():
    """Get all documents"""
    try:
        pipeline_service = get_pipeline()
        documents = pipeline_service.list_documents()
        
        return {
            "success": True,
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GET DOCUMENT ====================
@router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document metadata"""
    try:
        pipeline_service = get_pipeline()
        metadata = pipeline_service.get_document_metadata(document_id)
        
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


# ==================== DELETE DOCUMENT ====================
@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        pipeline_service = get_pipeline()
        success = pipeline_service.delete_document(document_id)
        
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
