"""
API Gateway — единая точка входа (порт 8000).

Запуск: uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000
Сервис приложения: uvicorn backend.app.main:app --host 0.0.0.0 --port 8001
"""

import logging
from contextlib import asynccontextmanager
from typing import Callable

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

PUBLIC_PATHS = {
    "/health",
    "/auth/register",
    "/auth/login",
    "/auth/admin/login",
    "/auth/admin/register",
    "/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc",
}

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path.rstrip("/") or "/"
        if path in PUBLIC_PATHS or path.startswith("/docs"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid token"})

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "access":
                return JSONResponse(status_code=401, content={"detail": "Invalid token type"})
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)


http_client = httpx.AsyncClient(timeout=300.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await http_client.aclose()


app = FastAPI(title="Нёрд-аналитика Gateway", lifespan=lifespan)
app.add_middleware(JWTAuthMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy(request: Request, full_path: str) -> Response:
    path = f"/{full_path}" if full_path else "/"
    target_base = settings.APP_SERVICE_URL.rstrip("/")

    url = f"{target_base}{path}"
    if request.url.query:
        url = f"{url}?{request.url.query}"

    body = await request.body()
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in {"host", "content-length"}
    }

    try:
        upstream = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
    except httpx.HTTPError as exc:
        logger.error("Proxy error for %s: %s", url, exc)
        return JSONResponse(status_code=502, content={"detail": "Upstream service unavailable"})

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        headers={
            k: v
            for k, v in upstream.headers.items()
            if k.lower() not in {"content-encoding", "transfer-encoding", "content-length"}
        },
        media_type=upstream.headers.get("content-type"),
    )
