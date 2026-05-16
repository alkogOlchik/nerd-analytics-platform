"""RAG search tool over a local Chroma persistent collection."""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from agent.config import settings


def _serialize_doc(doc: Document, score: float | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "content": doc.page_content,
        "metadata": doc.metadata or {},
    }
    if score is not None:
        payload["score"] = score
    return payload


def rag_search(query: str, top_k: int | None = None) -> Dict[str, Any]:
    """Search relevant chunks in Chroma by semantic similarity."""
    k = top_k or settings.rag_top_k
    if not query or not query.strip():
        return {
            "ok": False,
            "tool_name": "rag_search",
            "query": query,
            "results": [],
            "error": "Empty query is not allowed.",
        }

    try:
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embeddings_model,
            base_url=settings.ollama_base_url,
        )
        vectorstore = Chroma(
            collection_name=settings.chroma_collection_name,
            persist_directory=settings.chroma_persist_directory,
            embedding_function=embeddings,
        )
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
        results = [_serialize_doc(doc, score) for doc, score in docs_with_scores]
        return {
            "ok": True,
            "tool_name": "rag_search",
            "query": query,
            "top_k": k,
            "results": results,
            "count": len(results),
        }
    except Exception as err:
        return {
            "ok": False,
            "tool_name": "rag_search",
            "query": query,
            "results": [],
            "error_type": type(err).__name__,
            "error": str(err),
        }

