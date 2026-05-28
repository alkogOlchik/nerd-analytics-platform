import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.main import app
from backend.app.models.enums import EmployeeRole, TicketStatus, UserRole
from backend.app.schemas.analytics_extended import AIEfficiencyResponse, TicketAnomaliesResponse
from backend.app.schemas.ticket_extended import GuestTicketResponse, GuestTrackResponse


@pytest.fixture
def employee_user():
    return CurrentUser(
        id=uuid.uuid4(),
        username="operator1",
        role=UserRole.employee,
        employee_role=EmployeeRole.analyst.value,
    )


@pytest.fixture
def analyst_client(client, employee_user):
    async def override_user():
        return employee_user

    app.dependency_overrides[get_current_user] = override_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_guest_ticket(client):
    guest_response = GuestTicketResponse(
        ticket_id=uuid.uuid4(),
        guest_token="token-abc",
        status=TicketStatus.accepted.value,
    )
    with patch(
        "backend.app.api.v1.tickets.ticket_service.create_guest_ticket",
        new_callable=AsyncMock,
        return_value=guest_response,
    ):
        response = await client.post(
            "/tickets/guest",
            json={
                "product": "веб-сервис",
                "priority": "medium",
                "message": "Не работает вход",
                "guest_email": "guest@example.com",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["guest_token"] == "token-abc"
    assert data["status"] == "принято"


@pytest.mark.asyncio
async def test_track_guest_ticket(client):
    track = GuestTrackResponse(
        ticket_id=uuid.uuid4(),
        status=TicketStatus.in_progress.value,
        status_updated_at=datetime.now(UTC),
        product="веб-сервис",
        created_at=datetime.now(UTC),
    )
    with patch(
        "backend.app.api.v1.tickets.ticket_service.track_guest_ticket",
        new_callable=AsyncMock,
        return_value=track,
    ):
        response = await client.get("/tickets/track/token-abc")
    assert response.status_code == 200
    assert response.json()["status"] == "в_работе"


@pytest.fixture
def operator_client(client):
    async def override_user():
        return CurrentUser(
            id=uuid.uuid4(),
            username="operator1",
            role=UserRole.employee,
            employee_role=EmployeeRole.operator.value,
        )

    app.dependency_overrides[get_current_user] = override_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_patch_ticket_status_inserts_history(operator_client, sample_ticket):
    from backend.app.models.ticket_status_history import TicketStatusHistory

    updated = sample_ticket
    updated.status = TicketStatus.in_progress.value
    history_row = TicketStatusHistory(
        id=uuid.uuid4(),
        ticket_id=sample_ticket.id,
        status_from=TicketStatus.accepted.value,
        status_to=TicketStatus.in_progress.value,
        changed_by=uuid.uuid4(),
        created_at=datetime.now(UTC),
    )

    with patch(
        "backend.app.api.v1.tickets.ticket_service.patch_ticket_status",
        new_callable=AsyncMock,
        return_value=updated,
    ) as patch_status, patch(
        "backend.app.api.v1.tickets.ticket_service.get_ticket",
        new_callable=AsyncMock,
        return_value=sample_ticket,
    ), patch(
        "backend.app.api.v1.tickets.ticket_service.get_status_history",
        new_callable=AsyncMock,
        return_value=[history_row],
    ):
        response = await operator_client.patch(
            f"/tickets/{sample_ticket.id}/status",
            json={"status": "в_работе"},
        )
        assert response.status_code == 200
        patch_status.assert_awaited_once()
        history = await operator_client.get(f"/tickets/{sample_ticket.id}/status-history")
    assert history.status_code == 200
    assert history.json()[0]["status_to"] == "в_работе"


@pytest.mark.asyncio
async def test_analytics_ai_efficiency(analyst_client):
    payload = AIEfficiencyResponse(
        auto_resolved=10,
        escalated=5,
        auto_resolved_pct=66.67,
        avg_messages_before_escalation=3.5,
        top_escalated_categories=[],
        top_resolved_categories=[],
    )
    with patch(
        "backend.app.api.v1.analytics.analytics_service.ai_efficiency",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        response = await analyst_client.get("/analytics/ai/efficiency")
    assert response.status_code == 200
    assert response.json()["auto_resolved"] == 10


@pytest.mark.asyncio
async def test_analytics_tickets_anomalies(analyst_client):
    payload = TicketAnomaliesResponse(items=[])
    with patch(
        "backend.app.api.v1.analytics.analytics_service.tickets_anomalies",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        response = await analyst_client.get("/analytics/tickets/anomalies")
    assert response.status_code == 200
    assert response.json()["items"] == []
