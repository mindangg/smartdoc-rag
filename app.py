"""
SmartDoc RAG — FastAPI Application Entry Point
============================================
Intelligent Document Q&A System with Standard RAG + CoRAG
"""

import os
from dotenv import load_dotenv

# Load env before importing modules that read env vars
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import upload, query, history
from core.database import init_db

app = FastAPI(
    title="SmartDoc RAG API",
    description="Intelligent Document Q&A System combining Standard RAG and Corrective RAG (CoRAG)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup_event():
    init_db()

# ---- CORS ---------------------------------------------------------------
# Allow React dev server + production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # CRA / other
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes -------------------------------------------------------------
app.include_router(upload.router, prefix="/api", tags=["Document Upload"])
app.include_router(query.router, prefix="/api", tags=["Query"])
app.include_router(history.router, prefix="/api", tags=["History"])


# ---- Health check -------------------------------------------------------
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "running",
        "service": "SmartDoc RAG API",
        "version": "1.0.0",
    }


@app.get("/api/health", tags=["Health"])
async def health():
    from core.vector_store import get_document_count
    return {
        "status": "ok",
        "vector_count": get_document_count(),
        "llm_url": os.getenv("NGROK_LLM_URL", "not set"),
        "model": os.getenv("OLLAMA_MODEL", "not set"),
    }
