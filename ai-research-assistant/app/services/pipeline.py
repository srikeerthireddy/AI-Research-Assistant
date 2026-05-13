"""
Document Processing Pipeline Service
Handles: Upload → Parse → Chunk → Analyze workflow
Clean abstraction for document ingestion and processing
"""
import logging
from typing import Dict, List, Optional
from pathlib import Path
import uuid
from datetime import datetime

from app.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS
from app.services.document_service import DocumentService
from app.services.pdf_parser import PDFParser
from app.services.chunker import TextProcessor

logger = logging.getLogger(__name__)


class DocumentPipeline:
    """Clean pipeline for document processing"""
    
    def __init__(self):
        self.document_service = DocumentService()
        self.pdf_parser = PDFParser()
        self.text_processor = TextProcessor()
        self._rag_workflow = None

    def _get_rag_workflow(self):
        """Lazy load RAG workflow for embedding/indexing."""
        if self._rag_workflow is None:
            from app.rag.workflow import RAGWorkflow
            self._rag_workflow = RAGWorkflow()
        return self._rag_workflow

    def _index_document_for_retrieval(self, document_id: str, full_text: str) -> bool:
        """Embed and store document chunks in vector DB for Ask queries."""
        if not full_text or not full_text.strip():
            return False

        try:
            rag_workflow = self._get_rag_workflow()
            return rag_workflow.process_document(document_id, full_text)
        except Exception as e:
            logger.error(f"❌ Indexing error for {document_id}: {str(e)}")
            return False
    
    # ==================== PHASE 1: UPLOAD ====================
    def upload_document(self, filename: str, file_content: bytes) -> Dict:
        """
        Upload and validate document
        
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
            logger.info(f"📤 Uploading: {filename}")
            
            # Validate
            is_valid, error_msg = self.document_service.validate_upload(filename, len(file_content))
            if not is_valid:
                logger.warning(f"Validation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # Save
            metadata = self.document_service.save_document(filename, file_content)
            
            logger.info(f"✅ Uploaded: {metadata['document_id']}")
            return {
                "success": True,
                "document_id": metadata["document_id"],
                "filename": metadata["original_filename"],
                "size": metadata["file_size"],
                "upload_time": metadata["upload_time"],
                "status": "uploaded"
            }
        except Exception as e:
            logger.error(f"❌ Upload error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PHASE 2: PARSE ====================
    def parse_document(self, document_id: str) -> Dict:
        """
        Extract text from document
        
        Returns:
        {
            "success": True,
            "document_id": "uuid",
            "full_text": "...",
            "total_characters": 5000,
            "total_words": 800,
            "pages": 5,
            "extraction_quality": {...}
        }
        """
        try:
            logger.info(f"📄 Parsing: {document_id}")
            
            file_path = self.document_service.get_document_path(document_id)
            if not file_path:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            parsed_data = self.pdf_parser.extract_text(str(file_path))
            full_text = parsed_data.get("full_text", "")
            
            if not full_text or not full_text.strip():
                logger.warning(f"No text extracted: {document_id}")
                return {
                    "success": False,
                    "error": "No text extracted from document",
                    "extraction_quality": parsed_data.get("extraction_quality", {})
                }
            
            logger.info(f"✅ Parsed: {len(full_text)} characters")
            return {
                "success": True,
                "document_id": document_id,
                "full_text": full_text,
                "total_characters": len(full_text),
                "total_words": len(full_text.split()),
                "pages": len(parsed_data.get("pages", [])),
                "extraction_quality": parsed_data.get("extraction_quality", {})
            }
        except Exception as e:
            logger.error(f"❌ Parse error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PHASE 3: CHUNK ====================
    def chunk_document(
        self,
        document_id: str,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        method: str = "fixed",
        preview_count: int = 3
    ) -> Dict:
        """
        Split document into chunks
        
        Returns:
        {
            "success": True,
            "document_id": "uuid",
            "total_chunks": 10,
            "method": "fixed",
            "avg_chunk_size": 1950,
            "chunks": [
                {
                    "chunk_id": 0,
                    "text": "...",
                    "length": 2000,
                    "word_count": 350,
                    ...
                }
            ],
            "preview_chunks": [...],
            "metadata": {...}
        }
        """
        try:
            logger.info(f"✂️ Chunking: {document_id} (method={method})")
            
            file_path = self.document_service.get_document_path(document_id)
            if not file_path:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            parsed_data = self.pdf_parser.extract_text(str(file_path))
            full_text = parsed_data.get("full_text", "")
            
            if not full_text or not full_text.strip():
                return {
                    "success": False,
                    "error": "No text to chunk"
                }
            
            # Choose chunking method
            if method.lower() == "semantic":
                result = self.text_processor.split_into_semantic_chunks(
                    text=full_text,
                    target_chunk_size=max(200, int(chunk_size)),
                    min_chunk_size=max(100, int(chunk_overlap) or 100),
                    overlap=max(0, int(chunk_overlap)),
                    respect_headers=True,
                )
                chunks = result.get("chunks", [])
                metadata = result.get("metadata", {})
            else:
                chunks = self.text_processor.split_into_chunks(
                    full_text,
                    chunk_size=max(1, int(chunk_size)),
                    overlap=max(0, int(chunk_overlap)),
                )
                metadata = {
                    "chunk_size": int(chunk_size),
                    "chunk_overlap": int(chunk_overlap),
                    "method": "fixed",
                }
            
            # Calculate metrics
            avg_chunk_size = round(
                sum(chunk.get("length", 0) for chunk in chunks) / len(chunks), 2
            ) if chunks else 0
            
            preview_chunks = chunks[:max(1, preview_count)]

            # Ensure Ask endpoint can query these documents after chunking.
            indexed_for_queries = self._index_document_for_retrieval(document_id, full_text)
            
            logger.info(f"✅ Created {len(chunks)} chunks")
            return {
                "success": True,
                "document_id": document_id,
                "total_chunks": len(chunks),
                "method": method,
                "avg_chunk_size": avg_chunk_size,
                "chunks": chunks,
                "preview_chunks": preview_chunks,
                "metadata": metadata,
                "indexed_for_queries": indexed_for_queries
            }
        except Exception as e:
            logger.error(f"❌ Chunking error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== PHASE 4: ANALYZE ====================
    def analyze_document(self, document_id: str) -> Dict:
        """
        Analyze document structure and content
        
        Returns:
        {
            "success": True,
            "document_id": "uuid",
            "analysis": {
                "sections": [...],
                "summary": "...",
                "statistics": {...},
                "language_info": {...}
            },
            "quality_score": 0.85
        }
        """
        try:
            logger.info(f"🔬 Analyzing: {document_id}")
            
            file_path = self.document_service.get_document_path(document_id)
            if not file_path:
                return {
                    "success": False,
                    "error": "Document not found"
                }
            
            parsed_data = self.pdf_parser.extract_text(str(file_path))
            full_text = parsed_data.get("full_text", "")
            
            if not full_text or not full_text.strip():
                return {
                    "success": False,
                    "error": "No text to analyze"
                }
            
            analysis = self.text_processor.process_text(full_text)
            extraction_quality = parsed_data.get("extraction_quality", {})
            quality_score = extraction_quality.get("score", 50) / 100
            
            logger.info(f"✅ Analysis complete (quality: {quality_score:.2f})")
            return {
                "success": True,
                "document_id": document_id,
                "analysis": analysis,
                "quality_score": quality_score,
                "extraction_quality": extraction_quality
            }
        except Exception as e:
            logger.error(f"❌ Analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== COMBINED: FULL PIPELINE ====================
    def process_full_pipeline(
        self,
        document_id: str,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        method: str = "fixed"
    ) -> Dict:
        """
        Full pipeline: Parse → Chunk → Analyze
        
        Returns all results in single response
        """
        try:
            logger.info(f"🚀 Full pipeline: {document_id}")
            
            # Step 1: Parse
            parse_result = self.parse_document(document_id)
            if not parse_result.get("success"):
                return parse_result
            
            # Step 2: Chunk
            chunk_result = self.chunk_document(
                document_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                method=method,
                preview_count=3
            )
            if not chunk_result.get("success"):
                return chunk_result
            
            # Step 3: Analyze
            analyze_result = self.analyze_document(document_id)
            if not analyze_result.get("success"):
                return analyze_result
            
            logger.info(f"✅ Pipeline complete")
            return {
                "success": True,
                "document_id": document_id,
                "stages": {
                    "parse": {
                        "characters": parse_result.get("total_characters"),
                        "words": parse_result.get("total_words"),
                        "pages": parse_result.get("pages")
                    },
                    "chunk": {
                        "total_chunks": chunk_result.get("total_chunks"),
                        "method": chunk_result.get("method"),
                        "avg_chunk_size": chunk_result.get("avg_chunk_size"),
                        "preview_chunks": chunk_result.get("preview_chunks")
                    },
                    "analyze": {
                        "sections": len(analyze_result.get("analysis", {}).get("sections", [])),
                        "quality_score": analyze_result.get("quality_score"),
                        "summary": analyze_result.get("analysis", {}).get("summary", "")
                    }
                }
            }
        except Exception as e:
            logger.error(f"❌ Pipeline error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== UTILITIES ====================
    def list_documents(self) -> List[Dict]:
        """Get all documents"""
        return self.document_service.list_documents()
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict]:
        """Get document info"""
        return self.document_service.get_document(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document"""
        return self.document_service.delete_document(document_id)
