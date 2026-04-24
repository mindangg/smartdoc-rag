import os
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from core.database import SessionLocal, UploadedFile
from core.memory import get_chat_history
from core.vector_store import FAISS_INDEX_PATH

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/documents")
def get_documents(session_id: str = "default"):
    with SessionLocal() as db:
        docs = db.query(UploadedFile).filter(UploadedFile.session_id == session_id).all()
        return [
            {
                "id": doc.id,
                "name": doc.filename,
                "chunks": doc.chunk_count,
                "uploadedAt": doc.uploaded_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for doc in docs
        ]

@router.get("/history/chat")
def get_chat_history_api(session_id: str = "default"):
    try:
        history = get_chat_history(session_id)
        messages = []
        for msg in history.messages:
            # exclude system messages to keep it clean for frontend if there are any
            if msg.type in ["human", "ai"]:
                messages.append({
                    "role": "user" if msg.type == "human" else "assistant",
                    "content": msg.content,
                    "citations": msg.additional_kwargs.get("citations", []),
                    "used_web": msg.additional_kwargs.get("used_web", False)
                })
        return {"status": "success", "messages": messages}
    except Exception as e:
        logger.exception("Error fetching chat history")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/chat")
def clear_chat_history(session_id: str = "default"):
    try:
        history = get_chat_history(session_id)
        history.clear()
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        logger.exception("Error clearing chat history")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/documents")
def clear_documents(session_id: str = "default"):
    try:
        # Clear FAISS
        path = Path(FAISS_INDEX_PATH)
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
        
        # Clear _vector_store global
        import core.vector_store
        core.vector_store._vector_store = None

        # Clear DB records
        with SessionLocal() as db:
            db.query(UploadedFile).filter(UploadedFile.session_id == session_id).delete()
            db.commit()
            
        return {"status": "success", "message": "Documents and Vector Store cleared"}
    except Exception as e:
        logger.exception("Error clearing documents")
        raise HTTPException(status_code=500, detail=str(e))
