# Backend

## Запуск

1. Docker Desktop → Running  
2. Postgres:

```powershell
cd backend
docker compose up -d db
alembic upgrade head
```

3. API (из корня репозитория):

```powershell
uvicorn backend.app.main:app --port 8001 --reload
```

`.env` — скопировать из `backend/.env.example`.

## Схема БД (кратко)

| Таблица | API |
|---------|-----|
| clients | `/auth` |
| employees | только `/auth/login` (в БД вручную) |
| tickets | `/tickets` |
| reviews | `/reviews` |
| attachments | `/tickets/{id}/attachments` |
| chat_history | `/ai/chat`, `/ai/chat/history` |
| notifications | `/notifications` (read, + Kafka) |

**Tickets:** `product` (6 значений), `status`, `priority`, `sla_ttfr_min`, `sla_ttr_min`, AI-поля.  
**Reviews:** `ticket_id` **nullable**, категории AI: скорость решения / качество ответа / вежливость / техническая компетентность / общее впечатление.  
**Chat:** `chat_id` обязателен, роли `client` / `ai` / `admin`.

## API для фронтенда

Полное описание эндпоинтов: **[backend/FRONTEND_API.md](../backend/FRONTEND_API.md)**

Префиксы: `/auth` · `/tickets` · `/reviews` · `/notifications` · `/analytics` (employee) · `/ai`

## Загрузка данных из Excel

Проверка перед вставкой в БД: `backend/notebooks/validate_excel_data.ipynb`  
Положите файл в `backend/notebooks/data/` (листы = таблицы, столбцы = поля БД).

```powershell
pip install -r backend/notebooks/requirements.txt
```

## Тестирование

```powershell
cd backend
python -m pytest tests/ -v
```

Ручные сценарии: register → login → tickets → reviews → `/ai/chat` (нужен ML, см. [ML.md](ML.md)).

**Сотрудник / админка (`/analytics` на фронте):**

```powershell
# из корня репозитория, Postgres и alembic upgrade уже применены
python -m backend.scripts.create_employee
# роль по умолчанию analyst — иначе /analytics вернёт 403
python -m backend.scripts.create_employee --username admin --password admin123 --role analyst
```

Затем `POST /auth/login` → `/auth/me`: `"role": "employee"`.

**Данные для дашбордов** — отдельная БД `nerd_analytics_db` (не `nerd_db`):

```powershell
# БД создаётся скриптом init-db.sh при docker compose из корня, иначе:
docker exec -it <postgres> psql -U postgres -c "CREATE DATABASE nerd_analytics_db;"
cd backend
alembic -c analytics_alembic.ini upgrade head
cd ..
python -m backend.scripts.build_analytics_warehouse
```

В `backend/.env` желательно: `ANALYTICS_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5436/nerd_analytics_db`

## Kafka (опционально)

```powershell
docker compose up -d kafka
```
