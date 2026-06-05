import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.main import app
from backend.app.models.enums import UserRole
from backend.app.models.notification import Notification
from backend.app.schemas.notification import NotificationResponse
from backend.app.schemas.user import UserMeResponse


@pytest.fixture
def auth_client(client):
    async def override_user():
        return CurrentUser(
            id=uuid.uuid4(),
            username="testuser",
            role=UserRole.client,
            email="test@example.com",
            full_name="Test",
        )

    app.dependency_overrides[get_current_user] = override_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_change_password_wrong_current(auth_client, db_session):
    with patch(
        "backend.app.api.v1.auth.auth_service.change_password",
        new_callable=AsyncMock,
        side_effect=__import__("fastapi").HTTPException(status_code=400, detail="Invalid current password"),
    ):
        response = await auth_client.post(
            "/auth/change-password",
            json={"current_password": "wrong", "new_password": "newsecret123"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_password_success(auth_client):
    with patch(
        "backend.app.api.v1.auth.auth_service.change_password",
        new_callable=AsyncMock,
    ) as mock_change:
        response = await auth_client.post(
            "/auth/change-password",
            json={"current_password": "oldsecret", "new_password": "newsecret123"},
        )
    assert response.status_code == 200
    mock_change.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_profile(auth_client):
    payload = UserMeResponse(
        id=uuid.uuid4(),
        username="testuser",
        role=UserRole.client,
        email="test@example.com",
        full_name="Новое имя",
        city="Москва",
        age=25,
        gender="male",
    )
    with patch(
        "backend.app.api.v1.auth.auth_service.update_profile",
        new_callable=AsyncMock,
        return_value=payload,
    ):
        response = await auth_client.patch(
            "/auth/me",
            json={"full_name": "Новое имя", "city": "Москва", "age": 25, "gender": "male"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Новое имя"
    assert data["city"] == "Москва"


@pytest.mark.asyncio
async def test_mark_notification_read(auth_client):
    notification_id = uuid.uuid4()
    response_dto = NotificationResponse(
        id=notification_id,
        type="ticket_update",
        title="Тикет",
        message="Обновление",
        is_read=True,
        created_at=datetime.now(UTC),
        ticket_id=uuid.uuid4(),
    )
    with patch(
        "backend.app.api.v1.notifications.notification_service.update_notification",
        new_callable=AsyncMock,
        return_value=response_dto,
    ):
        response = await auth_client.patch(
            f"/notifications/{notification_id}",
            json={"is_read": True},
        )
    assert response.status_code == 200
    assert response.json()["is_read"] is True


@pytest.mark.asyncio
async def test_read_all_notifications(auth_client):
    with patch(
        "backend.app.api.v1.notifications.notification_service.mark_all_read",
        new_callable=AsyncMock,
        return_value=3,
    ):
        response = await auth_client.post("/notifications/read-all")
    assert response.status_code == 200
    assert response.json()["updated"] == 3


@pytest.mark.asyncio
async def test_admin_register_success(client):
    from backend.app.models.user import Employee

    employee = Employee(
        id=uuid.uuid4(),
        username="admin",
        full_name="Админ",
        password_hash="hash",
        status="active",
        role="super_admin",
        sec_level=1,
        created_at=datetime.now(UTC),
    )
    with patch(
        "backend.app.api.v1.auth.auth_service.register_employee",
        new_callable=AsyncMock,
        return_value=employee,
    ):
        response = await client.post(
            "/auth/admin/register",
            json={
                "username": "admin",
                "password": "secret123",
                "full_name": "Админ",
                "role": "analyst",
            },
        )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "super_admin"


def test_notification_to_response_defaults():
    from backend.app.services.notification_service import notification_to_response

    n = Notification(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        ticket_id=uuid.uuid4(),
        type="email",
        status="sent",
        event_type="ticket_update",
        is_read=False,
        created_at=datetime.now(UTC),
    )
    dto = notification_to_response(n)
    assert dto.type == "ticket_update"
    assert dto.is_read is False
    assert dto.title
