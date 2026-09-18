# ======================================================================
# DOCKERFILE EN .DEVOPS - BIO-E-NOSE PIRÓLISIS
# ======================================================================
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade "pip>=23.0" && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend
COPY database /app/database
COPY python /app/python

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')" || exit 1

CMD ["sh", "-c", "python -m uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
