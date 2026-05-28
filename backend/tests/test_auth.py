from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.models.user import Client
from backend.app.schemas.auth import TokenResponse


@pytest.mark.asyncio
async def test_register_success(client, db_session, sample_client):
    with patch(
        "backend.app.api.v1.auth.auth_service.register_client",
        new_callable=AsyncMock,
        return_value=sample_client,
    ):
        response = await client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "secret123",
                "full_name": "Test User",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_returns_tokens(client):
    tokens = TokenResponse(access_token="access", refresh_token="refresh")
    with patch(
        "backend.app.api.v1.auth.auth_service.login",
        new_callable=AsyncMock,
        return_value=tokens,
    ):
        response = await client.post(
            "/auth/login",
            json={"username": "testuser", "password": "secret123"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "access"
    assert data["refresh_token"] == "refresh"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    response = await client.get("/auth/me")
    assert response.status_code == 403
