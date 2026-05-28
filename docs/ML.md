# Проверка связи backend ↔ ML

Backend ходит в ML по адресу из `ML_SERVICE_URL` (по умолчанию `http://127.0.0.1:8091`).

Контракт:

```
POST {ML_SERVICE_URL}/query
{"query": "текст", "model": "gemma4:e2b"}

→ {"answer": "...", "model": "gemma4:e2b", ...}
```

## 1. Что должен поднять ML

В папке `ml/` нужен сервис с эндпоинтом **`/query`** — это **agent**, не web_guide_recorder:

```powershell
cd ml
pip install -r agent/requirements.txt
python -m agent.service --port 8091
```

Плюс Ollama и модель:

```powershell
ollama pull gemma4:e2b
ollama serve
```

Подробности — в `ml/README.md` (не меняем файлы в `ml/`, только читаем).

## 2. Прямая проверка ML (без backend)

### Health

```powershell
Invoke-RestMethod http://127.0.0.1:8091/health
```

Ожидание: `{"status":"ok"}` или аналог.

### Query

```powershell
$body = '{"query":"Ответь одним словом: ок","model":"gemma4:e2b"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8091/query -ContentType "application/json" -Body $body
```

Ожидание: JSON с полем **`answer`**.  
Первый запрос на CPU может идти **несколько минут** — это нормально для Ollama.

### curl

```bash
curl http://127.0.0.1:8091/health
curl -X POST http://127.0.0.1:8091/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Привет","model":"gemma4:e2b"}'
```

## 3. Проверка через backend

1. Запущены: Postgres, `uvicorn backend.app.main:app --port 8001`
2. В `backend/.env`: `ML_SERVICE_URL=http://127.0.0.1:8091`
3. Логин и токен:

```powershell
$base = "http://127.0.0.1:8001"
$login = '{"username":"ВАШ_USER","password":"ВАШ_PASS"}' 
$t = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType "application/json" -Body $login
$h = @{ Authorization = "Bearer $($t.access_token)" }
```

4. Чат (прокси в ML):

```powershell
$chat = '{"message":"Привет","model":"gemma4:e2b"}'
Invoke-RestMethod -Method Post -Uri "$base/ai/chat" -Headers $h -ContentType "application/json" -Body $chat
```

| Результат | Значение |
|-----------|----------|
| `200` + `assistant_message` | Связь OK |
| `502` + `ML service unavailable` | Backend не достучался до ML |
| `401` / `403` | Проблема с JWT, не с ML |

То же через Swagger: `POST /ai/chat` или `POST /ai/classify/ticket`.

## 4. Чеклист проблем

| Симптом | Что проверить |
|---------|----------------|
| Connection refused на 8091 | ML не запущен или другой порт |
| 404 на `/query` | Запущен `web_guide_recorder` вместо `agent.service` |
| Долго висит | Ollama не запущен / модель не скачана |
| 502 из backend | `ML_SERVICE_URL` в `.env` не совпадает с портом ML |
| Пустой `answer` | Ответ ML в неожиданном формате — смотри `ml_response` в ответе `/ai/chat` |

## 5. Переменная окружения

`backend/.env`:

```
ML_SERVICE_URL=http://127.0.0.1:8091
```

После смены — перезапусти uvicorn.
