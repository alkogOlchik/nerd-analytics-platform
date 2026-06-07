# SPEC — Нёрд-аналитика: клиент + администратор + дашборды

**Дата:** 2026-06-07  
**Статус:** Актуален. Дашборды сверены с `Система аналитики.docx`.

---

## Контекст и текущее состояние

Большинство моделей данных и базовых API уже реализованы. Спек фокусируется на пробелах и требованиях, которые нужно добавить/доработать.

Существующее:
- Модели: `Ticket`, `Review`, `ChatHistory`, `Attachment`, `TicketStatusHistory`, `InternalComment`, `Notification`
- API: `/tickets`, `/reviews`, `/analytics`, `/ai`, `/notifications`, `/auth`
- Frontend screens: `CreateTicket`, `TicketStatus`, `Tickets`, `Feedback`, `Assistant`, `Analytics`

Ключевой архитектурный пробел: **`TicketProduct` — hardcoded enum**, а не таблица БД. КЛ-06 требует динамического справочника продуктов.

---

## Часть 1. Клиентская сторона

### 1.1 Выбор продукта (КЛ-06, КЛ-08)

#### КЛ-06 — Выбор продукта при создании обращения

**Требование:** Первый шаг создания тикета — выбор продукта из динамического списка.

**Проблема:** Сейчас `product` — строковое поле, значения захардкожены в `TicketProduct` enum. Нужна таблица `products`.

**Изменения БД — новая таблица `products`:**
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    description TEXT,
    logo_url VARCHAR(1024),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Изменения в `Ticket`:** поле `product VARCHAR(64)` → `product_id UUID FK → products.id`

**API:**
- `GET /api/v1/products` — список активных продуктов (публичный, без авторизации)
- `POST /api/v1/products` — создать продукт (только `product_owner` / `super_admin`)
- `PATCH /api/v1/products/{id}` — редактировать / деактивировать

**UI (CreateTicketScreen):**
- Шаг 1: выпадающий список или карточки продуктов из `GET /products`
- Выбор продукта обязателен перед переходом к описанию проблемы

---

#### КЛ-08 — История обращений в ЛК, сгруппированная по продуктам

**Требование:** На странице `TicketsScreen` тикеты сгруппированы по продуктам.

**API:** `GET /api/v1/tickets?grouped_by=product` → структура:
```json
[
  {
    "product": { "id": "...", "name": "Мобильное приложение" },
    "tickets": [ { "id": "...", "status": "...", "admin_priority": "...", "updated_at": "..." } ]
  }
]
```

**Текущее состояние:** `GET /tickets` возвращает плоский список. Нужно добавить опцию группировки.

---

### 1.2 Эскалация к специалисту — создание тикета (Раздел 1.4: КЛ-30–КЛ-36)

Эндпоинт `POST /tickets/escalate` уже существует. Нужно проверить и дополнить следующее:

| ID | Требование | Статус | Что добавить |
|----|-----------|--------|--------------|
| КЛ-30 | Кнопка «Передать специалисту» в любой момент диалога с ИИ | Частично (экран AssistantScreen) | Убедиться, что кнопка видима всегда, не только в конце диалога |
| КЛ-31 | Авто-перенос истории диалога, продукта и файлов в тикет | Есть в `TicketEscalateRequest` | Проверить, что `chat_history_ids` и `attachments` пробрасываются |
| КЛ-32 | Авто-классификация тикета (AI теги) | Есть: `ai_suggested_category`, `confidence` | Расширить до нескольких тегов (сейчас одна категория) |
| КЛ-33 | Пользователь подтверждает или меняет предложенные категории | **Отсутствует** | Экран предпросмотра тикета с редактируемыми тегами |
| КЛ-34 | Возможность дополнить описание перед созданием тикета | **Отсутствует** | Поле `description_extra` на экране предпросмотра |
| КЛ-35 | Пользователь предлагает приоритет (рекомендательный) | Есть: `user_priority` в модели | Проверить наличие UI-выбора при эскалации |
| КЛ-36 | Подтверждение с ID тикета и итоговыми категориями | **Отсутствует** | Экран/тост после создания: «Тикет #1234 создан. Категории: [X, Y]» |

**Изменения в схеме `TicketEscalateRequest`:** добавить поля:
```python
description_extra: str | None = None
user_priority: str | None = None   # low / medium / high
confirmed_tags: list[str] | None = None  # категории, подтверждённые пользователем
```

**Экран предпросмотра тикета (новый шаг в CreateTicket/AssistantScreen):**
1. Показать предложенные ИИ-категории (чипы)
2. Дать выбрать из списка допустимых для продукта (`GET /products/{id}/tags`)
3. Поле «Дополнить описание» (textarea)
4. Radio: приоритет (Срочно / Обычный / Низкий)
5. Кнопка «Отправить»

---

### 1.3 Список обращений в ЛК (КЛ-37)

**Требование:** Список всех тикетов пользователя с: статусом, приоритетом от администратора, датой обновления, группировкой по продуктам.

**Поля карточки тикета:**
| Поле | Источник |
|------|----------|
| ID тикета | `ticket.id` |
| Продукт | `ticket.product_id → products.name` |
| Краткое описание | первые 120 символов из истории чата |
| Статус | `ticket.status` |
| Приоритет (от администратора) | `ticket.admin_priority` |
| Дата обновления | `ticket.status_updated_at` |

**Текущее состояние:** `TicketsScreen` уже есть, но проверить, что `admin_priority` отображается и есть группировка.

---

### 1.4 Оценка качества решения (Раздел 1.6: КЛ-43–КЛ-45)

Модель `Review` существует. Нужно проверить и закрыть пробелы:

| ID | Требование | Статус | Что добавить |
|----|-----------|--------|--------------|
| КЛ-43 | Предложить оценку после закрытия тикета | **Частично** | Триггер при смене статуса → «Закрыто»: показать баннер в ЛК + добавить в email |
| КЛ-44 | Текстовый комментарий к оценке | Есть в `Review` | Проверить наличие `comment` поля в UI |
| КЛ-45 | Повторное открытие закрытого тикета | **Отсутствует** | Кнопка «Проблема не решена» → `POST /tickets/{id}/reopen`; статус → «принято»; уведомление администратору |

**Новый эндпоинт:**
```
POST /api/v1/tickets/{id}/reopen
```
- Доступен только владельцу тикета
- Меняет статус на `принято`
- Увеличивает `reopened_count`
- Создаёт уведомление для ответственного

---

### 1.5 Обратная связь и предложения (Раздел 1.7: КЛ-46, КЛ-48)

| ID | Требование | Статус | Что добавить |
|----|-----------|--------|--------------|
| КЛ-46 | Отдельный путь для Feature Request / отзыва | Есть `FeedbackScreen` | Уточнить: тип записи «идея» vs «жалоба» vs «отзыв» — нужен `type` field |
| КЛ-48 | Авто-классификация тональности, удовлетворённости и категории | Есть `Sentiment` enum | Убедиться что ML pipeline вызывается при создании review; добавить `satisfaction_score` если нет |

**Форма отправки предложения:**
- Продукт (обязательно)
- Тип: `idea` / `review` / `complaint`
- Описание (textarea, обязательно)
- Оценка удовлетворённости 1–5 (опционально, для отзывов)
- Прикрепить файл (опционально)

**При сохранении:** ML-pipeline → `sentiment`, `satisfaction_score`, `ai_suggested_category`

---

## Часть 2. Административная сторона

### 2.1 Управление обращениями / инцидентами (АД-01–АД-09)

#### АД-01 — Единая очередь тикетов

**Текущее состояние:** `GET /tickets` для admin возвращает все тикеты. Нужно:
- Переключатель «Все продукты» / конкретный продукт (tab или filter)
- Дефолтная сортировка: `admin_priority DESC, date DESC`

#### АД-02 — Детальный просмотр тикета

Страница тикета должна показывать:

| Блок | Источник | Статус |
|------|----------|--------|
| Продукт | `ticket.product_id` | Нужно добавить `product` join в ответ |
| История переписки | `ticket.chat_messages` + `ticket.internal_comments` | Есть |
| Прикреплённые файлы | `ticket.attachments` | Есть |
| Статус + история | `ticket.status` + `TicketStatusHistory` | Есть |
| Ответственный | `ticket.responsible_id → employees` | Есть |
| Оба приоритета | `user_priority`, `admin_priority` | Есть в модели, проверить UI |
| Метки времени каждого действия | `status_history.changed_at` | Есть |

#### АД-03 — Изменение статуса

Эндпоинт `PATCH /tickets/{id}/status` уже есть. Проверить допустимые переходы (конечный автомат):

```
принято → в_работе → требуется_информация → в_работе → передано_разработчикам → исправлено → закрыто
принято → отклонено
закрыто → принято (при reopen от клиента)
```

#### АД-04, АД-05 — Управление приоритетом

`PATCH /tickets/{id}/priority` уже есть. Проверить:
- Сохраняется ли история изменений приоритета (нужна запись в `TicketStatusHistory` или отдельная таблица `priority_history`)
- UI показывает оба приоритета: пользовательский (`user_priority`) и итоговый (`admin_priority`)

#### АД-06 — Назначение ответственного

`PATCH /tickets/{id}/assignee` нужно проверить или добавить:
```
PATCH /api/v1/tickets/{id}/assignee
Body: { "responsible_id": "uuid" }
```

#### АД-08 — Ответ пользователю через интерфейс

`POST /tickets/{id}/comments` с `is_admin_reply: true` должен:
- Сохранять комментарий
- Триггерить email-уведомление пользователю
- Отображать ответ в ЛК пользователя

Проверить, что email отправляется. Если нет — добавить в сервис уведомлений.

#### АД-09 — Авто-эскалация по SLA

**Текущее состояние:** `sla_ttfr_min`, `sla_ttr_min` уже есть в модели `Ticket`.

**Что добавить:**
- Таблица `sla_rules` (если ещё нет):
```sql
CREATE TABLE sla_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id),
    priority VARCHAR(16) NOT NULL,
    ttfr_limit_minutes INTEGER NOT NULL,
    ttr_limit_minutes INTEGER NOT NULL
);
```
- Фоновый job (Celery / APScheduler): каждые 5 минут проверяет тикеты в открытых статусах → если нарушен TTFR или TTR → меняет статус / создаёт уведомление для `super_admin` / `product_owner`

---

### 2.2 Фильтрация и поиск обращений (АД-10–АД-12)

#### АД-10 — Составные фильтры

`GET /tickets` уже поддерживает: `status`, `priority`, `product`, `category`, `date_from`, `date_to`.

**Нужно добавить фильтры:**
| Параметр | Тип |
|----------|-----|
| `responsible_id` | UUID |
| `user_priority` | enum |
| `admin_priority` | enum |

**API:** `GET /api/v1/tickets?product_id=&tag=&status=&responsible_id=&user_priority=&admin_priority=&date_from=&date_to=`

#### АД-11 — Полнотекстовый поиск

**Текущее состояние:** скорее всего отсутствует.

**Добавить:** параметр `q` в `GET /tickets`:
- Поиск по: тексту chat_messages, internal_comments, ID тикета (строка), email/имени клиента
- Реализация: PostgreSQL `tsvector` + `GIN` индекс на `chat_messages.content`

```sql
ALTER TABLE chat_histories ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('russian', content)) STORED;
CREATE INDEX idx_chat_search ON chat_histories USING GIN(search_vector);
```

#### АД-12 — Сохранение фильтров между сессиями

**Что добавить:**
- Поле `ticket_filter_prefs JSONB` в таблице `employees` (или отдельная `user_preferences`)
- `GET /admin/me/preferences` / `PATCH /admin/me/preferences`
- При загрузке страницы тикетов — восстанавливать сохранённые фильтры

---

## Часть 3. Дашборды аналитики

### Источники требований

| Источник | Что содержит |
|----------|-------------|
| `Система аналитики.docx` | Макеты дашбордов в Yandex DataLens (6 ссылок), описание аналитической БД |
| `tz.md`, Часть 3 | Функциональные требования АН-00–АН-59 |
| dbdiagram.io (ссылка в вордике) | Схема аналитической БД: 7 таблиц (1 на дашборд 1–5, 2 для дашборда 6 — текущие + прогноз) |

**Ключевое из вордика:**
- Дашборд 6 (Тикеты): фильтры для **прогноза** (`category`, `product`) — отдельные от фильтров для анализа текущих тикетов
- Дашборд 5 (Отзывы): анализирует оба типа отзывов — «Feature Request» и «оценка после закрытия тикета»; разделение через фильтр `category`

---

### AI-ассистент на дашборде (сайд-панель)

#### UX

- Плавающая панель **справа** на экране аналитики, всегда видима, не перекрывает графики
- Текстовый чат с историей сессии
- Реализует требования КЛ-16–КЛ-29 из ТЗ

#### Архитектура: tool calling

Агент работает через Claude API. **Все tools передаются в каждый запрос** — LLM сам решает, нужен ли tool для конкретного ответа.

| Tool | Сигнатура | Кто выполняет | Пример |
|------|-----------|---------------|--------|
| `apply_filter` | `(field, value)` | Frontend (UI-команда) | «Покажи только Москву» |
| `set_date_range` | `(date_from, date_to)` | Frontend (UI-команда) | «Выборка за последний месяц» |
| `highlight_element` | `(chart_id, point_id)` | Frontend (UI-команда) | Визуальный акцент на аномалии |
| `change_chart_type` | `(chart_id, type)` | Frontend (UI-команда) | «Переведи в столбчатую» |
| `query_metric` | `(metric, filters)` | **Backend** → данные из аналитической БД | «Сколько обращений за неделю?» |
| `detect_anomalies` | `(days)` | **Backend** → `rolling_avg + 2σ` | «Найди аномалии за 7 дней» |
| `create_ticket` | `(product_id, description, priority)` | **Backend** → `ticket_service` | «Создай тикет для разработки» |

**Правило:** tools с side-effects (данные, запись в БД) выполняет бэк. UI-изменения (фильтры, выделения) — фронт по командам из ответа.

#### Поток запроса

```
Frontend                    Backend (analytics-chat)            Claude API
   │                               │                                │
   │── POST /ai/analytics-chat ──▶ │                                │
   │   {message, session_id,       │── messages + tools list ─────▶ │
   │    dashboard_context}         │                                │
   │                               │◀─ tool_use: query_metric ──── │
   │                               │   (бэк выполняет запрос к БД) │
   │                               │── tool_result ───────────────▶ │
   │                               │◀─ tool_use: create_ticket ─── │
   │                               │   (бэк вызывает ticket_service)│
   │                               │── tool_result {ticket_id} ───▶ │
   │                               │◀─ text reply ─────────────── │
   │◀── response ────────────────  │
   │   {reply, ui_commands,        │
   │    created_ticket_id}         │
```

#### Формат ответа эндпоинта

```python
# POST /api/v1/ai/analytics-chat
# Request
{
  "session_id": "uuid",
  "message": "строка",
  "dashboard_context": {
    "active_dashboard": 1,          # номер открытого дашборда
    "current_filters": {},          # активные фильтры
    "date_range": {"from": "...", "to": "..."}
  }
}

# Response
{
  "reply": "Текст ответа агента для отображения в чате",
  "ui_commands": [                  # команды для фронта, могут быть пустым списком
    {"type": "apply_filter", "field": "city", "value": "Москва"},
    {"type": "highlight_element", "chart_id": "chart_3", "point_id": "2024-06-01"}
  ],
  "created_ticket_id": "uuid | null"  # если агент создал тикет
}
```

#### Сценарий `create_ticket` (пример диалога)

`create_ticket` доступен всегда — не только при аномалиях.

```
Агент: «Количество "Ошибка 500" выросло в 5 раз за последний час.
        Возможно, связано с вчерашним деплоем.
        Рекомендую создать тикет для команды разработки.»

Пользователь: «Создай.»

Агент: [вызывает create_ticket(
          product_id="...",
          description="Аномальный рост Ошибка 500: +500% за час. Вероятная причина — деплой 2026-06-07 18:00",
          priority="high"
        )]
Бэк: ticket_service.create_ticket(..., created_by=current_admin_id)

Агент: «Тикет #4821 создан и назначен команде разработки.»
```

Тикет создаётся от имени администратора текущей сессии (`current_user` из JWT).

#### Backend-реализация

```python
# backend/app/services/analytics_ai_service.py

ANALYTICS_TOOLS = [
    {"name": "apply_filter", ...},
    {"name": "set_date_range", ...},
    {"name": "highlight_element", ...},
    {"name": "change_chart_type", ...},
    {"name": "query_metric", ...},
    {"name": "detect_anomalies", ...},
    {"name": "create_ticket", "input_schema": {
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]}
        },
        "required": ["product_id", "description", "priority"]
    }},
]

async def handle_tool(tool_name, tool_input, db, current_user_id):
    if tool_name == "query_metric":
        return await analytics_service.query_metric(**tool_input)
    elif tool_name == "detect_anomalies":
        return await analytics_service.detect_anomalies(**tool_input)
    elif tool_name == "create_ticket":
        ticket = await ticket_service.create_ticket(
            db, current_user_id,
            TicketCreate(**tool_input, source="analytics_ai")
        )
        return {"ticket_id": str(ticket.id)}
    else:
        return None  # UI-команды, бэк не выполняет
```

- Аномалии: `SELECT category, COUNT(*) FROM tickets WHERE date > NOW()-INTERVAL WHERE count > rolling_avg + 2σ`
- Хранение истории диалога: `session_id` → Redis (TTL 24ч) или таблица `ai_chat_sessions`

---

### Общие требования (АН-00–АН-05)

| Требование | Реализация |
|-----------|-----------|
| Выбор периода (сегодня/вчера/неделя/месяц/квартал/год/произвольный) | `DateRangePicker` — глобальный компонент дашборда, передаёт `date_from`/`date_to` во все запросы |
| Фильтры применяются на все графики одновременно | Context/store с фильтрами, все chart-компоненты подписаны |
| Экспорт PNG/PDF/CSV | Кнопка на каждом графике; CSV — данные через отдельный endpoint с `?format=csv` |
| Персональные настройки дашборда | `PATCH /admin/me/preferences` → `dashboard_settings: { filters: {}, chart_types: {} }` |
| Выбор серий через клик по легенде | Поведение chart library (Recharts/ECharts) из коробки |
| Tooltip с точными значениями | Стандартный tooltip в chart library |

**Chart library:** если не выбрана — рекомендация **Recharts** (React-native, TypeScript, MIT).

---

### Дашборд №1 — Сводная информация по обращениям

**Backend:** `GET /api/v1/analytics/summary?date_from=&date_to=&product_id=`

| ID | Элемент | Тип графика | Данные |
|----|---------|-------------|--------|
| АН-06 | Общее кол-во обращений (динамика) | LineChart + наложение прошлого периода | `SELECT DATE(date), COUNT(*) FROM tickets GROUP BY 1` |
| АН-07 | Всего обращений за период (KPI) | KPI-карточка + delta | Сумма за период vs предыдущий |
| АН-08 | Активные тикеты в динамике | LineChart | Статусы: принято, в_работе, требуется_информация, передано_разработчикам |
| АН-09 | Текущее кол-во открытых тикетов | KPI + разбивка по приоритетам | COUNT по `admin_priority` где статус открытый |
| АН-10 | Среднее время жизни тикета (часы) | KPI-карточка | `AVG(closed_at - date)` |
| АН-11 | Возвраты заявок в работу | LineChart | `SELECT DATE, COUNT(*) WHERE reopened_count > 0` |
| АН-12 | Процент возвратов | KPI | `reopened / total_closed * 100` |
| АН-13 | Удовлетворённость (динамика) | LineChart, средняя оценка 1–5 | `AVG(reviews.rating) GROUP BY DATE` |
| АН-14 | Распределение оценок | BarChart | `COUNT(*) GROUP BY reviews.rating` |
| АН-15 | Продукты с наихудшей удовлетворённостью | Table | `AVG(rating) GROUP BY product ORDER BY AVG ASC LIMIT 10` |

---

### Дашборд №2 — Эффективность ИИ

**Backend:** `GET /api/v1/analytics/ai?date_from=&date_to=&product_id=`

| ID | Элемент | Тип | Данные |
|----|---------|-----|--------|
| АН-16 | Доля проблем решённых ИИ (динамика) | LineChart + целевая линия 70% | Тикеты без эскалации / все тикеты |
| АН-17 | Текущая доля авто-решения | KPI + delta | Расчёт за период |
| АН-18 | ТОП-10 запросов, переводимых на оператора | Table | `final_category` WHERE эскалировано |
| АН-19 | Среднее время: ИИ vs Человек | Comparative KPI | ИИ: время от 1-го сообщения до закрытия без эскалации; Человек: `TTR` |
| АН-20 | ТОП-10 проблем, решаемых ИИ | Table | `ai_suggested_category` WHERE НЕ эскалировано |
| АН-22 | Среднее кол-во сообщений до эскалации | KPI | `AVG(message_count)` по эскалированным тикетам |
| АН-23 | Точность классификации ИИ | Table по категориям | `is_admin_changed = TRUE / total * 100` GROUP BY category |

---

### Дашборд №3 — Эффективность администратора

**Backend:** `GET /api/v1/analytics/operators?date_from=&date_to=&product_id=`

| ID | Элемент | Тип | Данные |
|----|---------|-----|--------|
| АН-24 | Нагрузка на администратора | BarChart сгруппированный | `COUNT(open/closed) GROUP BY responsible_id` |
| АН-25 | Рейтинг администраторов | Table | Закрытые тикеты, TTFR, TTR, SLA% по каждому |
| АН-26 | TTFR (время до первого ответа) | LineChart + разбивка по приоритету | `MIN(internal_comments.created_at) - tickets.date` |
| АН-27 | TTR (время полного решения) | LineChart + разбивка по приоритету | `tickets.closed_at - tickets.date` |
| АН-28 | Соблюдение SLA | BarChart по приоритетам | % тикетов где TTFR и TTR ≤ лимит |
| АН-29 | SLA нарушения по категориям | Table | TOP категорий по частоте нарушений |
| АН-30 | Heatmap: время ответа (день × час) | Heatmap | `AVG(TTFR)` GROUP BY `dow`, `hour` |
| АН-31 | Удовлетворённость по администраторам | BarChart | `AVG(reviews.rating)` GROUP BY `responsible_id` |

---

### Дашборд №4 — Пользователи

**Backend:** `GET /api/v1/analytics/users?date_from=&date_to=&product_id=`

| ID | Элемент | Тип | Данные |
|----|---------|-----|--------|
| АН-32 | Число уникальных пользователей | KPI | `COUNT(DISTINCT client_id)` |
| АН-33 | Новые пользователи за период | KPI | Клиенты с первым тикетом в периоде |
| АН-34 | Самые активные пользователи | Table (анонимизированный ID) | `COUNT(tickets) GROUP BY client_id ORDER BY COUNT DESC LIMIT 10` |
| АН-36 | Распределение по полу | PieChart | `COUNT GROUP BY clients.gender` |
| АН-37 | Распределение по возрастным группам | BarChart | 18–25, 26–35, 36–45, 46–55, 55+ |
| АН-38 | Распределение по городам | BarChart / Choropleth-карта | `COUNT GROUP BY clients.city` |
| АН-40 | Retention | LineChart | % клиентов с повторным обращением за 7/14/30 дней |

---

### Дашборд №5 — Отзывы

**Backend:** `GET /api/v1/analytics/reviews?date_from=&date_to=&product_id=`

| ID | Элемент | Тип | Данные |
|----|---------|-----|--------|
| АН-41 | ТОП-10 ключевых слов в отзывах | WordCloud + Table | TF-IDF по `reviews.comment`, разделить positive/negative |
| АН-42 | ТОП-10 категорий в отзывах | Table | `COUNT GROUP BY final_category` в reviews |
| АН-43 | Динамика позитива и негатива | LineChart (2 линии) | Оценки 4–5 и 1–2 по дням |
| АН-44 | Доля позитивных отзывов | KPI | `COUNT(rating >= 4) / COUNT(*) * 100` |
| АН-46 | Распределение оценок | BarChart | `COUNT GROUP BY rating` |
| АН-49 | Последние негативные отзывы | Table + ссылка на тикет | `SELECT * FROM reviews WHERE rating <= 2 ORDER BY created_at DESC` |

---

### Дашборд №6 — Тикеты

**Backend:** `GET /api/v1/analytics/tickets?date_from=&date_to=&product_id=`

| ID | Элемент | Тип | Данные |
|----|---------|-----|--------|
| АН-50 | ТОП-10 ключевых слов в обращениях | WordCloud + Table | TF-IDF по `tickets.keywords` |
| АН-51 | ТОП-10 категорий по частоте | BarChart | `COUNT GROUP BY final_category ORDER BY COUNT DESC` |
| АН-52 | Динамика роста проблем | LineChart | `COUNT(*) GROUP BY DATE(date)` |
| АН-53 | Текущие аномалии (авто-определение) | Карточка-список | Категории/продукты где `count_48h > rolling_avg + 2σ` |
| АН-55 | Распределение проблем по городам | BarChart | `COUNT GROUP BY clients.city` |
| АН-56 | Распределение по возрастным группам | BarChart | `COUNT GROUP BY age_bucket` |
| АН-57 | Тепловая карта проблем (день × час) | Heatmap | `COUNT GROUP BY dow, hour` |
| АН-58 | Проблемы с самым долгим TTR | Table | `AVG(closed_at - date) GROUP BY final_category ORDER BY AVG DESC LIMIT 10` |
| АН-59 | Прогноз частоты на 7 дней | LineChart | ARIMA/Prophet по историческим данным; ML-сервис в `/ml` |

---

## Открытые вопросы

| # | Вопрос | Влияет на |
|---|--------|----------|
| 1 | Читаем ли `Система аналитики.docx`? Там могут быть макеты и дополнительные требования к дашбордам | Часть 3 |
| 2 | Миграция `product` string → `product_id FK` — нужно ли конвертировать существующие данные? | КЛ-06, все тикеты |
| 3 | Какая chart library используется или будет использоваться? | Все дашборды |
| 4 | Email-нотификации — как реализованы сейчас? (SMTP / сервис / заглушка) | АД-08, КЛ-43 |
| 5 | Фоновые задачи — Celery уже есть или нужно добавить? | АД-09 (SLA авто-эскалация) |
| 6 | Карта регионов (АН-38) — внешняя библиотека или SVG-карта России? | Дашборд №4 |

---

## Порядок реализации (предлагаемый)

1. **БД:** миграция `products` + `sla_rules` + `product_id FK` в `tickets`
2. **API продуктов:** `GET/POST/PATCH /products`
3. **Клиент — тикеты:** экран предпросмотра тикета (КЛ-33, КЛ-34, КЛ-36) + reopen (КЛ-45)
4. **Клиент — ЛК:** группировка по продуктам (КЛ-08) + отображение `admin_priority` (КЛ-37)
5. **Клиент — отзывы:** `type` field + ML pipeline для тональности (КЛ-48)
6. **Админ — фильтры:** добавить `responsible_id`, `user_priority`, `admin_priority` + fulltext search (АД-11)
7. **Админ — предпочтения:** сохранение фильтров (АД-12)
8. **Админ — SLA:** таблица правил + фоновый job (АД-09)
9. **Дашборды:** backend аналитика → frontend chart-компоненты (по дашбордам 1→6)
