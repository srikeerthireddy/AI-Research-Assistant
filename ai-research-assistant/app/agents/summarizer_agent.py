"""
Summarizer Agent - Generates summaries of research content.
Phase 8: Multi-Agent System
"""
import logging
from typing import Dict, Optional

from app.services.retriever import RetrieverService
from app.services.generator import GeneratorService

logger = logging.getLogger(__name__)


class SummarizerAgent:
    """Agent for summarizing documents and content"""
    
    def __init__(self):
        """Initialize summarizer with retriever and generator"""
        self.retriever = RetrieverService()
        self.generator = GeneratorService()
    
    def summarize_document(self, document_id: str, length: str = "moderate") -> Dict:
        """
        Summarize entire document
        
        Args:
            document_id: ID of document to summarize
            length: "concise", "moderate", or "detailed"
            
        Returns:
            Dict with summary
        """
        try:
            logger.info(f"Summarizer Agent: Summarizing document {document_id}")
            
            # Retrieve all key chunks from document
            query = "main topics key concepts important points"
            chunks = self.retriever.retrieve(query, top_k=10, document_id=document_id)
            
            if not chunks:
                return {"status": "error", "message": "No content to summarize"}
            
            # Combine chunk text
            full_content = "\\n\\n".join([c["text"] for c in chunks])
            
            # Generate summary
            summary = self.generator.generate_summary(full_content, length)
            
            return {
                "status": "success",
                "document_id": document_id,
                "summary": summary,
                "length": length,
                "chunks_used": len(chunks)
            }
        except Exception as e:
            logger.error(f"Summarizer Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def summarize_query_results(self, query: str, document_id: Optional[str] = None) -> Dict:
        """
        Summarize the search results for a query
        
        Args:
            query: Search query
            document_id: Optional filter to specific document
            
        Returns:
            Dict with summary of results
        """
        try:
            logger.info(f"Summarizer Agent: Summarizing results for query")
            
            # Retrieve relevant chunks
            chunks = self.retriever.retrieve(query, top_k=5, document_id=document_id)
            
            if not chunks:
                return {"status": "error", "message": "No results to summarize"}
            
            # Combine content
            combined_content = "\\n\\n".join([c["text"] for c in chunks])
            
            # Generate summary
            summary = self.generator.generate_summary(combined_content, "moderate")
            
            return {
                "status": "success",
                "query": query,
                "summary": summary,
                "source_chunks": len(chunks)
            }
        except Exception as e:
            logger.error(f"Query Summarization Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def extract_key_points(self, document_id: Optional[str] = None) -> Dict:
        """
        Extract key points and topics from document(s)
        
        Args:
            document_id: Optional filter to specific document
            
        Returns:
            Dict with key topics
        """
        try:
            logger.info(f"Summarizer Agent: Extracting key points")
            
            query = "summary overview key findings conclusions recommendations"
            chunks = self.retriever.retrieve(query, top_k=15, document_id=document_id)
            
            if not chunks:
                return {"status": "error", "message": "No content found"}
            
            # Extract topics from chunks
            combined_content = "\\n\\n".join([c["text"] for c in chunks])
            topics = self.generator.extract_topics(combined_content)
            
            return {
                "status": "success",
                "topics": topics,
                "document_id": document_id,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            logger.error(f"Key Point Extraction Error: {str(e)}")
            return {"status": "error", "error": str(e)}
