from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.main import app
from backend.app.models.enums import UserRole


@pytest.fixture
def auth_client(client, sample_client):
    async def override_user():
        return CurrentUser(
            id=sample_client.id,
            username=sample_client.username,
            role=UserRole.client,
            email=sample_client.email,
            full_name=sample_client.full_name,
        )

    app.dependency_overrides[get_current_user] = override_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_ticket(auth_client, sample_ticket):
    deadline = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    with patch(
        "backend.app.api.v1.tickets.ticket_service.create_ticket",
        new_callable=AsyncMock,
        return_value=sample_ticket,
    ):
        response = await auth_client.post(
            "/tickets",
            json={
                "product": "веб-сервис",
                "priority": "medium",
                "deadline": deadline,
                "sla_ttfr_min": 60,
                "sla_ttr_min": 1440,
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "принято"
    assert data["product"] == "веб-сервис"


@pytest.mark.asyncio
async def test_list_tickets_requires_auth(client):
    response = await client.get("/tickets")
    assert response.status_code == 403
