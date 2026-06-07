"""Centralized project configuration.

This module keeps runtime settings in one place and loads optional overrides
from environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application settings used across agent components."""

    # LLM / vLLM (OpenAI-compatible API)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "ollama")
    llm_model: str = os.getenv("LLM_MODEL", "gemma4:e4b")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

    # Vector store (prepared for rag_tool.py)
    chroma_persist_directory: str = os.getenv(
        "CHROMA_PERSIST_DIRECTORY",
        "./chroma_db",
    )
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "documents")
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "6"))
    ollama_embeddings_model: str = os.getenv(
        "OLLAMA_EMBEDDINGS_MODEL",
        "nomic-embed-text",
    )
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Code executor
    code_execution_timeout_seconds: int = int(
        os.getenv("CODE_EXECUTION_TIMEOUT_SECONDS", "10")
    )
    code_execution_python_bin: str = os.getenv("CODE_EXECUTION_PYTHON_BIN", "python3")
    code_execution_max_output_chars: int = int(
        os.getenv("CODE_EXECUTION_MAX_OUTPUT_CHARS", "8000")
    )


settings = Settings()
