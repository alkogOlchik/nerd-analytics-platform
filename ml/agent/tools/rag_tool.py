"""RAG search tool over a local Chroma persistent collection."""

from __future__ import annotations

import logging
from typing import Any, Dict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from agent.config import settings

logger = logging.getLogger(__name__)


def _serialize_doc(doc: Document, score: float | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "content": doc.page_content,
        "metadata": doc.metadata or {},
    }
    if score is not None:
        payload["score"] = score
    return payload


def _collection_size(vectorstore: Chroma) -> int | None:
    """Best-effort count of vectors. Returns None if the underlying client
    doesn't expose a `count()` method (older Chroma versions)."""
    try:
        return int(vectorstore._collection.count())  # noqa: SLF001
    except Exception:  # noqa: BLE001
        return None


def _build_vectorstore() -> Chroma:
    embeddings = OllamaEmbeddings(
        model=settings.ollama_embeddings_model,
        base_url=settings.ollama_base_url,
    )
    return Chroma(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory,
        embedding_function=embeddings,
    )


def rag_status() -> Dict[str, Any]:
    """Lightweight introspection used by the HTTP API."""
    try:
        vectorstore = _build_vectorstore()
        size = _collection_size(vectorstore)
        return {
            "ok": True,
            "collection": settings.chroma_collection_name,
            "persist_dir": settings.chroma_persist_directory,
            "embeddings_model": settings.ollama_embeddings_model,
            "ollama_base_url": settings.ollama_base_url,
            "size": size,
        }
    except Exception as err:  # noqa: BLE001
        logger.exception("rag_status failed")
        return {
            "ok": False,
            "error_type": type(err).__name__,
            "error": str(err),
        }


def reset_collection() -> Dict[str, Any]:
    """Drop the entire collection. Returns a small summary."""
    try:
        vectorstore = _build_vectorstore()
        vectorstore.delete_collection()
        return {
            "ok": True,
            "collection": settings.chroma_collection_name,
            "persist_dir": settings.chroma_persist_directory,
            "message": "collection dropped",
        }
    except Exception as err:  # noqa: BLE001
        logger.exception("reset_collection failed")
        return {
            "ok": False,
            "error_type": type(err).__name__,
            "error": str(err),
        }


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
        size = _collection_size(vectorstore)
        if size == 0:
            return {
                "ok": False,
                "tool_name": "rag_search",
                "query": query,
                "results": [],
                "error": (
                    "Knowledge base is empty. Run `python -m agent.tools.rag_index "
                    "--source <path>` to ingest documents first."
                ),
                "collection": settings.chroma_collection_name,
                "persist_dir": settings.chroma_persist_directory,
            }
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
        results = [_serialize_doc(doc, score) for doc, score in docs_with_scores]
        logger.info(
            "rag_search query=%r k=%d -> %d results (collection size=%s)",
            query,
            k,
            len(results),
            size if size is not None else "?",
        )
        return {
            "ok": True,
            "tool_name": "rag_search",
            "query": query,
            "top_k": k,
            "results": results,
            "count": len(results),
        }
    except Exception as err:
        logger.exception("rag_search failed for query=%r", query)
        return {
            "ok": False,
            "tool_name": "rag_search",
            "query": query,
            "results": [],
            "error_type": type(err).__name__,
            "error": str(err),
        }

