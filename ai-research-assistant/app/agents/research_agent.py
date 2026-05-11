"""
Research Agent - Coordinates research tasks and information gathering.
Phase 8: Multi-Agent System
"""
import logging
from typing import Dict, List, Optional
import json

from app.services.retriever import RetrieverService
from app.services.generator import GeneratorService

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Research agent for answering questions based on documents"""
    
    def __init__(self):
        """Initialize research agent with retriever and generator"""
        self.retriever = RetrieverService()
        self.generator = GeneratorService()
    
    def answer_query(self, query: str, document_id: Optional[str] = None, top_k: int = 5) -> Dict:
        """
        Answer a research question using retrieved context
        
        Args:
            query: Research question
            document_id: Optional filter to specific document
            top_k: Number of chunks to retrieve
            
        Returns:
            Dict with answer and sources
        """
        try:
            logger.info(f"Research Agent: Answering - {query[:80]}...")
            
            # Retrieve relevant chunks
            chunks = self.retriever.retrieve(query, top_k, document_id)
            
            if not chunks:
                return {
                    "status": "no_sources",
                    "query": query,
                    "answer": "I couldn't find relevant information in the documents.",
                    "sources": []
                }
            
            # Format context for LLM
            context = self.retriever.retrieve_and_format(query, top_k, document_id)
            
            # Generate answer
            answer = self.generator.generate_answer(query, context)
            
            # Extract sources
            sources = self._extract_sources(chunks)
            
            return {
                "status": "success",
                "query": query,
                "answer": answer,
                "sources": sources,
                "retrieved_chunks": len(chunks)
            }
        except Exception as e:
            logger.error(f"Research Agent Error: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "answer": None
            }
    
    def compare_documents(self, query: str, document_ids: List[str]) -> Dict:
        """
        Compare information across multiple documents
        
        Args:
            query: Comparison query
            document_ids: List of document IDs to compare
            
        Returns:
            Dict with comparison analysis
        """
        try:
            logger.info(f"Research Agent: Comparing across {len(document_ids)} documents")
            
            comparisons = {}
            for doc_id in document_ids:
                result = self.answer_query(query, document_id=doc_id, top_k=3)
                comparisons[doc_id] = result
            
            # Generate comparative analysis
            analysis_prompt = f"""Compare the following answers from different documents:
            
{json.dumps(comparisons, indent=2)}

Provide a comparative analysis highlighting similarities, differences, and unique insights."""
            
            return {
                "status": "success",
                "query": query,
                "individual_answers": comparisons,
                "document_count": len(document_ids)
            }
        except Exception as e:
            logger.error(f"Comparison Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def search_across_documents(self, query: str, top_k: int = 5) -> Dict:
        """
        Search across all documents and find connections
        
        Args:
            query: Search query
            top_k: Chunks per document
            
        Returns:
            Dict with search results and connections
        """
        try:
            logger.info(f"Research Agent: Searching across all documents")
            
            # Search without document filter (all documents)
            chunks = self.retriever.retrieve(query, top_k=top_k)
            
            # Group by document
            by_document = {}
            for chunk in chunks:
                doc_id = chunk["metadata"].get("document_id", "unknown")
                if doc_id not in by_document:
                    by_document[doc_id] = []
                by_document[doc_id].append(chunk)
            
            return {
                "status": "success",
                "query": query,
                "documents_found": len(by_document),
                "total_chunks": len(chunks),
                "documents": by_document
            }
        except Exception as e:
            logger.error(f"Cross-document Search Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def _extract_sources(chunks: List[Dict]) -> List[Dict]:
        """Extract source information from retrieved chunks"""
        sources = []
        for i, chunk in enumerate(chunks):
            source = {
                "index": i + 1,
                "document_id": chunk["metadata"].get("document_id", "unknown"),
                "chunk_index": chunk["metadata"].get("chunk_index", 0),
                "page": chunk["metadata"].get("page", None),
                "similarity": f"{chunk['similarity']:.2%}"
            }
            sources.append(source)
        return sources
