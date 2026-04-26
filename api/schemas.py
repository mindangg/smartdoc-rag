from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer


class UploadProgressEvent(BaseModel):
    step: str
    message: str
    progress: int = Field(0, ge=0, le=100)
    chunk_count: Optional[int] = None
    total_vectors: Optional[int] = None
    error: Optional[str] = None

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=128)


class HistoryItem(BaseModel):
    id: int
    question: str
    rag_answer: Optional[str] = None
    corag_answer: Optional[str] = None
    created_at: str

class Citation(BaseModel):
    id: int
    type: str
    source: str
    title: str
    page: Optional[int] = None
    snippet: str
    url: Optional[str] = None

class QueryProgressEvent(BaseModel):
    step: str
    message: str
    score: Optional[float] = None
    decision: Optional[str] = None
    doc_count: Optional[int] = None
    web_count: Optional[int] = None
    result_count: Optional[int] = None
    used_web: Optional[bool] = None
    answer: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None
    relevance_score: Optional[float] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    vector_count: int
    llm_url: str
    model: str

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