"""
Сборка аналитической витрины из операционной БД nerd_db → nerd_analytics_db.

Запуск из корня репозитория:
  python -m backend.scripts.build_analytics_warehouse

Прогноз time_series (сначала сгенерируйте xlsx в classic_models/time_series):
  python -m backend.scripts.build_analytics_warehouse ^
    --forecast-xlsx classic_models/time_series/tickets_week_forecast_from_artifact.xlsx
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.app.analytics_warehouse.etl import build_warehouse
from backend.app.config import get_settings
from backend.app.db.analytics_session import AnalyticsSessionLocal, analytics_engine
from backend.app.db.session import AsyncSessionLocal, engine

_WAREHOUSE_TABLES = (
    "general",
    "ai_effective",
    "admin_effective",
    "fact_users",
    "fact_reviews",
    "fact_problems",
    "fact_forecast",
)


async def _preflight() -> None:
    settings = get_settings()
    print(f"Operational DB: {settings.DATABASE_URL}")
    print(f"Analytics DB:   {settings.ANALYTICS_DATABASE_URL}")

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise SystemExit(
            f"Не удалось подключиться к nerd_db.\n"
            f"  Проверьте Docker: docker compose -f backend/docker-compose.yml up -d\n"
            f"  Ошибка: {exc}"
        ) from exc

    try:
        async with analytics_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except OperationalError as exc:
        raise SystemExit(
            "Не удалось подключиться к nerd_analytics_db.\n"
            "  1) Создайте БД:\n"
            "     docker exec -it <postgres> psql -U postgres -c "
            "\"CREATE DATABASE nerd_analytics_db;\"\n"
            "  2) Примените миграции:\n"
            "     cd backend && alembic -c analytics_alembic.ini upgrade head\n"
            f"  Ошибка: {exc}"
        ) from exc

    missing: list[str] = []
    async with analytics_engine.connect() as conn:
        for table in _WAREHOUSE_TABLES:
            try:
                await conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            except ProgrammingError:
                missing.append(table)

    if missing:
        raise SystemExit(
            "В nerd_analytics_db нет таблиц витрины: " + ", ".join(missing) + "\n"
            "  Выполните: cd backend && alembic -c analytics_alembic.ini upgrade head"
        )


async def main(forecast_xlsx: Path | None) -> None:
    await _preflight()

    if forecast_xlsx:
        path = forecast_xlsx.resolve()
        if not path.is_file():
            print(
                f"WARNING: файл прогноза не найден: {path}\n"
                "  Сгенерируйте его:\n"
                "  cd classic_models/time_series && python tickets_time_series_predict.py\n"
                "  fact_forecast останется пустой.",
                file=sys.stderr,
            )
            forecast_xlsx = None
        else:
            print(f"Forecast file: {path}")

    async with AsyncSessionLocal() as odb, AnalyticsSessionLocal() as adb:
        stats = await build_warehouse(odb, adb, forecast_xlsx=forecast_xlsx)

    print("Warehouse built:", stats)
    if stats.get("fact_forecast", 0) == 0:
        print(
            "  fact_forecast: 0 строк (нормально, если не передавали --forecast-xlsx "
            "или файл отсутствует)"
        )
    print("\nПроверка в DBeaver: подключение к базе nerd_analytics_db, не nerd_db.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Заполнить аналитическую витрину nerd_analytics_db")
    parser.add_argument(
        "--forecast-xlsx",
        type=Path,
        default=None,
        help="Excel из tickets_time_series_predict.py (лист forecast_long)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.forecast_xlsx))
