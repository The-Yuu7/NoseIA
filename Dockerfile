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

# Puerto expuesto para el servidor SCADA y API
EXPOSE 8000

# Comando por defecto para iniciar el servidor uvicorn
CMD ["python", "-m", "uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
