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

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
