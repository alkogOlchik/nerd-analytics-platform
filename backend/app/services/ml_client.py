"""HTTP-клиент к внешнему ML-сервису (реализует команда ML).

Контракт ML-сервиса:
  POST {ML_SERVICE_URL}/query
  Body: {"query": str, "model": str}
  Response: {"answer": str, "model": str, ...}
"""

from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from backend.app.config import get_settings

settings = get_settings()


@dataclass
class MLQueryResult:
    answer: str
    model: str | None = None
    raw: dict | None = None


class MLClient:
    def __init__(self, base_url: str | None = None, timeout: float = 120.0) -> None:
        self.base_url = (base_url or settings.ML_SERVICE_URL).rstrip("/")
        self.timeout = timeout

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def query(self, text: str, model: str = "gemma4:e2b") -> MLQueryResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/query",
                    json={"query": text, "model": model},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ML service unavailable: {exc}",
            ) from exc

        answer = data.get("answer") or data.get("response") or ""
        if not answer and data:
            answer = str(data)
        return MLQueryResult(
            answer=answer.strip(),
            model=data.get("model"),
            raw=data,
        )


ml_client = MLClient()
