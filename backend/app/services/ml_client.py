"""HTTP-клиент к ML-сервису."""

from dataclasses import dataclass
import logging

import httpx
from fastapi import HTTPException, status

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

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
        self.timeout = timeout

    async def health(self) -> bool:
        try:
            response = await _LOCAL_HTTP.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def query(self, text: str, model: str = "gemma4:e2b") -> MLQueryResult:
        try:
            response = await _LOCAL_HTTP.post(
                f"{self.base_url}/query",
                json={"query": text, "model": model},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("ML service request failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ML service unavailable: {exc}",
            ) from exc

        data = response.json()
        answer = (data.get("answer") or data.get("response") or "").strip()
        if not answer:
            answer = str(data)

        return MLQueryResult(
            answer=answer,
            model=data.get("model"),
            raw=data,
            source="ml_agent",
        )


ml_client = MLClient()
