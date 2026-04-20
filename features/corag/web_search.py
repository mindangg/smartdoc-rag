import os
import logging
from typing import List, Dict, Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)

MAX_RESULTS_DEFAULT = 5


def search_web(
        query: str,
        max_results: int = MAX_RESULTS_DEFAULT,
) -> List[Dict[str, Any]]:
    api_key = os.getenv("TAVILY_API_KEY", "").strip()

    if api_key and api_key != "":
        logger.info(f"Web search via Tavily: {query[:60]!r}")
        results = _tavily_search(query, max_results, api_key)
    else:
        logger.info(f"Web search via DuckDuckGo (no Tavily key): {query[:60]!r}")
        results = _duckduckgo_search(query, max_results)

    logger.info(f"Web search returned {len(results)} results.")
    return results


def web_results_to_docs(results: List[Dict[str, Any]]) -> List[Document]:
    docs = []
    for r in results:
        content = r.get("content", "").strip()
        if not content:
            continue
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": r.get("url", ""),
                    "title": r.get("title", "Web"),
                    "file_type": "web",
                    "type": "web",
                },
            )
        )
    return docs


def _tavily_search(
        query: str,
        max_results: int,
        api_key: str,
) -> List[Dict[str, Any]]:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=False,
        )
        return [
            {
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "url": r.get("url", ""),
                "source": "tavily",
            }
            for r in response.get("results", [])
            if r.get("content")
        ]
    except Exception as e:
        logger.warning(f"Tavily search failed: {e}. Falling back to DuckDuckGo.")
        return _duckduckgo_search(query, max_results)


def _duckduckgo_search(
        query: str,
        max_results: int,
) -> List[Dict[str, Any]]:
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "content": r.get("body", ""),
                        "url": r.get("href", ""),
                        "source": "duckduckgo",
                    }
                )
        return results
    except Exception as e:
        logger.error(f"DuckDuckGo search also failed: {e}")
        return []
