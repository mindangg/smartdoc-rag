import logging
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage

from core.llm import get_llm, ANTI_HALLUCINATION_SYSTEM_PROMPT
from core.retriever import retrieve_with_scores
from core.vector_store import get_vector_store

logger = logging.getLogger(__name__)

def format_context(docs: List[Document]) -> str:
    if not docs:
        return "Không có thông tin ngữ cảnh."

    parts: List[str] = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")
        file_type = doc.metadata.get("file_type", doc.metadata.get("type", ""))

        label = f"[Nguồn {i}] {source}"
        if page:
            label += f" — Trang {page}"
        if file_type == "web":
            label = f"[Web {i}] {source}"

        parts.append(f"{label}:\n{doc.page_content}")

    return "\n\n" + ("─" * 60 + "\n\n").join(parts)

async def run_standard_rag(query: str) -> Dict[str, Any]:
    vs = get_vector_store()
    if vs is None:
        return {
            "answer": (
                "Chưa có tài liệu nào được tải lên. "
                "Vui lòng upload tài liệu trước."
            ),
            "docs": [],
            "context": "",
            "used_web": False,
        }

    results = retrieve_with_scores(query, vs)
    docs = [doc for doc, _ in results]

    logger.info(f"Standard RAG retrieved {len(docs)} docs for: {query[:60]!r}")

    context = format_context(docs)
    system_content = ANTI_HALLUCINATION_SYSTEM_PROMPT.format(context=context)
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=query),
    ]

    llm = get_llm()
    response = await llm.ainvoke(messages)

    return {
        "answer": response.content,
        "docs": docs,
        "context": context,
        "used_web": False,
    }

async def run_rag_with_streaming(
    query: str,
    vector_store,
    event_queue,
) -> None:
    async def emit(step: str, message: str, **extra) -> None:
        payload = {"source": "rag", "step": step, "message": message, **extra}
        await event_queue.put(payload)

    import asyncio
    loop = asyncio.get_event_loop()

    try:
        if vector_store is None:
            await emit("error", "Chưa có tài liệu nào được tải lên.")
            return

        await emit("retrieval", "Đang tìm kiếm tài liệu (RAG)...")
        results = await loop.run_in_executor(
            None, lambda: retrieve_with_scores(query, vector_store)
        )
        docs = [doc for doc, _ in results]
        await emit("retrieval_done", f"RAG tìm được {len(docs)} tài liệu.", doc_count=len(docs))

        await emit("generating", "Đang sinh câu trả lời (RAG)...")
        context = format_context(docs)
        system_content = ANTI_HALLUCINATION_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]

        llm = get_llm(streaming=False)
        response = await loop.run_in_executor(None, lambda: llm.invoke(messages))
        
        from features.citation_tracker import build_citations
        citations = build_citations(docs, [])

        await emit(
            "answer", 
            "Hoàn thành RAG!", 
            answer=response.content,
            citations=citations,
            used_web=False,
            doc_count=len(docs)
        )

    except Exception as exc:
        logger.exception(f"RAG pipeline error: {exc}")
        await emit("error", f"Lỗi RAG: {exc}")
    finally:
        pass
