FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY backend/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
