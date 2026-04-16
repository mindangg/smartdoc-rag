from typing import List, Dict, Any

from langchain_core.documents import Document


def build_citations(
    retrieved_docs: List[Document],
    web_results: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:

    citations: List[Dict[str, Any]] = []
    seen_sources: set = set()

    for i, doc in enumerate(retrieved_docs, start=1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page")

        key = f"{source}::{page}"
        if key in seen_sources:
            continue
        seen_sources.add(key)

        snippet = doc.page_content
        if len(snippet) > 350:
            snippet = snippet[:350].rsplit(" ", 1)[0] + "…"

        citations.append(
            {
                "id": i,
                "type": "document",
                "source": source,
                "title": f"{source}" + (f" — Trang {page}" if page else ""),
                "page": page,
                "snippet": snippet,
                "url": None,
            }
        )

    # ── Web citations ──────────────────────────────────────────────────────
    if web_results:
        offset = len(citations)
        for j, result in enumerate(web_results, start=1):
            url = result.get("url", "")
            if url in seen_sources:
                continue
            seen_sources.add(url)

            content = result.get("content", "")
            snippet = content[:350].rsplit(" ", 1)[0] + "…" if len(content) > 350 else content

            citations.append(
                {
                    "id": offset + j,
                    "type": "web",
                    "source": result.get("title", url),
                    "title": result.get("title", url),
                    "page": None,
                    "snippet": snippet,
                    "url": url,
                }
            )

    return citations
