"""CLI to ingest local documents into the Chroma collection used by `rag_search`.

Usage:
    python -m agent.tools.rag_index --source ./docs
    python -m agent.tools.rag_index --source ./docs --reset

Supported file types: .md, .markdown, .txt, .rst.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Iterable, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from agent.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {".md", ".markdown", ".txt", ".rst"}
DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "docs"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def _iter_files(source: Path) -> Iterable[Path]:
    if source.is_file():
        if source.suffix.lower() in SUPPORTED_EXTS:
            yield source
        return
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def _load_documents(source: Path) -> list[Document]:
    docs: list[Document] = []
    for path in _iter_files(source):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError as exc:
            logger.warning("Skip %s: %s", path, exc)
            continue
        if not text:
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source": str(path),
                    "filename": path.name,
                    "ext": path.suffix.lower(),
                },
            )
        )
    return docs


def _build_vectorstore(embeddings: OllamaEmbeddings, persist_dir: Path) -> Chroma:
    return Chroma(
        collection_name=settings.chroma_collection_name,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )


def index_directory(
    source: Path,
    *,
    reset: bool = False,
    persist_directory: Optional[Path] = None,
) -> dict:
    """Read documents, chunk them and add to Chroma. Returns a summary dict."""
    if not source.exists():
        return {
            "ok": False,
            "error": f"Source does not exist: {source}",
            "indexed_chunks": 0,
        }

    documents = _load_documents(source)
    if not documents:
        return {
            "ok": False,
            "error": f"No supported documents under {source}. "
            f"Allowed extensions: {sorted(SUPPORTED_EXTS)}",
            "indexed_chunks": 0,
        }

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    if not chunks:
        return {"ok": False, "error": "Splitting produced 0 chunks", "indexed_chunks": 0}

    persist_dir = persist_directory or Path(settings.chroma_persist_directory)
    persist_dir.mkdir(parents=True, exist_ok=True)

    embeddings = OllamaEmbeddings(
        model=settings.ollama_embeddings_model,
        base_url=settings.ollama_base_url,
    )

    vectorstore = _build_vectorstore(embeddings, persist_dir)
    if reset:
        try:
            vectorstore.delete_collection()
            logger.info("Dropped existing collection '%s'", settings.chroma_collection_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Drop collection failed (continuing): %s", exc)
        vectorstore = _build_vectorstore(embeddings, persist_dir)

    vectorstore.add_documents(chunks)

    return {
        "ok": True,
        "docs": len(documents),
        "indexed_chunks": len(chunks),
        "persist_dir": str(persist_dir),
        "collection": settings.chroma_collection_name,
        "embeddings_model": settings.ollama_embeddings_model,
    }


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index documents into Chroma")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to a file or directory to index (default: ./docs)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop the existing collection before indexing",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    _setup_logging(args.verbose)
    logger.info("Indexing %s (reset=%s)", args.source, args.reset)
    result = index_directory(args.source, reset=args.reset)
    print(result)
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
