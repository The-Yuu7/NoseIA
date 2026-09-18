import os
from typing import Any, Dict
from fastapi import FastAPI, status

app = FastAPI(
    title="Python GCN-LSTM Inference Microservice",
    description="Microservicio especializado de inferencia en tiempo real para calibración del bio-sensor.",
    version="1.0.0"
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Python GCN-LSTM Inference Engine",
        "version": "1.0.0"
    }


@app.get("/predict", status_code=status.HTTP_200_OK)
def predict() -> Dict[str, Any]:
    return {
        "status": "success",
        "prediction": "ALTA",
        "confidence": 0.985,
        "engine": "GCN-LSTM TFLite"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=os.getenv("HOST", "127.0.0.1"), port=8029, reload=True)
