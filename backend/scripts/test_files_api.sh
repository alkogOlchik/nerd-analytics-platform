#!/usr/bin/env bash
# Тест: загрузка файла и чат с агентом
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
USERNAME="${TEST_USER:-testuser}"
PASSWORD="${TEST_PASS:-Test1234!}"
FILE="${1:-}"
MESSAGE="${2:-Кратко опиши что в этом документе}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*"; exit 1; }
info() { echo -e "${YELLOW}→${NC} $*"; }

# ── helpers ──────────────────────────────────────────────────────────────────

json_field() {
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d$1)" 2>/dev/null
}

http() {
    local method="$1"; shift
    curl -sf -X "$method" "$@"
}

# ── 1. login ─────────────────────────────────────────────────────────────────

info "Логин: $USERNAME"
LOGIN=$(http POST "$BASE/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}") || fail "Логин не удался (сервер недоступен?)"

TOKEN=$(echo "$LOGIN" | json_field "['access_token']") || fail "Нет access_token в ответе логина"
ok "Токен получен: ${TOKEN:0:40}…"

AUTH="-H Authorization: Bearer $TOKEN"

# ── 2. upload ─────────────────────────────────────────────────────────────────

if [[ -z "$FILE" ]]; then
    # создаём временный txt-файл для теста
    TMPFILE=$(mktemp /tmp/test_XXXXXX.txt)
    cat > "$TMPFILE" <<'EOF'
Это тестовый документ для проверки загрузки файлов.
Содержит несколько строк текста.
Цель: убедиться, что бэкенд корректно принимает, хранит и передаёт файл агенту.
EOF
    FILE="$TMPFILE"
    CLEANUP=1
fi

info "Загрузка файла: $FILE"
UPLOAD=$(http POST "$BASE/ai/files" \
    -H "Authorization: Bearer $TOKEN" \
    -F "files=@${FILE};type=text/plain") || fail "Загрузка файла не удалась"

echo "$UPLOAD" | python3 -m json.tool
FILE_ID=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])") \
    || fail "Не удалось получить file_id"
FILENAME=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['filename'])")
SIZE=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['size_bytes'])")
ok "Файл загружен: $FILENAME ($SIZE байт) → id=$FILE_ID"

# ── 3. GET /ai/files/{id} ─────────────────────────────────────────────────────

info "Получение метаданных файла"
META=$(http GET "$BASE/ai/files/$FILE_ID" \
    -H "Authorization: Bearer $TOKEN") || fail "GET /ai/files/$FILE_ID не удался"
echo "$META" | python3 -m json.tool
ok "Метаданные получены"

# ── 4. chat with file ─────────────────────────────────────────────────────────

info "Отправка сообщения агенту с файлом…"
CHAT=$(http POST "$BASE/ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$MESSAGE\", \"file_ids\": [\"$FILE_ID\"]}") || fail "POST /ai/chat не удался"

ANSWER=$(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin)['assistant_message']['message'])")
CHAT_ID=$(echo "$CHAT" | python3 -c "import sys,json; print(json.load(sys.stdin)['chat_id'])")
ok "Ответ агента (chat_id=$CHAT_ID):"
echo -e "\n${ANSWER}\n"

# ── 5. delete ─────────────────────────────────────────────────────────────────

info "Удаление файла $FILE_ID"
http DELETE "$BASE/ai/files/$FILE_ID" \
    -H "Authorization: Bearer $TOKEN" -o /dev/null
ok "Файл удалён"

# ── cleanup ───────────────────────────────────────────────────────────────────

[[ "${CLEANUP:-0}" == "1" ]] && rm -f "$FILE"

echo ""
ok "Все проверки прошли успешно"
