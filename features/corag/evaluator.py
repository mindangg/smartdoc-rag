import os
import logging
from typing import List, Tuple, Optional

from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.35"))
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MAX_PASSAGE_CHARS = 512 

_cross_encoder: Optional[CrossEncoder] = None


def get_cross_encoder() -> CrossEncoder:
    global _cross_encoder
    if _cross_encoder is None:
        logger.info(f"Loading cross-encoder: {CROSS_ENCODER_MODEL}")
        _cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
        logger.info("Cross-encoder ready.")
    return _cross_encoder


def evaluate_context_relevance(
    query: str,
    docs: List[Document],
    threshold: float = RELEVANCE_THRESHOLD,
) -> Tuple[float, str, List[float]]:
    if not docs:
        logger.info("No documents retrieved — context is insufficient.")
        return 0.0, "insufficient", []

    model = get_cross_encoder()
    pairs = [
        (query, doc.page_content[:MAX_PASSAGE_CHARS])
        for doc in docs
    ]

    scores: List[float] = model.predict(pairs).tolist()
    max_score = max(scores)

    decision = "relevant" if max_score >= threshold else "insufficient"

    logger.info(
        f"Context evaluation: max_score={max_score:.3f} "
        f"threshold={threshold} → {decision}"
    )

    return max_score, decision, scores
