"""RAG search tool: hybrid dense (Chroma) + sparse (BM25) with RRF merging."""

from __future__ import annotations

import logging
import pickle
import re
from pathlib import Path
from typing import Any, Dict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from agent.config import settings

logger = logging.getLogger(__name__)

BM25_INDEX_FILENAME = "bm25_index.pkl"
RRF_K = 60  # standard constant for Reciprocal Rank Fusion

# Module-level cache so BM25 is loaded once per process.
_bm25_cache: Dict[str, Any] = {}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _load_bm25(persist_dir: str) -> Dict[str, Any] | None:
    """Load BM25 payload from disk; return None if index doesn't exist yet."""
    if persist_dir in _bm25_cache:
        return _bm25_cache[persist_dir]
    path = Path(persist_dir) / BM25_INDEX_FILENAME
    if not path.exists():
        logger.warning("BM25 index not found at %s — run indexing first", path)
        return None
    try:
        with path.open("rb") as fh:
            payload = pickle.load(fh)  # noqa: S301
        _bm25_cache[persist_dir] = payload
        logger.info("BM25 index loaded: %d chunks", len(payload["chunks"]))
        return payload
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load BM25 index: %s", exc)
        return None


def _bm25_search(query: str, k: int, persist_dir: str) -> list[Dict[str, Any]]:
    """Return top-k BM25 results as list of {content, metadata, bm25_score}."""
    payload = _load_bm25(persist_dir)
    if payload is None:
        return []
    tokens = _tokenize(query)
    if not tokens:
        return []
    scores = payload["bm25"].get_scores(tokens)
    chunks = payload["chunks"]
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
    return [
        {"content": chunks[i]["content"], "metadata": chunks[i]["metadata"], "bm25_score": float(s)}
        for i, s in ranked
        if s > 0
    ]


def _rrf_merge(
    vector_results: list[Dict[str, Any]],
    bm25_results: list[Dict[str, Any]],
    top_k: int,
) -> list[Dict[str, Any]]:
    """Merge two ranked lists with Reciprocal Rank Fusion.

    Uses content as the deduplication key. The final score field reflects
    the combined RRF score for logging; individual source scores are preserved.
    """
    scores: Dict[str, float] = {}
    docs: Dict[str, Dict[str, Any]] = {}

    for rank, doc in enumerate(vector_results):
        key = doc["content"]
        scores[key] = scores.get(key, 0.0) + 1.0 / (rank + 1 + RRF_K)
        if key not in docs:
            docs[key] = {**doc, "vector_rank": rank + 1}

    for rank, doc in enumerate(bm25_results):
        key = doc["content"]
        scores[key] = scores.get(key, 0.0) + 1.0 / (rank + 1 + RRF_K)
        if key not in docs:
            docs[key] = {**doc, "bm25_rank": rank + 1}
        else:
            docs[key]["bm25_rank"] = rank + 1
            docs[key]["bm25_score"] = doc.get("bm25_score")

    merged = sorted(docs.values(), key=lambda d: scores[d["content"]], reverse=True)
    for doc in merged:
        doc["rrf_score"] = round(scores[doc["content"]], 6)
    return merged[:top_k]


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
    """Hybrid search: dense (Chroma) + sparse (BM25), merged with RRF."""
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

        # Dense retrieval: fetch more candidates for RRF (2× top_k).
        fetch_k = k * 2
        docs_with_scores = vectorstore.similarity_search_with_score(query, k=fetch_k)
        vector_results = [_serialize_doc(doc, score) for doc, score in docs_with_scores]

        # Sparse retrieval: BM25 over the same corpus.
        bm25_results = _bm25_search(query, fetch_k, settings.chroma_persist_directory)

        # Merge with Reciprocal Rank Fusion.
        if bm25_results:
            results = _rrf_merge(vector_results, bm25_results, k)
            retrieval_mode = "hybrid"
        else:
            results = vector_results[:k]
            retrieval_mode = "vector_only"

        logger.info(
            "rag_search query=%r k=%d -> %d results mode=%s (collection size=%s)",
            query,
            k,
            len(results),
            retrieval_mode,
            size if size is not None else "?",
        )
        return {
            "ok": True,
            "tool_name": "rag_search",
            "query": query,
            "top_k": k,
            "results": results,
            "count": len(results),
            "retrieval_mode": retrieval_mode,
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

