FROM python:3.11-slim

WORKDIR /app

# Системные зависимости для Playwright (Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget curl ca-certificates \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libxcb1 libxkbcommon0 libx11-6 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Зависимости агента
COPY agent/requirements.txt /tmp/agent-requirements.txt
RUN pip install --no-cache-dir -r /tmp/agent-requirements.txt

# Зависимости web_guide_recorder
COPY web_guide_recorder/requirements.txt /tmp/recorder-requirements.txt
RUN pip install --no-cache-dir -r /tmp/recorder-requirements.txt

# Установить браузеры Playwright
RUN playwright install chromium

# Код
COPY agent/ ./agent/
COPY web_guide_recorder/ ./web_guide_recorder/

EXPOSE 8090

CMD ["python", "-m", "agent.service", "--host", "0.0.0.0", "--port", "8090"]
