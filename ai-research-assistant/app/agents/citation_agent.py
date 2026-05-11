"""
Citation Agent - Manages citations and references.
Phase 8: Multi-Agent System
"""
import logging
from typing import Dict, List, Optional

from app.services.retriever import RetrieverService

logger = logging.getLogger(__name__)


class CitationAgent:
    """Agent for managing citations and source references"""
    
    def __init__(self):
        """Initialize citation agent"""
        self.retriever = RetrieverService()
    
    def get_citations_for_query(self, query: str, document_id: Optional[str] = None, top_k: int = 5) -> Dict:
        """
        Get citations for query results
        
        Args:
            query: Query to get citations for
            document_id: Optional filter to specific document
            top_k: Number of citations
            
        Returns:
            Dict with formatted citations
        """
        try:
            logger.info(f"Citation Agent: Generating citations for query")
            
            # Retrieve relevant chunks
            chunks = self.retriever.retrieve(query, top_k, document_id)
            
            if not chunks:
                return {"status": "no_sources", "citations": []}
            
            # Format citations
            citations = self._format_citations(chunks)
            
            return {
                "status": "success",
                "query": query,
                "citation_count": len(citations),
                "citations": citations
            }
        except Exception as e:
            logger.error(f"Citation Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def get_full_citation(self, document_id: str, chunk_index: int) -> Dict:
        """
        Get full citation for a specific chunk
        
        Args:
            document_id: ID of document
            chunk_index: Index of chunk
            
        Returns:
            Dict with full citation info
        """
        try:
            return {
                "status": "success",
                "document_id": document_id,
                "chunk_index": chunk_index,
                "citation": self._format_single_citation(document_id, chunk_index)
            }
        except Exception as e:
            logger.error(f"Error getting full citation: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def generate_bibliography(self, document_ids: List[str]) -> Dict:
        """
        Generate bibliography for multiple documents
        
        Args:
            document_ids: List of document IDs
            
        Returns:
            Dict with formatted bibliography
        """
        try:
            logger.info(f"Citation Agent: Generating bibliography for {len(document_ids)} documents")
            
            bibliography = []
            for doc_id in document_ids:
                citation = self._format_single_citation(doc_id, 0)
                bibliography.append(citation)
            
            return {
                "status": "success",
                "document_count": len(document_ids),
                "bibliography": bibliography
            }
        except Exception as e:
            logger.error(f"Bibliography Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def _format_citations(chunks: List[Dict]) -> List[Dict]:
        """Format chunks into citations"""
        citations = []
        for i, chunk in enumerate(chunks):
            citation = {
                "number": i + 1,
                "document_id": chunk["metadata"].get("document_id", "Unknown"),
                "page": chunk["metadata"].get("page", "N/A"),
                "chunk_index": chunk["metadata"].get("chunk_index", 0),
                "snippet": chunk["text"][:150] + "...",
                "relevance": f"{chunk['similarity']:.2%}"
            }
            citations.append(citation)
        return citations
    
    @staticmethod
    def _format_single_citation(document_id: str, chunk_index: int) -> str:
        """
        Format single citation in APA-like style
        
        Args:
            document_id: Document ID
            chunk_index: Chunk index
            
        Returns:
            Formatted citation string
        """
        return f"Source: Document ID: {document_id}, Section: {chunk_index}"
    
    def get_source_metadata(self, document_id: str) -> Dict:
        """
        Get metadata about a source document
        
        Args:
            document_id: ID of document
            
        Returns:
            Dict with document metadata
        """
        try:
            # This would connect to document service in a full implementation
            return {
                "status": "success",
                "document_id": document_id,
                "metadata": {
                    "title": f"Document: {document_id}",
                    "source_type": "Research Document",
                    "upload_date": "Recent"
                }
            }
        except Exception as e:
            logger.error(f"Error getting source metadata: {str(e)}")
            return {"status": "error", "error": str(e)}
