from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.config import get_settings

settings = get_settings()

analytics_engine = create_async_engine(settings.ANALYTICS_DATABASE_URL, echo=False)
AnalyticsSessionLocal = async_sessionmaker(
    analytics_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_analytics_db() -> AsyncGenerator[AsyncSession, None]:
    async with AnalyticsSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
