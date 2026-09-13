# NoseIA - Sistema Bio-E-Nose con Inteligencia Artificial para Control de Calidad de Biocombustibles

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow Lite](https://img.shields.io/badge/TensorFlow--Lite-GCN--LSTM-FF6F00.svg)](https://www.tensorflow.org/lite)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![GitLab CI](https://img.shields.io/badge/GitLab--CI-Passed-FC6D26.svg)](https://gitlab.com)

**NoseIA** es una plataforma integral de **Control de Calidad de Biocombustibles** basada en **Nariz Electrónica (E-Nose)** y redes neuronales profundas híbridas **GCN-LSTM** (Graph Convolutional Networks + Long Short-Term Memory). El sistema analiza la huella de compuestos orgánicos volátiles (VOCs) emitidos durante la pirólisis de biomasa para clasificar la pureza, calidad y tipo de combustible en tiempo real.

---

## 🚀 Arquitectura del Sistema

```
  +-----------------------+     I2C / ADC     +------------------------+
  | Array de Sensores Gas |  ---------------> | ESP32 / Raspberry Pi   |
  | MQ-2, MQ-3, MQ-4, MQ-7|                   | Inferencia Edge TFLite |
  | MQ-9, MQ-135, DHT, TC |                   +------------------------+
  +-----------------------+                               |
                                                    HTTP REST / JSON
                                                          v
                                              +------------------------+
                                              | Backend FastAPI        |
                                              | Modelo GCN-LSTM TFLite |
                                              +------------------------+
                                                          |
                                                    WebSockets / HTTP
                                                          v
                                              +------------------------+
                                              | Dashboard Web SCADA    |
                                              | Monitoreo en Vivo      |
                                              +------------------------+
```

---

## 📁 Estructura del Repositorio

```text
NoseIA/
├── .devops/            # Manifiestos Docker y SonarQube para CI/CD
├── backend/            # API REST FastAPI, suite de pruebas Pytest y modelo GCN-LSTM
├── database/           # Esquemas relacionales y persistencia SQLite / SQLAlchemy
├── docs/               # Documentación metodológica, manuales y plan de pruebas
├── frontend/           # Dashboard Web SCADA en tiempo real (HTML5/JS/Chart.js)
├── infrastructure/     # Scripts de despliegue en Raspberry Pi y drivers LCD
├── python/             # Scripts de inferencia Edge, entrenamiento y calibración real
├── .env.example        # Plantilla de variables de entorno
├── .gitignore          # Reglas de exclusión para Git
├── .gitlab-ci.yml      # Pipeline CI/CD para automatización de pruebas
├── Dockerfile          # Imagen Docker ligera basada en Python 3.11-slim
├── docker-compose.yml  # Orquestación de backend API y simulador
├── LICENSE             # Licencia de software
├── project.yml         # Configuración general del proyecto
└── README.md           # Documentación principal
```

---

## ⚡ Inicio Rápido (Despliegue Local)

### Opción 1: Entorno Virtual Python

```bash
# 1. Crear e ingresar al entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux / Raspberry Pi
# En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r backend/requirements.txt

# 3. Iniciar servidor FastAPI
uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
```

Accede al dashboard en: **`http://localhost:8000`**

### Opción 2: Despliegue con Docker

```bash
# Construir y levantar contenedores
docker compose up --build -d

# Inspeccionar logs
docker compose logs -f bioenose-backend
```

---

## 🧪 Ejecución de Pruebas Unitarias y Linters

```bash
# Pruebas automatizadas de la API (Pytest)
pytest backend/test_api.py

# Verificación de calidad de código (Flake8)
flake8 backend python infrastructure --max-line-length=120
```

---

## 📑 Endpoints de la API REST

- `GET /health`: Estado de salud del sistema y versión del modelo.
- `GET /sensor_data`: Última lectura capturada del array de sensores.
- `POST /sensor_data`: Envío de datos desde microcontroladores (ESP32/RPi).
- `GET /history`: Historial de lecturas almacenadas.
- `GET /api/prediction`: Inferencia del modelo GCN-LSTM sobre las lecturas recientes.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más información.
