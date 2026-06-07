"""One-shot script to index the knowledge base documents into ChromaDB.

Run from the ml/ directory:
    python seed_knowledge_base.py

Or with a custom Chroma path:
    CHROMA_PERSIST_DIRECTORY=./chroma_db python seed_knowledge_base.py --reset
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Allow running from the ml/ directory without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.rag_index import index_directory

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent / "docs"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ChromaDB with knowledge base docs")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop the existing collection before indexing (full rebuild)",
    )
    args = parser.parse_args()

    if not DOCS_DIR.exists() or not any(DOCS_DIR.iterdir()):
        logger.error("Docs directory is empty or missing: %s", DOCS_DIR)
        sys.exit(1)

    doc_files = list(DOCS_DIR.rglob("*.md")) + list(DOCS_DIR.rglob("*.txt"))
    logger.info("Found %d document(s) in %s", len(doc_files), DOCS_DIR)
    for f in sorted(doc_files):
        logger.info("  %s", f.name)

    logger.info("Indexing into ChromaDB (reset=%s) …", args.reset)
    result = index_directory(DOCS_DIR, reset=args.reset)

    if result.get("ok"):
        logger.info(
            "Done: %d doc(s) → %d chunk(s) in collection '%s' at %s",
            result.get("docs", 0),
            result.get("indexed_chunks", 0),
            result.get("collection", ""),
            result.get("persist_dir", ""),
        )
    else:
        logger.error("Indexing failed: %s", result.get("error", result))
        sys.exit(1)


if __name__ == "__main__":
    main()
