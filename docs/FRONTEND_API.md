# API для фронтенда

**Base URL:** `http://127.0.0.1:8001`  
**Swagger:** http://127.0.0.1:8001/docs  
**Auth:** `Authorization: Bearer <access_token>`

Публичные пути: `/auth/register`, `/auth/login`, `/auth/refresh`, `/health`

---

## Auth

| Метод | Путь |
|-------|------|
| POST | `/auth/register` |
| POST | `/auth/login` |
| POST | `/auth/refresh` |
| POST | `/auth/logout` |
| GET | `/auth/me` |

Login response: `{ access_token, refresh_token, token_type: "bearer" }`  
Me: `{ id, username, role: "client"|"employee", email?, full_name? }`

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

## Analytics (employee only)

| Метод | Путь |
|-------|------|
| GET | `/analytics/tickets/summary` |
| GET | `/analytics/tickets/sla` |
| GET | `/analytics/ai/accuracy` |
| GET | `/analytics/reviews/summary` |
| GET | `/analytics/reviews/keywords` |

---

## AI

| Метод | Путь |
|-------|------|
| POST | `/ai/classify/ticket` |
| POST | `/ai/classify/review` |
| POST | `/ai/chat` |
| GET | `/ai/chat/history` |
| GET | `/ai/classify/ticket/{ticket_id}` |

**Chat body:** `{ message, model?, chat_id?, ticket_id?, product?, category?, resolved_by_ai? }`  
**Chat response:** `{ chat_id, user_message, assistant_message, ml_response }`  
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
