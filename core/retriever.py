import os
import logging
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

TOP_K_DEFAULT = int(os.getenv("TOP_K_RETRIEVAL", "5"))


def retrieve_with_scores(
    query: str,
    vector_store: FAISS,
    k: int = TOP_K_DEFAULT,
) -> List[Tuple[Document, float]]:
    results = vector_store.similarity_search_with_score(query, k=k)
    logger.debug(f"Retrieved {len(results)} docs for query: {query[:60]!r}")
    return results


def retrieve(
    query: str,
    vector_store: FAISS,
    k: int = TOP_K_DEFAULT,
) -> List[Document]:
    return [doc for doc, _ in retrieve_with_scores(query, vector_store, k=k)]
