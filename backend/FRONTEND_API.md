# API для фронтенда (Нёрд-аналитика)

Документ для интеграции UI с backend. Актуальный контракт также в Swagger после запуска API.

---

## Подключение

| Параметр | Значение |
|----------|----------|
| **Base URL (разработка)** | `http://127.0.0.1:8001` |
| **Swagger / OpenAPI** | `http://127.0.0.1:8001/docs` · `http://127.0.0.1:8001/openapi.json` |
| **Авторизация** | `Authorization: Bearer <access_token>` |
| **Content-Type** | `application/json` |

Скопируйте `backend/.env.example` → `backend/.env`. Для фронта важно: API на **8001**, ML отдельно на **8091** (фронт в ML не ходит).

### Публичные эндпоинты (без токена)

- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`

Все остальные — с Bearer `access_token`.

### Роли

| Роль | Как получить | Доступ |
|------|----------------|--------|
| `client` | `POST /auth/register` + login | Свои тикеты, отзывы, чат, уведомления |
| `employee` | только `POST /auth/login` (запись в БД `employees`) | Все тикеты, PATCH, **analytics** |

---

## Общие правила

- **ID** — UUID в строках (`"550e8400-e29b-41d4-a716-446655440000"`).
- **Пагинация:** query `skip` (default 0), `limit` (default 20, max 100) где указано.
- **Даты** — ISO 8601, например `"2026-12-31T23:59:59Z"`.
- **Пустые опциональные UUID** — не отправляйте `""`; omit поле или `null` (для `ticket_id` в отзывах/чате).

### Коды ошибок

| HTTP | Когда |
|------|--------|
| 400 | Дубликат username/email, неверная бизнес-логика |
| 401 | Невалидный / просроченный токен |
| 403 | Нет токена (`Not authenticated`) или нет прав (чужой тикет, analytics для client) |
| 404 | Сущность не найдена |
| 422 | Ошибка валидации тела (см. `detail[].loc`) |
| 502 | ML недоступен (`/ai/*`) |

Формат 422:

```json
{
  "detail": [
    { "loc": ["body", "password"], "msg": "String should have at least 6 characters", "type": "..." }
  ]
}
```

---

## 1. Health

### `GET /health`

**Auth:** нет  

**Response 200:**

```json
{ "status": "ok" }
```

---

## 2. Auth — `/auth`

### `POST /auth/register`

Регистрация **клиента**.

**Body:**

```json
{
  "username": "user01",
  "email": "user01@example.com",
  "password": "secret123",
  "full_name": "Иван",
  "age": 25,
  "gender": "male",
  "city": "Москва"
}
```

| Поле | Обязательно | Правила |
|------|-------------|---------|
| username | да | 3–64 символа |
| email | да | валидный email |
| password | да | **минимум 6** символов |
| full_name, age, city | нет | |
| gender | нет | `"male"` или `"female"` |

**Response 201:** объект клиента (`id`, `username`, `email`, `full_name`, `age`, `gender`, `city`, `created_at`).

**400:** `Username or email already exists`

---

### `POST /auth/login`

Логин **клиента** или **сотрудника** (по `username` в `clients` / `employees`).

**Body:**

```json
{
  "username": "user01",
  "password": "secret123"
}
```

**Response 200:**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Сохраните `access_token` для заголовка Authorization.

---

### `POST /auth/refresh`

**Body:**

```json
{ "refresh_token": "eyJ..." }
```

**Response 200:** новая пара `access_token`, `refresh_token`.

---

### `POST /auth/logout`

**Body:**

```json
{ "refresh_token": "eyJ..." }
```

**Response 204** — без тела.

---

### `GET /auth/me`

**Auth:** да  

**Response 200:**

```json
{
  "id": "uuid",
  "username": "user01",
  "role": "client",
  "email": "user01@example.com",
  "full_name": "Иван"
}
```

Для `employee` поле `email` может отсутствовать.

---

## 3. Tickets — `/tickets`

### `POST /tickets`

**Auth:** client (или employee — по политике; создаётся от имени текущего client_id)  

**Body:**

```json
{
  "product": "веб-сервис",
  "priority": "medium",
  "deadline": "2026-12-31T23:59:59Z",
  "sla_ttfr_min": 60,
  "sla_ttr_min": 1440
}
```

| Поле | Обязательно | Значения |
|------|-------------|----------|
| product | да | см. enum **product** ниже |
| priority | нет (default `medium`) | `low`, `medium`, `high` |
| deadline | да | ISO datetime |
| sla_ttfr_min, sla_ttr_min | нет | минуты, int ≥ 1 |

**Response 201:** тикет (см. **объект Ticket**).

---

### `GET /tickets`

**Auth:** да  

**Query:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| skip, limit | int | пагинация |
| status | string | `open`, `in_progress`, `closed`, `reopened` |
| priority | string | `low`, `medium`, `high` |
| product | string | один из product enum |
| category | string | фильтр по `final_category` / AI-категории |
| date_from, date_to | datetime | по полю `date` |

**Поведение:** `client` — только свои; `employee` — все.

**Response 200:** `Ticket[]`

---

### `GET /tickets/{ticket_id}`

**Auth:** да  

**Response 200:** **TicketDetail** = Ticket + массив `attachments`.

**403/404** — нет доступа / не найден.

---

### `PATCH /tickets/{ticket_id}`

**Auth:** **employee**

**Body** (все поля опциональны):

```json
{
  "status": "in_progress",
  "priority": "high",
  "responsible_id": "uuid-сотрудника",
  "final_category": "технический сбой",
  "is_admin_changed": true,
  "sla_ttfr_min": 30
}
```

**Response 200:** обновлённый Ticket.

---

### `POST /tickets/{ticket_id}/reopen`

**Auth:** да  

**Response 200:** тикет со статусом `reopened`, увеличенным `reopened_count`.

---

### `POST /tickets/{ticket_id}/attachments`

Загрузка файла **не реализована** — только ссылка (URL).

**Auth:** да (владелец тикета / employee)

**Body:**

```json
{
  "file_url": "https://cdn.example.com/file.pdf",
  "file_type": "pdf"
}
```

**Response 201:**

```json
{
  "id": "uuid",
  "ticket_id": "uuid",
  "file_url": "https://...",
  "file_type": "pdf",
  "created_at": "2026-05-25T12:00:00Z"
}
```

---

### Объект Ticket (ответ)

```json
{
  "id": "uuid",
  "client_id": "uuid",
  "responsible_id": "uuid | null",
  "product": "веб-сервис",
  "status": "open",
  "priority": "medium",
  "date": "2026-05-25T10:00:00Z",
  "deadline": "2026-12-31T23:59:59Z",
  "closed_at": null,
  "reopened_count": 0,
  "last_reopened_at": null,
  "ai_suggested_category": "технический сбой",
  "final_category": "технический сбой",
  "is_admin_changed": false,
  "keywords": ["оплата", "ошибка"],
  "confidence": 0.87,
  "sla_ttfr_min": 60,
  "sla_ttr_min": 1440
}
```

`keywords` в JSON — **массив строк** (в БД может храниться строкой).

---

## 4. Reviews — `/reviews`

### `POST /reviews`

**Auth:** client  

**Body:**

```json
{
  "ticket_id": null,
  "product": "личный кабинет",
  "rating": 5,
  "comment": "Всё отлично"
}
```

| Поле | Обязательно | Примечание |
|------|-------------|------------|
| rating | да | 1–5 |
| ticket_id | нет | `null` или omit — отзыв без тикета |
| product, comment | нет | |

**Response 201:** Review (см. ниже).

---

### `GET /reviews`

**Auth:** да  

**Query:** `skip`, `limit`, `ticket_id` (опционально)

**Поведение:** client — свои; employee — все.

**Response 200:** `Review[]`

---

### `GET /reviews/{review_id}`

**Auth:** да  

**Response 200:** Review

---

### `PATCH /reviews/{review_id}`

**Auth:** да (client — свой отзыв)

**Body:**

```json
{
  "rating": 4,
  "comment": "Обновлённый текст",
  "product": "веб-сервис",
  "final_category": "качество ответа",
  "is_admin_changed": true
}
```

**Response 200:** Review

---

### Объект Review

```json
{
  "id": "uuid",
  "ticket_id": "uuid | null",
  "client_id": "uuid",
  "product": "веб-сервис",
  "rating": 5,
  "comment": "текст",
  "created_at": "2026-05-25T12:00:00Z",
  "ai_suggested_category": "вежливость",
  "final_category": "вежливость",
  "is_admin_changed": false,
  "sentiment": "positive",
  "keywords_positive": ["быстро"],
  "keywords_neutral": [],
  "keywords_negative": [],
  "confidence": 0.91
}
```

---

## 5. Notifications — `/notifications`

Только **чтение**. Записи создаёт backend по событиям Kafka (при закрытии тикета и т.д.).

### `GET /notifications`

**Auth:** да  

**Query:** `skip`, `limit`

**Поведение:** client — свои; employee — все.

**Response 200:**

```json
[
  {
    "id": "uuid",
    "client_id": "uuid",
    "ticket_id": "uuid",
    "type": "email",
    "status": "pending",
    "created_at": "2026-05-25T12:00:00Z"
  }
]
```

`type`: `email` | `push`  
`status`: `pending` | `sent` | `failed`

---

### `GET /notifications/{notification_id}`

**Auth:** да  

**Response 200:** один объект как выше.

---

## 6. Analytics — `/analytics` (только employee)

Все запросы с токеном **employee** (`POST /auth/admin/login`). Для `client` → **403**.

**Источник данных:** операционная БД `nerd_db` (актуальные тикеты/отзывы).  
**Query (опционально):** `date_from`, `date_to`, алиасы `from`/`to`, `product`, `priority`, `category`.  
**Динамика:** `GET /analytics/tickets/timeline` → `{ "items": [{ "date": "2025-01-01", "count": 12 }] }`.  
**Прогноз:** `GET /analytics/tickets/forecast` — 7 дней вперёд (скользящее среднее).  
**Дашборды целиком:** `GET /analytics/dashboard/1` … `/dashboard/6/forecast`.  
**Витрина ETL:** `GET /analytics/warehouse/*` (без фильтров периода).

### `GET /analytics/tickets/summary`

**Response 200:**

```json
{
  "by_status": [{ "key": "open", "count": 10 }],
  "by_product": [{ "key": "веб-сервис", "count": 5 }],
  "by_category": [{ "key": "технический сбой", "count": 3 }]
}
```

---

### `GET /analytics/tickets/sla`

**Response 200:**

```json
{
  "total": 100,
  "breached": 12,
  "compliant": 88,
  "compliance_rate": 0.88
}
```

---

### `GET /analytics/ai/accuracy`

**Response 200:**

```json
{
  "total_classified": 200,
  "admin_changed": 15,
  "accuracy_rate": 0.925
}
```

---

### `GET /analytics/reviews/summary`

**Response 200:**

```json
{
  "average_rating": 4.2,
  "total_reviews": 1235,
  "sentiment_distribution": [
    { "key": "positive", "count": 800 }
  ]
}
```

---

### `GET /analytics/reviews/keywords`

**Response 200:**

```json
{
  "keywords_positive": [{ "key": "быстро", "count": 40 }],
  "keywords_negative": [{ "key": "долго", "count": 12 }]
}
```

---

## 7. AI — `/ai`

Прокси к ML-сервису (`ML_SERVICE_URL`, порт **8091**). При недоступном ML → **502**.

### `POST /ai/chat/attachments`

**Auth:** да · **Content-Type:** `multipart/form-data`

Поле `file` — JPEG, PNG, WebP, GIF или PDF (до `FILE_UPLOAD_MAX_BYTES`, по умолчанию 10 МБ).

Файл сохраняется в **S3/MinIO** (если заданы `S3_*` в `.env`) или локально (`LOCAL_UPLOAD_DIR`, URL вида `/files/local/…`).

**Response 201:**

```json
{
  "file_url": "http://127.0.0.1:8001/files/local/uploads/uuid/….pdf",
  "file_type": "application/pdf",
  "file_name": "scan.pdf",
  "size_bytes": 12345
}
```

Передайте `file_url` (и при желании `file_type`, `file_name`) в `attachments` при `POST /ai/chat`.

Для тикета: `POST /tickets/{ticket_id}/attachments/upload` (тот же `file`, создаёт запись в `attachments`).

---

### `POST /ai/chat`

**Auth:** client (и employee, если разрешено политикой)

**Первое сообщение** — только:

```json
{
  "message": "Не работает оплата",
  "model": "gemma4:e2b",
  "attachments": [
    {
      "file_url": "http://127.0.0.1:8001/files/local/uploads/uuid/….png",
      "file_type": "image/png",
      "file_name": "screenshot.png"
    }
  ]
}
```

Нужно хотя бы одно из: непустой `message` или непустой `attachments`.

**Продолжение диалога** — добавить `chat_id` из прошлого ответа:

```json
{
  "message": "Спасибо, что делать дальше?",
  "model": "gemma4:e2b",
  "chat_id": "uuid-диалога"
}
```

**Опционально:**

| Поле | Описание |
|------|----------|
| ticket_id | привязка к тикету (должен принадлежать клиенту) |
| product, category | контекст в `chat_history` |
| resolved_by_ai | bool, default false |

**Response 200:**

```json
{
  "chat_id": "uuid",
  "user_message": { "...ChatMessage" },
  "assistant_message": { "...ChatMessage" },
  "ml_response": { "answer": "...", "model": "gemma4:e2b" }
}
```

Сохраняйте `chat_id` для следующих сообщений.

---

### `GET /ai/chat/history`

**Auth:** да  

**Query (один из):**

- `chat_id` — история диалога  
- `ticket_id` — все сообщения по тикету  

Дополнительно: `skip`, `limit` (max 100).

**Response 200:** `ChatMessage[]`

```json
{
  "id": "uuid",
  "chat_id": "uuid",
  "ticket_id": null,
  "role": "client",
  "product": "веб-сервис",
  "category": null,
  "resolved_by_ai": false,
  "message": "текст",
  "created_at": "2026-05-25T12:00:00Z"
}
```

`role`: `client` | `ai` | `admin`

---

### `POST /ai/classify/ticket`

Классификация текста тикета через ML, результат пишется в поля тикета.

**Body:**

```json
{
  "ticket_id": "uuid",
  "text": "Не проходит оплата картой",
  "model": "gemma4:e2b"
}
```

**Response 200:** полный **Ticket** с заполненными `ai_suggested_category`, `keywords`, `confidence` и т.д.

---

### `GET /ai/classify/ticket/{ticket_id}`

Текущие AI-поля тикета без вызова ML.

**Response 200:**

```json
{
  "id": "uuid",
  "ai_suggested_category": "технический сбой",
  "final_category": "технический сбой",
  "is_admin_changed": false,
  "keywords": ["оплата"],
  "confidence": 0.85
}
```

---

### `POST /ai/classify/review`

**Body:**

```json
{
  "review_id": "uuid",
  "text": "Оператор очень помог",
  "model": "gemma4:e2b"
}
```

**Response 200:** AI-поля отзыва (`ai_suggested_category`, `sentiment`, keywords_*, `confidence`).

---

## 8. Справочники (enum)

### product (тикеты, отзывы, чат)

- `веб-сервис`
- `платёжный сервис`
- `мобильное приложение`
- `API интеграция`
- `личный кабинет`
- `аналитический модуль`

### ticket status

- `open`
- `in_progress`
- `closed`
- `reopened`

### priority

- `low`
- `medium`
- `high`

### gender (register)

- `male`
- `female`

### review sentiment

- `positive`
- `neutral`
- `negative`

### категории AI — тикет

- `технический сбой`
- `вопрос по оплате`
- `запрос документов`
- `жалоба на сервис`
- `консультация`
- `ошибка в данных`
- `запрос возврата`
- `проблема с доступом`

### категории AI — отзыв

- `скорость решения`
- `качество ответа`
- `вежливость`
- `техническая компетентность`
- `общее впечатление`

### notification

- type: `email`, `push`
- status: `pending`, `sent`, `failed`

---

## 9. Типичные сценарии UI

### Клиент

1. `POST /auth/register` → `POST /auth/login`
2. `GET /auth/me`
3. `POST /tickets` → список `GET /tickets`
4. `POST /reviews` (с `ticket_id` или без)
5. `POST /ai/chat` → хранить `chat_id` → `GET /ai/chat/history`
6. `GET /notifications`

### Сотрудник

1. `POST /auth/login` (учётка из `employees`)
2. `GET /tickets` (все) → `PATCH /tickets/{id}` (статус, ответственный)
3. `GET /analytics/*`
4. При необходимости `POST /ai/classify/ticket`

---

## 10. TypeScript (опционально)

```bash
npx openapi-typescript http://127.0.0.1:8001/openapi.json -o src/api/schema.ts
```

---

## 11. CORS

Backend отдаёт `Access-Control-Allow-Origin: *` (разработка). В проде сузить до домена фронта.

---

## Связанные файлы

- Запуск backend: [../docs/BACKEND.md](../docs/BACKEND.md)
- ML / чат: [../docs/ML.md](../docs/ML.md)
- Краткая копия в корне: [../docs/FRONTEND_API.md](../docs/FRONTEND_API.md)
