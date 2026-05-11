"""
Chroma Database - Vector database for storing and retrieving embeddings.
Phase 5: Vector Database Integration
"""
import logging
import uuid
from typing import List, Dict, Optional
import chromadb

from app.config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)


class ChromaVectorDB:
    """Chroma DB wrapper for storing and retrieving embeddings"""
    
    def __init__(self, db_path: str = CHROMA_DB_PATH, collection_name: str = CHROMA_COLLECTION_NAME):
        """
        Initialize Chroma DB client
        
        Args:
            db_path: Path to store Chroma DB
            collection_name: Name of the collection to work with
        """
        try:
            logger.info(f"Initializing Chroma DB at {db_path}")
            
            # Initialize Chroma client with persistent storage using new API
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection_name = collection_name
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine distance for embeddings
            )
            
            logger.info(f"✅ Chroma DB initialized. Collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error initializing Chroma DB: {str(e)}")
            raise
    
    def add_chunks(self, document_id: str, chunks: List[Dict]) -> bool:
        """
        Store chunks with embeddings in the vector DB
        
        Args:
            document_id: ID of the document
            chunks: List of chunks with format:
                {
                    "text": "chunk content",
                    "embedding": [vector],
                    "metadata": {"page": 1, ...}
                }
                
        Returns:
            True if successful
        """
        if not chunks:
            logger.warning("No chunks provided for storage")
            return False
        
        try:
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{i}"
                ids.append(chunk_id)
                embeddings.append(chunk["embedding"])
                documents.append(chunk["text"])
                
                # Add metadata
                metadata = chunk.get("metadata", {})
                metadata["document_id"] = document_id
                metadata["chunk_index"] = i
                metadatas.append(metadata)
            
            # Store in Chroma
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"✅ Stored {len(chunks)} chunks for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding chunks: {str(e)}")
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 5, document_id: Optional[str] = None) -> List[Dict]:
        """
        Search for similar chunks (Phase 6: Retrieval)
        
        Args:
            query_embedding: Embedding vector of the query
            top_k: Number of top results to return
            document_id: Optional filter by specific document
            
        Returns:
            List of retrieved chunks with metadata
        """
        try:
            # Build where filter if document_id provided
            where = None
            if document_id:
                where = {"document_id": {"$eq": document_id}}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            retrieved_chunks = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    retrieved_chunks.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": float(results["distances"][0][i]),  # Lower is better for cosine
                        "similarity": 1 - float(results["distances"][0][i])  # Convert to similarity
                    })
            
            logger.debug(f"Retrieved {len(retrieved_chunks)} chunks")
            return retrieved_chunks
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks for a document
        
        Args:
            document_id: ID of document to delete
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(
                where={"document_id": {"$eq": document_id}}
            )
            logger.info(f"✅ Deleted all chunks for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "embedding_dimension": self.get_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings in this collection"""
        try:
            # Get a sample to determine dimension
            data = self.collection.get(limit=1)
            if data and data["embeddings"] and len(data["embeddings"]) > 0:
                return len(data["embeddings"][0])
            return 384  # Default for all-MiniLM-L6-v2
        except:
            return 384

