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

## Kafka (опционально)

```powershell
docker compose up -d kafka
```
