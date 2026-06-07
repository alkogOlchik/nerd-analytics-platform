from backend.app.db.session import engine
from backend.app.models.base import Base
from backend.app.models import chat, notification, review, ticket, user  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
