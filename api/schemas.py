from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class UploadProgressEvent(BaseModel):
    step: str
    message: str
    progress: int = Field(0, ge=0, le=100)
    chunk_count: Optional[int] = None
    total_vectors: Optional[int] = None
    error: Optional[str] = None

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=64)

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
