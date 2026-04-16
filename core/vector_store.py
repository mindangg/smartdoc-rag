import os
import logging
from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from core.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")

_vector_store: Optional[FAISS] = None


def get_vector_store() -> Optional[FAISS]:
    global _vector_store
    if _vector_store is None:
        _vector_store = _load_from_disk()
    return _vector_store


def add_documents(documents: List[Document]) -> FAISS:
    global _vector_store
    embeddings = get_embedding_model()

    if not documents:
        raise ValueError("No documents provided to add_documents().")

    if _vector_store is None:
        logger.info(f"Creating new FAISS index with {len(documents)} documents…")
        _vector_store = FAISS.from_documents(documents, embeddings)
    else:
        logger.info(f"Adding {len(documents)} documents to existing FAISS index…")
        _vector_store.add_documents(documents)

    _save_to_disk(_vector_store)
    logger.info(f"FAISS index now contains {_vector_store.index.ntotal} vectors.")
    return _vector_store


def get_document_count() -> int:
    vs = get_vector_store()
    if vs is None:
        return 0
    return vs.index.ntotal

def _load_from_disk() -> Optional[FAISS]:
    path = Path(FAISS_INDEX_PATH)
    if not path.exists():
        logger.info("No existing FAISS index found — starting fresh.")
        return None
    try:
        embeddings = get_embedding_model()
        vs = FAISS.load_local(
            str(path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info(f"Loaded FAISS index with {vs.index.ntotal} vectors from {path}.")
        return vs
    except Exception as e:
        logger.warning(f"Failed to load FAISS index: {e}. Starting fresh.")
        return None


def _save_to_disk(vs: FAISS) -> None:
    path = Path(FAISS_INDEX_PATH)
    path.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(path))
    logger.info(f"FAISS index saved to {path}.")
