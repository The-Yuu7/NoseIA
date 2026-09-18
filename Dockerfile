# ======================================================================
# DOCKERFILE OFICIAL - BIO-E-NOSE PIRÓLISIS (FASTAPI + GCN-LSTM)
# ======================================================================
FROM python:3.10-slim

# Evitar escritura de bytecode de Python y búfer de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python desde backend
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade "pip>=23.0" && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copiar toda la estructura del proyecto en el contenedor
COPY backend /app/backend
COPY frontend /app/frontend
COPY database /app/database
COPY python /app/python

# Crear usuario no privilegiado para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

ARG PORT=8000
ENV PORT=${PORT}
EXPOSE ${PORT}

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')" || exit 1

CMD ["sh", "-c", "python -m uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
