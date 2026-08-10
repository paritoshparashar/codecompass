import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class TextEmbedder:
    """
    Handles text and code embedding using sentence-transformers.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Embeds a list of strings into a numpy array of vectors."""
        return self.model.encode(texts, show_progress_bar=False)

    def embed_file(self, file_path: Path) -> np.ndarray:
        """
        Reads a file, chunks it to respect token limits, embeds all chunks, 
        and averages them (Mean Pooling) to represent the entire file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                return np.zeros(self.dimension)

            # 1000 characters is roughly 250 tokens, safely under the 256 token limit.
            chunk_size = 1000
            chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
            
            # Batch embed all chunks at once (sentence-transformers handles batching efficiently)
            chunk_embeddings = self.model.encode(chunks, show_progress_bar=False)
            
            # Average the vectors along the first axis (axis=0) to get the file representation
            file_embedding = np.mean(chunk_embeddings, axis=0)
            return file_embedding
            
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return np.zeros(self.dimension)