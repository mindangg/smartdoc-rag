import asyncio
import logging
from typing import TypedDict, List, Dict, Any

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from core.llm import get_llm, ANTI_HALLUCINATION_SYSTEM_PROMPT
from core.rag_chain import format_context
from core.retriever import retrieve_with_scores
from features.corag.evaluator import evaluate_context_relevance
from features.corag.web_search import search_web, web_results_to_docs
from features.citation_tracker import build_citations

logger = logging.getLogger(__name__)

class CoRAGState(TypedDict):
    query: str
    retrieved_docs: List[Document]
    web_results: List[Dict[str, Any]]
    relevance_score: float
    relevance_decision: str
    combined_context: str
    answer: str
    citations: List[Dict[str, Any]]
    used_web: bool

def build_corag_graph(vector_store):

    def retrieve_node(state: CoRAGState) -> dict:
        results = retrieve_with_scores(state["query"], vector_store)
        docs = [doc for doc, _ in results]
        return {"retrieved_docs": docs}

    def evaluate_node(state: CoRAGState) -> dict:
        score, decision, _ = evaluate_context_relevance(
            state["query"], state["retrieved_docs"]
        )
        return {
            "relevance_score": score,
            "relevance_decision": decision,
        }

    def web_search_node(state: CoRAGState) -> dict:
        results = search_web(state["query"])
        return {"web_results": results, "used_web": True}

    def generate_node(state: CoRAGState) -> dict:
        combined_docs = list(state.get("retrieved_docs", []))
        web_docs = web_results_to_docs(state.get("web_results", []))
        all_docs = (combined_docs + web_docs)[:8]

        context = format_context(all_docs)
        system_content = ANTI_HALLUCINATION_SYSTEM_PROMPT.format(context=context)
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=state["query"]),
        ]

        llm = get_llm(streaming=False)
        response = llm.invoke(messages)

        citations = build_citations(
            state.get("retrieved_docs", []),
            state.get("web_results", []),
        )

        return {
            "combined_context": context,
            "answer": response.content,
            "citations": citations,
        }

    # ── Routing ────────────────────────────────────────────────────────────

    def route_after_evaluate(state: CoRAGState) -> str:
        return (
            "web_search"
            if state["relevance_decision"] == "insufficient"
            else "generate"
        )

    # ── Build graph ────────────────────────────────────────────────────────

    graph = StateGraph(CoRAGState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "web_search": "web_search",
            "generate": "generate",
        },
    )
    graph.add_edge("web_search", "generate")
    graph.add_edge("generate", END)

    return graph.compile()

async def run_corag_with_streaming(
    query: str,
    vector_store,
    event_queue: asyncio.Queue,
    session_id: str = "default"
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
            f"Độ liên quan: {score:.2f} → {'Đủ tốt' if decision == 'relevant' else 'Không đủ ⚠️'}",
            score=round(score, 3),
            decision=decision,
        )

        # ── Step 3: Web Search (conditional) ──────────────────────────────
        web_results: List[Dict[str, Any]] = []
        used_web = False

        if decision == "insufficient":
            await emit(
                "web_search",
                f"Context không đủ (score={score:.2f} < threshold). Đang tìm kiếm web…",
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
        system_content = ANTI_HALLUCINATION_SYSTEM_PROMPT
        
        from core.memory import get_chat_history
        history = get_chat_history(session_id)
        # Lấy 4 tin nhắn gần nhất (2 lượt hỏi-đáp)
        history_messages = history.messages[-4:] if len(history.messages) > 0 else []
        
        messages = [SystemMessage(content=system_content)]
        messages.extend(history_messages)
        
        # Nhét tài liệu trực tiếp vào câu hỏi
        user_content = f"TÀI LIỆU TRÍCH XUẤT (CONTEXT):\n{context}\n\nCÂU HỎI CỦA TÔI:\n{query}"
        messages.append(HumanMessage(content=user_content))

        llm = get_llm(streaming=False)
        response = await loop.run_in_executor(None, lambda: llm.invoke(messages))
        
        citations = build_citations(docs, web_results)
        
        # KHÔNG LƯU VÀO HISTORY Ở ĐÂY NỮA
        # RAG_CHAIN sẽ chịu trách nhiệm lưu để tránh bị ghi đúp 2 lần (Race Condition)

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
