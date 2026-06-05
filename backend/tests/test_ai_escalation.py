import uuid
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.main import app
from backend.app.models.enums import UserRole
from backend.app.schemas.ai import EscalationOffer
from backend.app.schemas.ticket_extended import TicketEscalateResponse


@pytest.fixture
def client_user():
    return CurrentUser(
        id=uuid.uuid4(),
        username="client1",
        role=UserRole.client,
        email="c@test.com",
    )


@pytest.fixture
def auth_client(client, client_user):
    async def override_user():
        return client_user

    app.dependency_overrides[get_current_user] = override_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_escalation_options(auth_client):
    response = await auth_client.get("/ai/escalation/options")
    assert response.status_code == 200
    data = response.json()
    assert "веб-сервис" in data["products"]
    assert "low" in data["priorities"]


@pytest.mark.asyncio
async def test_chat_detects_human_request(auth_client):
    from datetime import UTC, datetime

    from backend.app.models.chat import ChatHistory

    offer = EscalationOffer(
        required=True,
        suggested_product="платёжный сервис",
        suggested_category="вопрос по оплате",
        confidence=0.9,
        products=["веб-сервис"],
        categories=["вопрос по оплате"],
        priorities=["low", "medium", "high"],
        priority_labels={"low": "Низкий", "medium": "Средний", "high": "Высокий"},
    )
    chat_id = uuid.uuid4()
    now = datetime.now(UTC)
    user_msg = ChatHistory(
        id=uuid.uuid4(),
        chat_id=chat_id,
        client_id=uuid.uuid4(),
        role="client",
        message="позовите оператора",
        resolved_by_ai=False,
        created_at=now,
    )
    ai_msg = ChatHistory(
        id=uuid.uuid4(),
        chat_id=chat_id,
        client_id=user_msg.client_id,
        role="ai",
        message="Нужен специалист",
        resolved_by_ai=False,
        created_at=now,
    )
    ml_response = {"answer": "Нужен специалист", "escalation": offer.model_dump()}

    with patch(
        "backend.app.api.v1.ai.ai_service.chat",
        new_callable=AsyncMock,
        return_value=(chat_id, user_msg, ai_msg, ml_response, offer),
    ):
        response = await auth_client.post(
            "/ai/chat",
            json={"message": "позовите оператора, не помогает", "request_human": True},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["escalation"]["required"] is True
    assert body["escalation"]["suggested_product"] == "платёжный сервис"


@pytest.mark.asyncio
async def test_chat_escalate_confirm(auth_client, client_user):
    ticket_id = uuid.uuid4()
    result = TicketEscalateResponse(
        ticket_id=ticket_id,
        ai_suggested_category="технический сбой",
        final_category="технический сбой",
        status="принято",
    )
    with patch(
        "backend.app.services.escalation_service.confirm_chat_escalation",
        new_callable=AsyncMock,
        return_value=result,
    ):
        response = await auth_client.post(
            "/ai/chat/escalate",
            json={
                "chat_id": str(uuid.uuid4()),
                "product": "веб-сервис",
                "user_priority": "high",
                "category": "технический сбой",
            },
        )
    assert response.status_code == 201
    assert response.json()["ticket_id"] == str(ticket_id)
