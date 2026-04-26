import asyncio
import json
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import QueryRequest
from core.vector_store import get_document_count, get_vector_store
from core.history_store import save_qa
from features.corag.corag_chain import run_corag_with_streaming
from core.rag_chain import run_rag_with_streaming

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query")
async def query_documents(request: QueryRequest):
    question = request.question.strip()
    session_id = request.session_id
    logger.info(f"Query received: {question[:80]!r}  session={session_id}")

    async def generate():
        queue: asyncio.Queue = asyncio.Queue()
        vector_store = get_vector_store()

        # Collect final answers for history saving
        answers: dict = {"rag": None, "corag": None}

        task_rag = asyncio.create_task(
            run_rag_with_streaming(question, vector_store, queue)
        )
        task_corag = asyncio.create_task(
            run_corag_with_streaming(question, vector_store, queue)
        )

        async def wait_all():
            results = await asyncio.gather(task_rag, task_corag, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.exception(f"Task error: {r}")
                    await queue.put({"source": "system", "step": "error", "message": f"❌ Lỗi: {r}"})
            await queue.put(None)

        asyncio.create_task(wait_all())

        while True:
            event = await queue.get()
            if event is None:
                break

            # Capture final answers for history
            if event.get("step") == "answer":
                src = event.get("source")
                if src == "rag":
                    answers["rag"] = event.get("answer")
                elif src == "corag":
                    answers["corag"] = event.get("answer")

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # Persist Q&A to history DB
        try:
            save_qa(
                session_id=session_id,
                question=question,
                rag_answer=answers["rag"],
                corag_answer=answers["corag"],
            )
        except Exception as exc:
            logger.warning(f"Failed to save history: {exc}")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/stats")
async def get_stats():
    return {
        "vector_count": get_document_count(),
        "status": "ready" if get_document_count() > 0 else "empty",
    }
