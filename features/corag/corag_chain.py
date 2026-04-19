import asyncio
import logging
from typing import List, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage

from core.llm import get_llm, ANTI_HALLUCINATION_SYSTEM_PROMPT
from core.rag_chain import format_context
from core.retriever import retrieve_with_scores
from features.citation_tracker import build_citations
from features.corag.evaluator import evaluate_context_relevance
from features.corag.rewriter import rewrite_query
from features.corag.web_search import search_web, web_results_to_docs

logger = logging.getLogger(__name__)

async def run_corag_with_streaming(
    query: str,
    vector_store,
    event_queue: asyncio.Queue,
) -> None:

    async def emit(step: str, message: str, **extra) -> None:
        payload = {"source": "corag", "step": step, "message": message, **extra}
        await event_queue.put(payload)

    loop = asyncio.get_event_loop()

    try:
        if vector_store is None:
            await emit(
                "error",
                "Chưa có tài liệu nào được tải lên. Vui lòng upload tài liệu trước.",
            )
            return

        # ── Step 1: Retrieve ───────────────────────────────────────────────
        await emit("retrieval", "Đang tìm kiếm tài liệu liên quan trong Vector DB…")
        results = await loop.run_in_executor(
            None, lambda: retrieve_with_scores(query, vector_store)
        )
        docs = [doc for doc, _ in results]
        await emit(
            "retrieval_done",
            f"Truy xuất được {len(docs)} đoạn văn bản liên quan.",
            doc_count=len(docs),
        )

        # ── Step 2: Evaluate ───────────────────────────────────────────────
        await emit("evaluating", "Đang đánh giá chất lượng ngữ cảnh (CoRAG)…")
        score, decision, per_scores = await loop.run_in_executor(
            None, lambda: evaluate_context_relevance(query, docs)
        )
        await emit(
            "evaluation_done",
            f"Độ liên quan: {score:.2f} → {'Đủ tốt' if decision == 'relevant' else 'Không đủ'}",
            score=round(score, 3),
            decision=decision,
        )

        # ── Step 3: Rewrite and Re-retrieve (conditional) ───────────────────
        if decision == "insufficient":
            await emit(
                "rewriting_query", 
                "Context gốc chưa đủ tốt. Đang phân tích và viết lại câu truy vấn để thử tìm kiếm lại..."
            )
            rewritten = await loop.run_in_executor(None, lambda: rewrite_query(query))
            await emit("re_retrieval", f"Tìm kiếm lại với truy vấn: '{rewritten}'")
            
            new_results = await loop.run_in_executor(
                None, lambda: retrieve_with_scores(rewritten, vector_store)
            )
            new_docs = [doc for doc, _ in new_results]
            
            seen = set(d.page_content for d in docs)
            for d in new_docs:
                if d.page_content not in seen:
                    docs.append(d)
                    seen.add(d.page_content)
                    
            await emit("re_evaluating", "Đang đánh giá lại ngữ cảnh sau khi thử lại...")
            score, decision, _ = await loop.run_in_executor(
                None, lambda: evaluate_context_relevance(query, docs)
            )
            await emit(
                "re_evaluation_done",
                f"Độ liên quan mới: {score:.2f} → {'Đủ tốt' if decision == 'relevant' else 'Vẫn không đủ'}",
                score=round(score, 3),
                decision=decision,
            )

        # ── Step 4: Web Search (conditional) ──────────────────────────────
        web_results: List[Dict[str, Any]] = []
        used_web = False

        if decision == "insufficient":
            await emit(
                "web_search",
                f"Context vẫn chưa đủ (score={score:.2f} < threshold). Bắt đầu tìm kiếm web…",
                score=round(score, 3),
            )
            web_results = await loop.run_in_executor(None, lambda: search_web(query))
            used_web = True
            await emit(
                "web_search_done",
                f"Bổ sung {len(web_results)} kết quả từ web.",
                result_count=len(web_results),
            )
        else:
            await emit(
                "context_sufficient",
                f"Ngữ cảnh đủ tốt (score={score:.2f}). Bỏ qua web search.",
                score=round(score, 3),
            )

        # ── Step 4: Generate ───────────────────────────────────────────────
        await emit("generating", "Đang sinh câu trả lời từ Local LLM (Ollama)…")

        combined_docs = docs + web_results_to_docs(web_results)
        all_docs = combined_docs[:8]
        context = format_context(all_docs)
        system_content = ANTI_HALLUCINATION_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=query),
        ]

        llm = get_llm(streaming=False)
        response = await loop.run_in_executor(None, lambda: llm.invoke(messages))

        citations = build_citations(docs, web_results)

        # ── Final answer event ─────────────────────────────────────────────
        await emit(
            "answer",
            "Hoàn thành!",
            answer=response.content,
            citations=citations,
            used_web=used_web,
            relevance_score=round(score, 3),
            doc_count=len(docs),
            web_count=len(web_results),
        )

    except Exception as exc:
        logger.exception(f"CoRAG pipeline error: {exc}")
        await emit("error", f"Lỗi trong quá trình xử lý: {exc}")

    finally:
        pass
