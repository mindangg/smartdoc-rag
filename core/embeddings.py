import os
import logging
from typing import List, Optional

from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

_embedding_model: Optional["MPNetEmbeddings"] = None


def get_embedding_model() -> "MPNetEmbeddings":
    global _embedding_model
    if _embedding_model is None:
        model_name = os.getenv(
            "EMBEDDING_MODEL",
            "paraphrase-multilingual-mpnet-base-v2",
        )
        logger.info(f"Loading embedding model: {model_name}")
        _embedding_model = MPNetEmbeddings(model_name)
        logger.info("Embedding model ready.")
    return _embedding_model


class MPNetEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = self._model.get_embedding_dimension()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self._model.encode(
            [text],
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embedding[0].tolist()

    def encode(self, texts: List[str], **kwargs):
        return self._model.encode(texts, normalize_embeddings=True, **kwargs)
