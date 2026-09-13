# Guía de Despliegue con Docker - Bio-E-Nose

Este documento contiene las instrucciones para levantar todo el sistema **Bio-E-Nose (Backend FastAPI + Modelo GCN-LSTM + Dashboard SCADA)** utilizando Docker y Docker Compose.

## 🐳 Estructura de Dockerización

* **`Dockerfile`**: Archivo de construcción principal ubicado en la raíz de `pruebas/` e impulsado por Python 3.10-slim.
* **`docker-compose.yml`**: Orquestador multi-contenedor (Backend API + Simulador de sensores).
* **`.devops/Dockerfile`**: Copia de respaldo para el servidor de CI/CD de GitLab.

---

## 🚀 Comandos para Ejecutar con Docker

### Option 1: Levantar con Docker Compose (Recomendado)

Desde la carpeta `pruebas/`:

```bash
# Construir y levantar todos los contenedores en segundo plano
docker compose up --build -d
```

* **Backend + Frontend SCADA UI:** `http://localhost:8000`
* **Swagger API Docs:** `http://localhost:8000/docs`

#### Ver logs del contenedor:
```bash
docker compose logs -f
```

#### Detener los contenedores:
```bash
docker compose down
```

---

### Option 2: Construir y Levantar con Docker Directo

```bash
# 1. Construir la imagen
docker build -t bioenose:latest .

# 2. Ejecutar el contenedor en el puerto 8000
docker run -d -p 8000:8000 --name bioenose_app bioenose:latest
```
