# Нёрд-аналитика

Платформа-агрегатор обращений пользователей с аналитической надстройкой для бизнеса.

**Для пользователя** — единое окно для любых вопросов и проблем по продуктам компании: ИИ-помощник → эскалация в тикет → отслеживание статуса.

**Для бизнеса** — централизованный сбор фидбеков, дашборды эффективности (тикеты, ИИ, администраторы, пользователи, отзывы, проблемы), прогнозирование.

## Архитектура

```
frontend (React/Vite, :80)
    └─ gateway (FastAPI, :8000) — единая точка входа
           └─ backend (FastAPI, :8001) — бизнес-логика
                  ├─ PostgreSQL :5436
                  │    ├─ nerd_db (операционная)
                  │    └─ nerd_analytics_db (аналитическая витрина)
                  ├─ Kafka :9092
                  └─ MinIO S3 :9000/:9001

ml/ (вне Docker, рядом с Ollama/GPU)
    ├─ agent :8090       — RAG + браузер (gemma4)
    └─ web_guide_recorder :8091 — запись гайдов
```

## Быстрый старт (Docker)

Полный стек в одну команду:

```bash
docker compose up --build
```

| Сервис | URL |
|--------|-----|
| Фронтенд | http://localhost |
| API Gateway | http://localhost:8000 |
| Backend API / Swagger | http://localhost:8001/docs |
| MinIO Console | http://localhost:9001 (minioadmin / minioadmin) |

## Локальный запуск (разработка)

### 1. Зависимости

```bash
./install.sh
```

Требования: Python 3.10+, Node.js 18+, npm, Docker.

### 2. Инфраструктура

```bash
docker compose up -d db kafka minio
```

### 3. Переменные окружения

```bash
cp backend/.env.example backend/.env
```

### 4. Миграции

```bash
cd backend
alembic upgrade head
alembic -c analytics_alembic.ini upgrade head
```

### 5. Backend

```bash
# из корня репозитория
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Frontend

```bash
npm --prefix frontend/nerd run dev
```

Открыть: http://localhost:5173

### 7. ML-сервис (опционально, нужна Ollama)

```bash
ollama serve
ollama pull gemma4:e2b
ollama pull nomic-embed-text

cd ml
uvicorn agent.api.server:app --host 127.0.0.1 --port 8090
uvicorn web_guide_recorder.api.server:app --host 127.0.0.1 --port 8091
```

Без GPU модели работают медленно. `gemma4:e2b` — быстрее, `gemma4:e4b` — умнее.

## Аналитическая витрина

После первого запуска заполнить витрину:

```bash
python -m backend.scripts.build_analytics_warehouse
# с прогнозом:
python -m backend.scripts.build_analytics_warehouse \
  --forecast-xlsx classic_models/time_series/tickets_week_forecast_from_artifact.xlsx
```

Дашборды D1–D6: тикеты, эффективность ИИ, администраторов, пользователи, отзывы, проблемы.

## Переменные окружения (ключевые)

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Основная БД (nerd_db) |
| `ANALYTICS_DATABASE_URL` | Аналитическая БД (nerd_analytics_db) |
| `SECRET_KEY` | JWT-секрет — **сменить в проде** |
| `ML_SERVICE_URL` | URL ML-агента (по умолчанию :8091) |
| `KAFKA_URL` | Kafka broker |
| `S3_ENDPOINT_URL` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` | MinIO |
| `GOOGLE_CLIENT_ID` / `GITHUB_CLIENT_ID` | OAuth (опционально) |

## Команда

| Участник | Роль |
|----------|------|
| Ерёмин Иван | Data Analyst, PM, Data Science |
| Крепостная Ольга | DevOps, Backend |
| Чернавцева Алина | Frontend |
| Чашин Михаил | ML |
