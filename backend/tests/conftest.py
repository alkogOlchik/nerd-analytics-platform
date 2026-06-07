import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.api.deps import get_db
from backend.app.main import app
from backend.app.models.enums import TicketPriority, TicketProduct, TicketStatus
from backend.app.models.user import Client


@pytest.fixture
async def db_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.add = lambda obj: None
    return session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def sample_client():
    return Client(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password_hash="hashed",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_ticket(sample_client):
    from backend.app.models.ticket import Ticket

    return Ticket(
        id=uuid.uuid4(),
        client_id=sample_client.id,
        product=TicketProduct.web.value,
        status=TicketStatus.accepted.value,
        priority=TicketPriority.medium.value,
        date=datetime.now(UTC),
        deadline=datetime.now(UTC),
        reopened_count=0,
        is_admin_changed=False,
        sla_ttfr_min=60,
        sla_ttr_min=1440,
    )
