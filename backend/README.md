# Backend — запуск

## Требования

- Python 3.12+
- Docker + Docker Compose

---

## Локальный запуск (без Docker)

### 1. Инфраструктура

```bash
cd backend
docker compose up -d db kafka minio
```

Сервисы:
| Сервис | Адрес |
|--------|-------|
| PostgreSQL | `localhost:5436` |
| Kafka | `localhost:9092` |
| MinIO S3 | `localhost:9000` |
| MinIO Console | `localhost:9001` (логин: `minioadmin` / `minioadmin`) |

### 2. Переменные окружения

```bash
cp .env.example .env
```

При необходимости отредактируй `.env`. Дефолтные значения работают с `docker compose` из этого каталога.

### 3. Зависимости

```bash
pip install -r requirements.txt
```

### 4. Миграции

Из корня репозитория:

```bash
cd backend
alembic upgrade head
```

### 5. Запуск сервера

Из корня репозитория:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

API доступно по адресу: http://localhost:8001  
Документация: http://localhost:8001/docs

---

## Запуск в Docker

```bash
docker compose up --build
```

Миграции применяются автоматически при старте контейнера (`entrypoint.sh`).

---

## Структура сервисов

```
backend/app/
├── api/v1/         — роутеры FastAPI
├── models/         — ORM-модели SQLAlchemy
├── schemas/        — Pydantic-схемы
├── services/       — бизнес-логика
│   ├── ai_service.py
│   ├── s3_service.py   — загрузка файлов в MinIO
│   └── file_parser.py  — парсинг PDF/DOCX/XLSX/CSV/TXT
└── config.py       — настройки через .env
```

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Основная БД |
| `ML_SERVICE_URL` | `http://localhost:8091` | ML-сервис |
| `S3_ENDPOINT_URL` | `http://localhost:9000` | MinIO endpoint |
| `S3_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `S3_SECRET_KEY` | `minioadmin` | MinIO secret key |
| `S3_BUCKET_NAME` | `nerd-files` | Bucket для файлов |
| `SECRET_KEY` | — | JWT-секрет (сменить в проде) |
| `KAFKA_URL` | `localhost:9092` | Kafka broker |

---

## Загрузка файлов (новое)

Поддерживаемые форматы: `pdf`, `docx`, `doc`, `txt`, `md`, `rst`, `xlsx`, `xls`, `csv`.  
Максимальный размер: **50 MB**.

```
POST   /ai/files           — загрузить один или несколько файлов
GET    /ai/files/{id}      — метаданные файла
DELETE /ai/files/{id}      — удалить файл
POST   /ai/chat            — чат (поле file_ids: [uuid, ...] — опционально)
```
