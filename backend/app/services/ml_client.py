"""HTTP-клиент к ML-сервису и резервный вызов Ollama (OpenAI-compatible API)."""

import asyncio
from dataclasses import dataclass
import logging

import httpx
from fastapi import HTTPException, status

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_ML_FALLBACK_ANSWER_MARKER = "Reasoning failed"

# Windows/VPN: системный прокси (Clash и т.п.) ломает localhost → 503 у Ollama/ML
_LOCAL_HTTP = httpx.AsyncClient(trust_env=False)


@dataclass
class MLQueryResult:
    answer: str
    model: str | None = None
    raw: dict | None = None
    source: str = "ml_agent"


class MLClient:
    def __init__(self, base_url: str | None = None, timeout: float = 300.0) -> None:
        self.base_url = (base_url or settings.ML_SERVICE_URL).rstrip("/")
        self.ollama_base = settings.OLLAMA_BASE_URL.rstrip("/")
        self.timeout = timeout

    async def health(self) -> bool:
        try:
            response = await _LOCAL_HTTP.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def _query_via_ml_agent(self, text: str, model: str) -> MLQueryResult | None:
        response = await _LOCAL_HTTP.post(
            f"{self.base_url}/query",
            json={"query": text, "model": model},
            timeout=self.timeout,
        )
        if response.status_code >= 500:
            logger.warning(
                "ML agent returned %s for /query, trying Ollama fallback",
                response.status_code,
            )
            return None
        response.raise_for_status()
        data = response.json()
        answer = (data.get("answer") or data.get("response") or "").strip()
        if not answer and data:
            answer = str(data)
        if _ML_FALLBACK_ANSWER_MARKER in answer:
            logger.warning("ML agent stub answer, trying Ollama fallback")
            return None
        return MLQueryResult(
            answer=answer,
            model=data.get("model"),
            raw=data,
            source="ml_agent",
        )

    async def _query_ollama_direct(self, text: str, model: str) -> MLQueryResult:
        url = f"{self.ollama_base}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": text}],
            "stream": False,
        }
        last_exc: httpx.HTTPError | None = None
        for attempt in range(3):
            try:
                response = await _LOCAL_HTTP.post(url, json=payload, timeout=self.timeout)
                if response.status_code == 503:
                    logger.warning("Ollama 503 (attempt %s/3), retrying…", attempt + 1)
                    await asyncio.sleep(2 + attempt * 2)
                    continue
                response.raise_for_status()
                data = response.json()
                break
            except httpx.HTTPError as exc:
                last_exc = exc
                logger.warning("Ollama request failed (attempt %s/3): %s", attempt + 1, exc)
                await asyncio.sleep(2 + attempt * 2)
        else:
            raise last_exc or httpx.HTTPStatusError(
                "Ollama unavailable after retries",
                request=None,
                response=None,
            )
        choices = data.get("choices") or []
        if not choices:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama returned empty choices",
            )
        answer = (choices[0].get("message") or {}).get("content") or ""
        if not str(answer).strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ollama returned empty answer",
            )
        return MLQueryResult(
            answer=str(answer).strip(),
            model=data.get("model") or model,
            raw=data,
            source="ollama",
        )

    async def query(self, text: str, model: str = "gemma4:e2b") -> MLQueryResult:
        ml_error: str | None = None
        try:
            result = await self._query_via_ml_agent(text, model)
            if result is not None:
                return result
            ml_error = "ML agent returned 5xx or stub answer"
        except httpx.HTTPError as exc:
            ml_error = str(exc)
            logger.warning("ML agent request failed: %s", exc)

        if not settings.ML_OLLAMA_FALLBACK:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ML service unavailable: {ml_error}",
            )

        try:
            return await self._query_ollama_direct(text, model)
        except httpx.HTTPError as exc:
            hint = (
                f"ML: {ml_error}; Ollama: {exc}. "
                f"Проверьте: ollama list, ollama run {model}, прогрейте модель."
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"LLM unavailable ({hint})",
            ) from exc


ml_client = MLClient()
