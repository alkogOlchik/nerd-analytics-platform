import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from backend.app.api.deps import CurrentUser, get_current_user
from backend.app.main import app
from backend.app.models.enums import UserRole
from backend.app.models.user import Employee
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
async def test_change_password_bad_current(auth_client):
    with patch(
        "backend.app.api.v1.auth.auth_service.change_password",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=400, detail="Invalid current password"),
    ):
        response = await auth_client.post(
            "/auth/change-password",
            json={"current_password": "wrong", "new_password": "newsecret123"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_password_ok(auth_client):
    with patch("backend.app.api.v1.auth.auth_service.change_password", new_callable=AsyncMock):
        response = await auth_client.post(
            "/auth/change-password",
            json={"current_password": "old", "new_password": "newsecret123"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_patch_profile(auth_client):
    payload = UserMeResponse(
        id=uuid.uuid4(),
        username="testuser",
        role=UserRole.client,
        email="test@example.com",
        full_name="Иван",
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
            json={"full_name": "Иван", "city": "Москва", "age": 25, "gender": "male"},
        )
    assert response.status_code == 200
    assert response.json()["city"] == "Москва"


@pytest.mark.asyncio
async def test_admin_register(client):
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
            json={"username": "admin", "password": "secret123", "full_name": "Админ"},
        )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_mark_notification_read(auth_client):
    nid = uuid.uuid4()
    from backend.app.models.notification import Notification

    notification = Notification(
        id=nid,
        client_id=uuid.uuid4(),
        ticket_id=uuid.uuid4(),
        type="email",
        status="sent",
        is_read=True,
        created_at=datetime.now(UTC),
    )
    with patch(
        "backend.app.api.v1.notifications.notification_service.update_notification",
        new_callable=AsyncMock,
        return_value=notification,
    ):
        response = await auth_client.patch(f"/notifications/{nid}", json={"is_read": True})
    assert response.status_code == 200
    assert response.json()["is_read"] is True


@pytest.mark.asyncio
async def test_read_all_notifications(auth_client):
    with patch(
        "backend.app.api.v1.notifications.notification_service.mark_all_read",
        new_callable=AsyncMock,
        return_value=2,
    ):
        response = await auth_client.post("/notifications/read-all")
    assert response.status_code == 200
    assert response.json()["updated"] == 2
