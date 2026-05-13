# =========================================================
# Stage 1: Build frontend
# =========================================================
FROM node:20-alpine AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# =========================================================
# Stage 2: Python runtime
# =========================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# System deps for cryptography wheels (most have prebuilt wheels; keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /web/dist ./frontend_dist

# SQLite data volume mount point (Railway: attach a volume here)
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8000

# Use PORT env on Railway
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
