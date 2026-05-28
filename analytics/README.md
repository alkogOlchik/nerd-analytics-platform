# Система аналитики

Аналитическая витрина хранится в **отдельной БД** `nerd_analytics_db` (операционная `nerd_db` не меняется).

## Таблицы (дашборды D1–D6)

| Таблица | Дашборд |
|---------|---------|
| `general` | D1 — обработка тикетов |
| `ai_effective` | D2 — эффективность ИИ |
| `admin_effective` | D3 — эффективность администратора |
| `fact_users` | D4 — пользователи |
| `fact_reviews` | D5 — отзывы |
| `fact_problems` | D6 — проблемы |
| `fact_forecast` | D6 — прогноз (time_series) |

Схема: [dbdiagram.io](https://dbdiagram.io/d/nerd_analytics_dashbord-6a047c327a923b9472a2c97e)

ETL читает **фактические колонки** из `nerd_db` (миграция 006 на операционной БД не обязательна).

## Первый запуск

```powershell
# 1. Если Postgres уже поднимался без второй БД — создайте вручную:
docker exec -it <container> psql -U postgres -c "CREATE DATABASE nerd_analytics_db;"

# 2. Миграции аналитической БД (из папки backend):
cd backend
alembic -c analytics_alembic.ini upgrade head

# 3. Заполнение витрины из nerd_db (+ опционально прогноз):
cd ..
python -m backend.scripts.build_analytics_warehouse
# с прогнозом:
python -m backend.scripts.build_analytics_warehouse --forecast-xlsx classic_models/time_series/tickets_week_forecast_from_artifact.xlsx
```

Переменная окружения: `ANALYTICS_DATABASE_URL` (см. `backend/.env.example`).

## Ноутбук

`data_to_dasboards.ipynb` — эталонная логика сборки витрины (pandas). ETL в бэкенде (`backend/app/analytics_warehouse/etl.py`) повторяет ту же идею и пишет напрямую в PostgreSQL.

## API

Эндпоинты `/analytics/*` читают **только** из `nerd_analytics_db`. После изменений в операционной БД перезапустите ETL.
