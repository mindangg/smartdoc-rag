import os
import logging
from typing import List, Optional

from api.schemas import MPNetEmbeddings

logger = logging.getLogger(__name__)

_embedding_model: Optional["MPNetEmbeddings"] = None

def get_embedding_model() -> MPNetEmbeddings | None:
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
