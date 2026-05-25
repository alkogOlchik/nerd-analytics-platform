# nerd-analytics-platform

Платформа аналитики поддержки «Нёрд-аналитика».

| Часть | Папка |
|-------|--------|
| Backend | `backend/` |
| ML (отдельная команда) | `ml/` |
| Документация | `docs/` |

## Документация

- [Запуск и тест backend](docs/BACKEND.md)
- [API для фронтенда](docs/FRONTEND_API.md)
- [Проверка связи с ML](docs/ML.md)

## Backend за 30 секунд

```powershell
cd backend
docker compose up -d db
alembic upgrade head
cd ..
uvicorn backend.app.main:app --port 8001 --reload
```

http://127.0.0.1:8001/docs
