#!/usr/bin/env bash
# Install all project dependencies: backend, ML agent, web guide recorder, frontend

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[install]${NC} $*"; }
warning() { echo -e "${YELLOW}[warning]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*" >&2; }

# ── helpers ────────────────────────────────────────────────────────────────

require_cmd() {
  if ! command -v "$1" &>/dev/null; then
    error "'$1' not found. $2"
    exit 1
  fi
}

pip_install() {
  local label="$1"; local req="$2"
  info "pip: $label"
  pip3 install -q -r "$req"
}

# ── checks ─────────────────────────────────────────────────────────────────

require_cmd python3 "Install Python 3.10+."
require_cmd pip3    "Install pip."
require_cmd node    "Install Node.js 18+."
require_cmd npm     "Install npm."

PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [[ "$PYTHON_MAJOR" -lt 3 || ("$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 10) ]]; then
  error "Python 3.10+ required (found $PYTHON_MAJOR.$PYTHON_MINOR)."
  exit 1
fi

# ── backend ────────────────────────────────────────────────────────────────

pip_install "backend" "$ROOT/backend/requirements.txt"

# ── ml/agent ───────────────────────────────────────────────────────────────

pip_install "ml/agent" "$ROOT/ml/agent/requirements.txt"

# ── ml/web_guide_recorder ──────────────────────────────────────────────────

pip_install "ml/web_guide_recorder" "$ROOT/ml/web_guide_recorder/requirements.txt"

info "playwright: installing Chromium browser binaries"
playwright install chromium

# ── frontend ───────────────────────────────────────────────────────────────

info "npm: frontend/nerd"
npm --prefix "$ROOT/frontend/nerd" install --legacy-peer-deps

# ── done ───────────────────────────────────────────────────────────────────

echo ""
info "All dependencies installed successfully."
echo ""
echo "  Backend:         pip packages ready"
echo "  ML agent:        pip packages ready"
echo "  Web guide:       pip packages + Chromium ready"
echo "  Frontend:        node_modules ready (frontend/nerd)"
