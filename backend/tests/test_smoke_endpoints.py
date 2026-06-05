"""Smoke: новые эндпоинты зарегистрированы в OpenAPI и отвечают без 5xx."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app

NEW_ROUTES = [
    ("POST", "/auth/change-password"),
    ("PATCH", "/auth/me"),
    ("POST", "/auth/admin/register"),
    ("POST", "/ai/chat/attachments"),
    ("POST", "/notifications/read-all"),
    ("PATCH", "/notifications/00000000-0000-0000-0000-000000000001"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", NEW_ROUTES)
async def test_route_exists_not_500(method: str, path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        if method == "POST":
            response = await client.post(path, json={})
        elif method == "PATCH":
            response = await client.patch(path, json={})
        else:
            response = await client.request(method, path)
    assert response.status_code != 500, response.text
