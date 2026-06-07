# API для фронтенда

**Base URL:** `http://127.0.0.1:8001`  
**Swagger:** http://127.0.0.1:8001/docs  
**Auth:** `Authorization: Bearer <access_token>`

Публичные пути: `/auth/register`, `/auth/login`, `/auth/admin/login`, `/auth/refresh`, `/health`

---

## Auth

| Метод | Путь |
|-------|------|
| POST | `/auth/register` |
| POST | `/auth/login` |
| POST | `/auth/admin/login` |
| POST | `/auth/refresh` |
| POST | `/auth/logout` |
| GET | `/auth/me` |

Login response: `{ access_token, refresh_token, token_type: "bearer" }`  

**Admin login** (`/auth/admin/login`) — только `employees`, тело как у login:

```json
{ "username": "admin", "password": "..." }
```

Ответ: токены + `role: "employee"`, `employee_role` (`analyst` | `operator` | …), `username`.

Me: `{ id, username, role: "client"|"employee", employee_role?, email?, full_name? }`

---

## Tickets

| Метод | Путь | Примечание |
|-------|------|------------|
| POST | `/tickets` | client |
| GET | `/tickets` | client — свои; employee — все |
| GET | `/tickets/{id}` | + attachments |
| PATCH | `/tickets/{id}` | employee |
| POST | `/tickets/{id}/reopen` | |
| POST | `/tickets/{id}/attachments` | только URL |

**Create:** `{ product, priority, deadline, sla_ttfr_min?, sla_ttr_min? }`

**List query:** `skip`, `limit`, `status`, `product`, `priority`, `category`, `date_from`, `date_to`

**Ticket fields:** `product`, `status`, `priority`, `date`, `deadline`, `closed_at`, `reopened_count`, `ai_suggested_category`, `final_category`, `keywords[]`, `confidence`, `sla_ttfr_min`, `sla_ttr_min`

---

## Reviews

| Метод | Путь |
|-------|------|
| POST | `/reviews` |
| GET | `/reviews` |
| GET | `/reviews/{id}` |
| PATCH | `/reviews/{id}` |

**Create:** `{ ticket_id?, rating (1-5), comment?, product? }` — `ticket_id` опционален

**Review AI categories:** `скорость решения` · `качество ответа` · `вежливость` · `техническая компетентность` · `общее впечатление`

---

## Notifications

| Метод | Путь |
|-------|------|
| GET | `/notifications` |
| GET | `/notifications/{id}` |

---

## Analytics (employee, nerd_db)

**Auth:** `POST /auth/admin/login` → токен сотрудника.

**Query на всех операционных ручках** (опционально):

- `date_from`, `date_to` — период (по умолчанию последние 30 дней)
- `from`, `to` — алиасы для `date_from` / `date_to`
- `product` — enum продукта
- `priority` — `low` | `medium` | `high`
- `category` — категория

### Гранулярные ручки (для текущего фронта)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/analytics/tickets/summary` | Агрегаты по статусу/продукту/категории |
| GET | `/analytics/tickets/timeline` | **Динамика по дням** `[{ date, count }]` |
| GET | `/analytics/tickets/dynamics` | Алиас `timeline` |
| GET | `/analytics/tickets/sla` | SLA сводка |
| GET | `/analytics/tickets/reopens` | Возвраты |
| GET | `/analytics/tickets/anomalies` | Аномалии 48ч |
| GET | `/analytics/tickets/forecast` | Прогноз 7 дней (MA) |
| GET | `/analytics/ai/accuracy` | Точность классификации |
| GET | `/analytics/ai/efficiency` | Эффективность ИИ |
| GET | `/analytics/admin/workload` | Нагрузка операторов |
| GET | `/analytics/admin/sla` | SLA по приоритетам |
| GET | `/analytics/admin/heatmap` | Heatmap TTFR |
| GET | `/analytics/users/demographics` | Демография |
| GET | `/analytics/users/retention` | Retention |
| GET | `/analytics/reviews/summary` | Сводка отзывов |
| GET | `/analytics/reviews/keywords` | Ключевые слова |
| GET | `/analytics/reviews/dynamics` | Динамика sentiment по дням |

### Дашборды (один запрос на экран UI)

| GET | `/analytics/dashboard/1` … `/dashboard/5` |
| GET | `/analytics/dashboard/6/tickets` |
| GET | `/analytics/dashboard/6/forecast` | только `product`, `category` |

### Витрина (после ETL, без фильтров периода)

| GET | `/analytics/warehouse/tickets/summary` и др. |

---

## AI

| Метод | Путь |
|-------|------|
| POST | `/ai/classify/ticket` |
| POST | `/ai/classify/review` |
| POST | `/ai/chat/attachments` |
| POST | `/ai/chat` |
| GET | `/ai/chat/history` |
| POST | `/tickets/{id}/attachments/upload` |
| GET | `/ai/classify/ticket/{ticket_id}` |

**Upload (multipart `file`):** JPEG/PNG/WebP/GIF/PDF → `{ file_url, file_type, file_name, size_bytes }`. Без S3 — локально, URL `/files/local/…`.

**Chat body:** `{ message?, attachments?: [{ file_url, file_type?, file_name? }], model?, chat_id?, … }` — нужен текст или вложения.

**Chat response:** `{ chat_id, user_message, assistant_message, ml_response }` — в сообщениях поле `attachments[]`.

**History query:** `chat_id` или `ticket_id`

Проверка ML: [ML.md](ML.md)

---

## Enums

**product:** `веб-сервис` · `платёжный сервис` · `мобильное приложение` · `API интеграция` · `личный кабинет` · `аналитический модуль`

**status:** `open` · `in_progress` · `closed` · `reopened`

**priority:** `low` · `medium` · `high`

**gender:** `male` · `female`

**chat role:** `client` · `ai` · `admin`

**sentiment (reviews):** `positive` · `neutral` · `negative`

---

## Ошибки

| HTTP | Причина |
|------|---------|
| 401 | Нет/битый токен |
| 403 | Нет прав (analytics, чужой тикет) |
| 404 | Не найдено |
| 502 | ML недоступен |

OpenAPI types: `npx openapi-typescript http://127.0.0.1:8001/openapi.json -o src/api/schema.ts`
