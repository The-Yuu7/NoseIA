# Documentación CI/CD y Calidad de Código - Bio-E-Nose

Este documento define la tubería de integración continua y despliegue continuo (CI/CD) para el proyecto **Control de Calidad de Biocombustibles mediante Nariz Electrónica e Inteligencia Artificial (GCN-LSTM)**.

## Arquitectura del Pipeline

```
+-----------+      +-----------+      +-----------+      +-----------+
|   LINT    | ---> |   TEST    | ---> |   BUILD   | ---> |  DEPLOY   |
| (flake8)  |      | (pytest)  |      | (docker)  |      |   (rpi)   |
+-----------+      +-----------+      +-----------+      +-----------+
```

### Etapas principales:
1. **Linting & Formato (`lint`)**: Validación sintáctica y estilo PEP8.
2. **Pruebas Unitarias e Integración (`test`)**: Ejecución automatizada de Pytest y cobertura de pruebas para endpoints FastAPI.
3. **Construcción de Contenedores (`build`)**: Empaquetado en imagen Docker para arquitectura ARM64/x86.
4. **Despliegue (`deploy`)**: Despliegue en caliente en la Raspberry Pi 4 B.

## Ejecución Local de Pruebas

Para ejecutar las pruebas en este directorio localmente:

```bash
cd backend
python -m pytest test_api.py -v
```
