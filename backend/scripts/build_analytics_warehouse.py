"""
Сборка аналитической витрины из операционной БД.

Запуск из корня репозитория:
  python -m backend.scripts.build_analytics_warehouse

Опционально — прогноз из time_series:
  python -m backend.scripts.build_analytics_warehouse --forecast-xlsx classic_models/time_series/tickets_week_forecast_from_artifact.xlsx
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from backend.app.config import get_settings
from backend.app.db.analytics_session import AnalyticsSessionLocal
from backend.app.db.session import AsyncSessionLocal
from backend.app.analytics_warehouse.etl import build_warehouse


async def main(forecast_xlsx: Path | None) -> None:
    settings = get_settings()
    print(f"Operational DB: {settings.DATABASE_URL}")
    print(f"Analytics DB:   {settings.ANALYTICS_DATABASE_URL}")

    async with AsyncSessionLocal() as odb, AnalyticsSessionLocal() as adb:
        stats = await build_warehouse(odb, adb, forecast_xlsx=forecast_xlsx)
    print("Warehouse built:", stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forecast-xlsx",
        type=Path,
        default=None,
        help="Excel с прогнозом time_series (колонки date/category/product/predicted_count)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.forecast_xlsx))
