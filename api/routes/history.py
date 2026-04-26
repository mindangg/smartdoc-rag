"""
History & Vector Store management API routes.
"""
import logging

from fastapi import APIRouter, Query

from core.history_store import clear_history, get_history
from core.vector_store import clear_vector_store, get_document_count

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history")
async def list_history(session_id: str = Query("default", max_length=128)):
    items = get_history(session_id)
    return {"session_id": session_id, "items": items, "count": len(items)}


@router.delete("/history")
async def delete_history(session_id: str = Query("default", max_length=128)):
    deleted = clear_history(session_id)
    logger.info(f"Cleared {deleted} history rows for session={session_id!r}")
    return {"deleted": deleted, "session_id": session_id}


@router.delete("/vectorstore")
async def delete_vectorstore():
    clear_vector_store()
    return {"deleted": True, "vector_count": get_document_count()}
