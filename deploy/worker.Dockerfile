FROM python:3.12-slim

WORKDIR /app
COPY backend /app/backend
RUN pip install --no-cache-dir -e /app/backend
WORKDIR /app/backend
CMD ["rq", "worker", "--url", "redis://redis:6379/0", "default"]
