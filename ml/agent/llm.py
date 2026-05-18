"""LLM client factory for OpenAI-compatible endpoints (vLLM / Ollama)."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from agent.config import settings


def get_llm(model: str | None = None) -> ChatOpenAI:
    """Create a configured ChatOpenAI client.

    The endpoint is expected to implement the OpenAI-compatible chat API.
    """
    return ChatOpenAI(
        model=model or settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_timeout_seconds,
    )
