"""
Embeddings Service - Generates vector embeddings for text chunks.
Phase 4: Embeddings Generation using sentence-transformers
"""
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Generate embeddings using sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embeddings service
        
        Args:
            model_name: Sentence transformer model to use
                - all-MiniLM-L6-v2: Fast, lightweight (384 dims)
                - all-mpnet-base-v2: Higher quality (768 dims)
                - paraphrase-multilingual-mpnet-base-v2: Multilingual support
        """
        self.model_name = model_name
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Embeddings model loaded. Dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading embeddings model: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text chunk
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.embedding_dim
        
        try:
            embedding = self.model.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text chunks
        Efficient batch processing
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            logger.warning("Empty text list provided for embedding")
            return []
        
        try:
            # Filter out empty texts
            non_empty_texts = [t for t in texts if t and t.strip()]
            
            if not non_empty_texts:
                logger.warning("All texts are empty")
                return [[0.0] * self.embedding_dim for _ in texts]
            
            # Batch encode for efficiency
            embeddings = self.model.encode(non_empty_texts, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            e1 = np.array(embedding1)
            e2 = np.array(embedding2)
            similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0

