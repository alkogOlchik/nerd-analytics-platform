# SPEC: Рефакторинг AssistantScreen — привязка диалогов к тикетам

## Контекст

Текущее состояние:
- Сессии чата хранятся в **localStorage** (не на бэкенде) — любой пользователь видит чужие сессии на этом устройстве, нет персистентности между устройствами
- При создании диалога тикет **не создаётся автоматически** — только через эскалацию
- Нет кнопки «Проблема решена»
- Статусы тикетов фронта (`"open"`, `"in_progress"`, `"closed"`, `"reopened"`) не совпадают с новыми требованиями бизнеса

---

## Требования (8 пунктов)

1. **Изоляция истории**: каждый пользователь видит только свои диалоги
2. **Точки входа**: кнопка `+` в `ChatHistory` или `PromptCard` на `MainScreen`
3. **Автосоздание тикета**: при отправке первого сообщения сразу создаётся тикет-черновик (`title="Новое обращение"`, `status="in_progress"`) + вкладка в истории; ML переименовывает тикет после анализа
4. **ИИ-ассистент**: следует правилам ML-сервиса, выясняет проблему
5. **Кнопка «Проблема решена»**: появляется после каждого ответа ассистента
6. **Закрытие через ИИ**: нажатие → статус тикета `"closed"`, сообщение «Рад помочь! Обращение закрыто», чат заблокирован
7. **Передача оператору**: если ИИ не справился или пользователь написал «переведи на оператора» → статус `"waiting_for_operator"`
8. **Статусы на фронте**: `in_progress`, `waiting_for_operator`, `in_operator_processing`, `closed`

---

## Решения по трём вопросам интервью

| Вопрос | Решение |
|--------|---------|
| Старый статус `accepted` | Оставить, добавить `waiting_for_operator` и `in_operator_processing` |
| Поле title | Добавить `title VARCHAR(255)` в таблицу `tickets` (миграция) |
| Сигнал кнопки «Проблема решена» | Показывать после каждого ответа ассистента |

---

## Архитектурный план

### Backend (7 файлов)

#### 1. Миграция `010_add_ticket_title_and_chat_statuses.py`
```sql
ALTER TABLE tickets ADD COLUMN title VARCHAR(255);
ALTER TABLE tickets ALTER COLUMN product DROP NOT NULL;
```
- `title` nullable (default NULL → при создании через чат = "Новое обращение")
- `product` nullable (авто-тикет из чата не знает продукт)

#### 2. `backend/app/models/ticket.py`
```python
title: Mapped[str | None] = mapped_column(String(255), nullable=True)
product: Mapped[str | None] = mapped_column(String(64), nullable=True)
```

#### 3. `backend/app/models/enums.py`
Добавить в `TicketStatus`:
```python
waiting_for_operator = "waiting_for_operator"
in_operator_processing = "in_operator_processing"
```

#### 4. `backend/app/schemas/ticket.py`
Добавить `title: str | None` в `TicketResponse`.

#### 5. `backend/app/schemas/ai.py`
```python
class ChatResponse(BaseModel):
    chat_id: uuid.UUID
    ticket_id: uuid.UUID          # НОВОЕ: id авто-созданного тикета
    ticket_status: str            # НОВОЕ: текущий статус тикета
    ticket_title: str             # НОВОЕ: текущее название тикета
    solution_offered: bool = True # НОВОЕ: всегда True после ответа ассистента
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    ml_response: dict
    escalation: EscalationOffer | None = None

class ChatSessionResponse(BaseModel):
    id: uuid.UUID                 # = chat_id
    title: str                    # из ticket.title
    ticket_id: uuid.UUID | None
    ticket_status: str | None     # НОВОЕ
    created_at: datetime
    updated_at: datetime
    last_message: str | None = None
```

#### 6. `backend/app/services/ai_service.py`
Изменения в функции `chat()`:

**Если `data.chat_id is None` (новый чат):**
```python
# Создать тикет-черновик
deadline = now + timedelta(days=7)
ticket = Ticket(
    client_id=client_id,
    product=data.product,     # может быть None
    title="Новое обращение",
    status="in_progress",
    priority="medium",
    date=now, deadline=deadline,
)
db.add(ticket)
await db.flush()
ticket_id = ticket.id
# Все сообщения этого чата будут linked к этому ticket_id
```

**После ML-ответа (только первое сообщение):**
```python
if is_first_message:
    # Параллельно генерировать название
    title_result = await ml_client.query(
        f"Придумай краткое название для обращения (5-7 слов, только текст, без кавычек): {user_text}",
        model=data.model
    )
    ticket.title = title_result.answer.strip()[:100]
```

**Детект оператора:**
```python
OPERATOR_PHRASES = ["переведи на оператора", "хочу оператора", "позови оператора", "человека", "живого человека"]
if data.request_human or any(phrase in user_text.lower() for phrase in OPERATOR_PHRASES):
    ticket.status = "waiting_for_operator"
```

**Возврат:**
```python
return chat_id, ticket_id, ticket_status, ticket_title, user_msg, assistant_msg, ml_response, escalation
```

#### 7. `backend/app/api/v1/ai.py`

**Новые эндпоинты:**

```
GET  /ai/chat/sessions
     → list[ChatSessionResponse] для текущего пользователя
     Логика: GROUP BY chat_id, JOIN tickets ON ticket_id

POST /ai/chat/{chat_id}/resolve
     → { ticket_id, status: "closed" }
     Логика: ticket.status = "closed", ticket.closed_at = now

POST /ai/chat/{chat_id}/operator
     → { ticket_id, status: "waiting_for_operator" }
     Логика: ticket.status = "waiting_for_operator"
```

---

### Frontend (13 файлов)

#### 8. `data/sources/Assistant/types.ts`
```typescript
interface ApiChatResponse {
  chat_id: string
  ticket_id: string
  ticket_status: string
  ticket_title: string
  solution_offered: boolean
  user_message: MessageDto
  assistant_message: MessageDto
  escalation: EscalationOffer | null
}

interface ChatSessionDto {
  id: string          // chat_id
  title: string       // ticket.title
  ticket_id: string | null
  ticket_status: string | null
  created_at: string
  updated_at: string
  last_message?: string
}
```

#### 9. `data/sources/Assistant/index.ts`
- Удалить всё что связано с localStorage
- `getSessions()` → `GET /ai/chat/sessions`
- Добавить `resolveChat(chatId)` → `POST /ai/chat/{chatId}/resolve`
- Добавить `escalateToOperator(chatId)` → `POST /ai/chat/{chatId}/operator`

#### 10. `data/repositories/Assistant/types.ts`
```typescript
interface ChatSession {
  id: string
  title: string
  ticketId: string | null
  ticketStatus: string | null    // НОВОЕ
  createdAt: string
  updatedAt: string
  lastMessage?: string
}

interface SendMessageResult {
  userMessage: Message
  assistantMessage: Message
  solutionOffered: boolean       // НОВОЕ
  ticketId: string | null        // НОВОЕ
  ticketStatus: string           // НОВОЕ
  ticketTitle: string            // НОВОЕ
  escalation: EscalationInfo | null
}

// Аналогично CreateSessionResult
```

#### 11. `data/repositories/Assistant/index.ts`
- Обновить `mapSession` — добавить `ticketId`, `ticketStatus`
- Обновить маппинг `sendMessage`/`createSession` — добавить `solutionOffered`, `ticketId`, `ticketStatus`, `ticketTitle`
- Добавить `resolveChat(chatId)` и `escalateToOperator(chatId)`

#### 12. `data/repositories/Tickets/types.ts`
```typescript
export type TicketStatus = "open" | "in_progress" | "closed" | "reopened"
  | "waiting_for_operator" | "in_operator_processing"  // НОВЫЕ

export interface Ticket {
  ...
  title: string | null   // НОВОЕ
}
```

#### 13. `data/sources/Tickets/types.ts`
Добавить новые статусы и `title` в `TicketDto`.

#### 14–15. `domain/Assistant/useResolveChat/index.ts` (новый)
```typescript
export const useResolveChat = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (chatId: string) => assistantRepository.resolveChat(chatId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CHAT_SESSIONS_QUERY_KEY })
    },
  })
}
```
Аналогично `useEscalateToOperator`.

#### 16. `domain/Assistant/index.ts`
Экспортировать новые хуки.

#### 17. `screens/AssistantScreen/index.tsx`
**Добавить:**
- State: `ticketId`, `ticketStatus`, `ticketTitle`, `solutionOffered`
- После каждого ответа ассистента: кнопка «Проблема решена» (если `ticketStatus !== "closed"`)
- При нажатии «Проблема решена»: `resolveChat(sessionId)` → установить статус "closed", показать «Рад помочь! Обращение закрыто», заблокировать `<ChatInput>`
- Если `ticketStatus === "waiting_for_operator"` — показать баннер «Обращение передано оператору», заблокировать чат
- Убрать `EscalationBanner` (заменено автоматическим созданием тикета)

#### 18. `modules/ChatHistory/index.tsx`
Показывать статус рядом с названием сессии:
```tsx
const STATUS_LABEL: Record<string, string> = {
  in_progress: "в работе",
  waiting_for_operator: "ожидание",
  in_operator_processing: "у оператора",
  closed: "закрыт",
}
```

#### 19. `screens/TicketsScreen/index.tsx`
```typescript
const TABS = [
  { value: "all", label: "Все" },
  { value: "in_progress", label: "В работе" },
  { value: "waiting_for_operator", label: "Ожидание оператора" },
  { value: "in_operator_processing", label: "У оператора" },
  { value: "closed", label: "Закрыты" },
]

const STATUS_LABELS = {
  in_progress: "В работе",
  waiting_for_operator: "Ожидание оператора",
  in_operator_processing: "У оператора",
  closed: "Закрыт",
  // backward compat
  open: "Открыт",
  reopened: "Переоткрыт",
}
```

#### 20. `modules/TicketCard/index.tsx`
Отображать `ticket.title` вместо/рядом с `ticket.product`.

---

## Порядок реализации

1. Миграция БД
2. Backend (модель → схемы → сервис → API)
3. Frontend types/sources/repositories
4. Frontend domain хуки
5. Frontend screens/components

## Потенциальные проблемы

- **product NOT NULL**: миграция сделает `product` nullable; существующий код `TicketCreate` всё ещё требует product — нужно убедиться что создание тикета через чат не использует `TicketCreate` схему напрямую
- **Старые статусы на русском**: существующие тикеты с `"принято"`, `"в_работе"` и т.д. — `STATUS_LABELS` должен иметь fallback для них
- **ML title latency**: генерация названия выполняется параллельно с основным ответом через `asyncio.gather`
- **localStorage cleanup**: при деплое старые localStorage-данные у пользователей станут невалидными; решение: в `getSessions()` при загрузке игнорировать localStorage
