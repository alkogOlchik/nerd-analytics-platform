# Нёрд-аналитика — инструкции для Claude

## Стек

**Backend** (`backend/`)
- Python 3.13, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2
- PostgreSQL 16 (два и��станса: `nerd_db` — операционная, `nerd_analytics_db` — витрина)
- Kafka (события тикетов), MinIO (S3-хранилище файлов)
- ��очка входа: `backend/app/` �� ��о����ы в `api/v1/`, сервисы в `services/`, ��одели в `models/`

**ML-сервис** (`ml/`)
- Python 3.13, LangGraph (ReAct-агент), LangChain, ChromaDB (RAG), Ollama (инференс)
- Зап��скается **в��е Docker** на порту `8091` (рядом с Ollama для доступа к GPU)
- Промт агента: `ml/agent/graph.py` → `SYSTEM_PROMPT`
- Конфиг: `ml/agent/config.py` (env-переменные: `LLM_BASE_URL`, `LLM_MODEL`, `OLLAMA_BASE_URL`, `CHROMA_PERSIST_DIRECTORY`)
- Запуск: `cd ml && LLM_BASE_URL=http://localhost:11434/v1 LLM_API_KEY=ollama LLM_MODEL=gemma4:e4b OLLAMA_BASE_URL=http://localhost:11434 CHROMA_PERSIST_DIRECTORY=./chroma_db python3 -m agent.service --host 0.0.0.0 --port 8091`

**Frontend** (`frontend/nerd/`)
- React 19, TypeScript, React Router v7, TanStack Query v5, Recharts, Axios
- Структура: `screens/` — эк��аны, `domain/` — хуки бизнес-логики, `data/repositories/` — типы+ма��пинг, `data/sources/` — HTTP-вызовы, `modules/` — общие компоненты
- API-прокси через nginx → gateway (`:8000`) → backend (`:8001`)

**Инфраструктура** (`docker-compose.yml`)
- В Docker: `backend`, `gateway`, `frontend`, `db`, `kafka`, `minio`
- В��е Docker: `ml-agent` (��орт 8091), `ollama` (порт 11434)
- Backend достучится до хоста через `host.docker.internal`

## Архитектурные решения

- **Все AI-запросы идут только через ML-сервис** (`ml_client.py` → `http://host.docker.internal:8091`). Прям��го вызова Ollama из бэкенда нет.
- **Продукт передаётся в ML-зап��ос** как префикс `"Продукт: ...\nКатегория: ..."` в `ai_service.py`
- **Стату��ы тикетов**: `open`, `in_progress`, `closed`, `reopened` (4 штуки, ТЗ требует 7 — незакрытый долг)
- **Аналитические фильтры** сохраняются в `localStorage` через `useAnalyticsFilters(dashboardId)`
- **Экспорт**: утилиты `exportCsv`, `exportPng`, `exportPdf` в `shared/utils/exportAnalytics`

## Правила работы

### Запросы к базе данных
- Использовать `AsyncSession`, не `Session`
- Миграции через Alembic: `cd backend && alembic -c alembic.ini revision --autogenerate -m "описание"`
- Для аналитической БД: `alembic -c analytics_alembic.ini ...`

### API
- Все роуты в `backend/app/api/v1/`, регистрируются в `backend/app/core/app.py` или аналоге
- Схемы запросов/ответов в `backend/app/schemas/`
- Авторизация: JWT Bearer, `get_current_user` / `get_current_employee` из `core/deps.py`

### Frontend
- Новые данные: ��обавить тип в `data/repositories/X/types.ts` → source-функцию в `data/sources/X/index.ts` → хук в `domain/X/`
- Продукты захардкожены в нескольких экранах (`CreateTicketScreen`, `AssistantScreen`, `FeedbackScreen`, `TicketsScreen`) — при изменении менять везде

### ML
- Промт агента только в `ml/agent/graph.py::SYSTEM_PROMPT`
- Новые инструменты: добавить в `ml/agent/tools/`, зарегистрировать в `ml/agent/tools/__init__.py`

## Коммиты

После каждого выполненного запроса **обязательно** создай git-коммит:

1. Определи тип изменения:
   - `feat:` — новая функциональность
   - `fix:` — исправление бага
   - `refactor:` — рефакторинг без изменения поведения
   - `chore:` — конфиг, зависимости, инфраструктура
   - `style:` — только визуальные/CSS изменения

2. Укажи область (`scope`) если изменение локальное:
   - `feat(ml):`, `fix(backend):`, `fix(frontend):`, `chore(docker):`

3. Сообщение — од��а строка, по-русски, суть изменения:
   - ✅ `fix(backend): убрать Ollama-fallback, все запросы через ML-сервис`
   - ✅ `feat(ml): обновить системный промт агента по требованиям ТЗ`
   - ❌ `update files` — слишком размы��о
   - ❌ `fix bug` — непонятно что

4. Стаг�� только файлы, которые реально изменились в рамках задачи. Не добавлять `.DS_Store`, `__pycache__`, `*.pyc`.

Пример команды:
```
git add backend/app/services/ml_client.py
git commit -m "fix(backend): убрать Ollama-fallback, все запросы через ML-сервис"
```
