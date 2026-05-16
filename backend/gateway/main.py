"""
API Gateway — единая точка входа.

Запуск: uvicorn backend.gateway.main:app --reload
"""

from fastapi import FastAPI

from backend.app.api.v1 import analytics, auth, tickets
from backend.app.config import get_settings

settings = get_settings()

app = FastAPI(title="Нёрд Аналитика Gateway")

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(tickets.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
