"""
Embedding model wrapper
Handles text to vector conversion
"""
from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np


class EmbeddingModel:
    """Wrapper for sentence transformer model"""
    
    def __init__(self, model_name: str):
        print(f"🔄 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded (dimension: {self.dimension})")
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Convert text(s) to embeddings
        
        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar
            
        Returns:
            numpy array of embeddings
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
    
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text (convenience method)"""
        return self.encode(text) if isinstance(text, str) else self.encode([text])


# Singleton instance
_embedding_model = None

def get_embedding_model(model_name: str = None) -> EmbeddingModel:
    """Get or create embedding model instance"""
    global _embedding_model
    
    if _embedding_model is None:
        from config.settings import EMBEDDING_MODEL
        model_name = model_name or EMBEDDING_MODEL
        _embedding_model = EmbeddingModel(model_name)
    
    return _embedding_model