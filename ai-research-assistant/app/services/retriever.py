"""
Retriever Service - Retrieves relevant documents and chunks from the database.
Phase 6: Retrieval using semantic search
"""
import logging
from typing import List, Dict, Optional

from app.services.embeddings import EmbeddingsService
from app.database.chroma_db import ChromaVectorDB

logger = logging.getLogger(__name__)


class RetrieverService:
    """Retrieve relevant chunks based on semantic similarity"""
    
    def __init__(self):
        """Initialize retriever with embeddings and vector DB"""
        self.embeddings_service = EmbeddingsService()
        self.vector_db = ChromaVectorDB()
    
    def retrieve(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant chunks for a query using semantic search
        
        Args:
            query: User's question or search query
            top_k: Number of top results to return
            document_id: Optional filter by specific document
            
        Returns:
            List of retrieved chunks with content, metadata, and similarity scores
        """
        try:
            logger.info(f"Retrieving top {top_k} chunks for query: {query[:100]}...")
            
            # Generate embedding for query
            query_embedding = self.embeddings_service.embed_text(query)
            
            # Search vector DB
            retrieved_chunks = self.vector_db.search(
                query_embedding=query_embedding,
                top_k=top_k,
                document_id=document_id
            )
            
            if not retrieved_chunks:
                logger.warning("No chunks retrieved")
                return []
            
            logger.info(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks")
            
            # Log retrieval with similarity scores
            for i, chunk in enumerate(retrieved_chunks):
                logger.debug(f"  [{i+1}] Similarity: {chunk['similarity']:.3f} | {chunk['text'][:80]}...")
            
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    def retrieve_and_format(self, query: str, top_k: int = 5, document_id: Optional[str] = None) -> str:
        """
        Retrieve chunks and format as context for LLM
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            document_id: Optional filter by document
            
        Returns:
            Formatted context string for LLM
        """
        chunks = self.retrieve(query, top_k, document_id)
        
        if not chunks:
            return "No relevant information found."
        
        # Format context
        context_parts = ["Relevant Information from Documents:"]
        context_parts.append("=" * 50)
        
        for i, chunk in enumerate(chunks):
            context_parts.append(f"\n[Source {i+1}] (Similarity: {chunk['similarity']:.2%})")
            context_parts.append(f"Document: {chunk['metadata'].get('document_id', 'Unknown')}")
            if chunk['metadata'].get('page'):
                context_parts.append(f"Page: {chunk['metadata']['page']}")
            context_parts.append("-" * 40)
            context_parts.append(chunk['text'])
        
        return "\n".join(context_parts)
    
    def retrieve_batch(self, queries: List[str], top_k: int = 5) -> Dict[str, List[Dict]]:
        """
        Retrieve chunks for multiple queries
        
        Args:
            queries: List of queries
            top_k: Number of top results per query
            
        Returns:
            Dictionary mapping queries to their retrieved chunks
        """
        results = {}
        for query in queries:
            results[query] = self.retrieve(query, top_k)
        return results

