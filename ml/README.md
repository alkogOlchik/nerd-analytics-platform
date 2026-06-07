# Запуск 
из папки ml
```bash
uvicorn web_guide_recorder.api.server:app --host 127.0.0.1 --port 8091 --log-level info
```
Так же надо установить ollama, желательно иметь видюху cuda, на cpu будет супер долго
```bash
ollama pull gemma4:e2b
```
# Использование
эндпоинт `/query` универсальный, рекомендую его использовать для всех задач. Агент имеет сразу все tools и может выполнять все задачи. Есть вычисление Rag и браузер, от запроса он сам выберет нужные инструменты


Пример запроса:
```json
{
  "query": "https://lenta.ru сделай мне гайд о том как попасть во вкладку спорт",
  "model": "gemma4:e2b"
}
```
Модели которые можно поставить gemma4:e2b - работает быстрее, gemma4:e4b - медленнее но умнее.

---

# Полный запуск (агент + RAG + recorder)

Все команды выполняются из папки `ml/`.

## 1. Зависимости

```bash
pip install -r agent/requirements.txt
pip install -r web_guide_recorder/requirements.txt
pip install python-multipart   # для загрузки файлов в /rag/documents
```

## 2. Ollama: LLM + эмбеддинги

```bash
ollama serve &                 # если ещё не запущен (порт 11434)
ollama pull gemma4:e2b         # основная LLM (быстрая)
ollama pull gemma4:e4b         # опционально, медленнее но умнее
ollama pull nomic-embed-text   # эмбеддинги для RAG (обязательно)
```

## 3. API агента (/query, /record, /rag/*)

```bash
python -m agent.service              # запуск, по умолчанию 127.0.0.1:8090
# или напрямую uvicorn'ом:
uvicorn agent.api.server:app --host 127.0.0.1 --port 8090
```

Проверка:
```bash
curl http://127.0.0.1:8090/health
```

## 4. API web-recorder'а (отдельный сервис, если нужен напрямую)

```bash
python -m web_guide_recorder.service --host 127.0.0.1 --port 8091
```

# RAG: индексация документов

База — Chroma в persist-режиме (`./chroma_db` относительно cwd). Поэтому
все команды индексации запускай из той же папки `ml/`, что и сервис.

## Через CLI

```bash
# проиндексировать всю папку ./docs (по умолчанию)
python -m agent.tools.rag_index --source ./docs

# полная перестройка с очисткой коллекции
python -m agent.tools.rag_index --source ./docs --reset

# одиночный файл
python -m agent.tools.rag_index --source ./docs/my_note.md
```

Поддерживаемые расширения: `.md`, `.markdown`, `.txt`, `.rst`.

## Через API

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/rag/status` | размер коллекции, путь, модель эмбеддингов |
| `POST` | `/rag/search` | `{query, top_k}` — поиск по базе |
| `POST` | `/rag/documents` | multipart-загрузка файла + индексация |
| `POST` | `/rag/documents/text` | `{name, content}` — inline-документ |
| `POST` | `/rag/reindex` | переиндексировать каталог (`?reset=true`, `?source=...`) |
| `DELETE` | `/rag/collection` | сбросить коллекцию |

Примеры:
```bash
# загрузить файл
curl -X POST http://127.0.0.1:8090/rag/documents \
     -F "file=@./my_notes.md"

# загрузить текстом
curl -X POST http://127.0.0.1:8090/rag/documents/text \
     -H "Content-Type: application/json" \
     -d '{"name":"faq.md","content":"# FAQ\n..."}'

# полная перестройка
curl -X POST "http://127.0.0.1:8090/rag/reindex?reset=true"

# поиск
curl -X POST http://127.0.0.1:8090/rag/search \
     -H "Content-Type: application/json" \
     -d '{"query":"как работает recorder","top_k":3}'

# статус
curl http://127.0.0.1:8090/rag/status
```

# Переменные окружения (опционально)

| Переменная | По умолчанию | Где |
|---|---|---|
| `LLM_MODEL` | `gemma4:e4b` | модель ReAct-агента |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama |
| `OLLAMA_EMBEDDINGS_MODEL` | `nomic-embed-text` | модель эмбеддингов |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_db` | persist-каталог Chroma |
| `CHROMA_COLLECTION_NAME` | `documents` | имя коллекции |
| `RAG_TOP_K` | `4` | сколько чанков возвращать по умолчанию |
