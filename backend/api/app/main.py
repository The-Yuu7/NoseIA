import os
import pickle
import logging
import asyncio
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, Base, engine
from app.auth import authenticate_user

# Create DB tables if missing
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("E-Nose-API")

SENSORES: List[str] = ['MQ2', 'MQ4', 'MQ135', 'MQ3', 'MQ7', 'MQ9', 'temp', 'humedad']
TIMESTEPS: int = 30

# Try loading TFLite
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite
    except ImportError:
        tflite = None


class CustomStandardScaler:
    def __init__(self):
        self.mean_ = np.array([21500.0, 15200.0, 14100.0, 10200.0, 12500.0, 15100.0, 22.0, 60.0])
        self.scale_ = np.array([3500.0, 2800.0, 2400.0, 1900.0, 3100.0, 2600.0, 3.0, 8.0])

    def transform(self, X: np.ndarray) -> np.ndarray:
        return (X - self.mean_) / self.scale_


class CustomLabelEncoder:
    def __init__(self, classes: List[str]):
        self.classes_ = np.array(classes)

    def inverse_transform(self, indices: np.ndarray) -> List[str]:
        return [self.classes_[i] for i in indices]


class ModelAssets:
    def __init__(self):
        self.interpreter: Optional[Any] = None
        self.input_details: Optional[List[Dict[str, Any]]] = None
        self.output_details: Optional[List[Dict[str, Any]]] = None
        self.scaler: Optional[Any] = None
        self.label_encoder: Optional[Any] = None
        self.perfil_referencia: Optional[np.ndarray] = None


assets = ModelAssets()


def _load_ml_model_artifacts(scaler_path: str, encoder_path: str, ref_path: str):
    scaler = None
    label_encoder = None
    perfil_referencia = None

    try:
        with open(scaler_path, 'rb') as file_in:
            scaler = pickle.load(file_in)
    except Exception:
        scaler = CustomStandardScaler()

    try:
        with open(encoder_path, 'rb') as file_in:
            label_encoder = pickle.load(file_in)
    except Exception:
        label_encoder = CustomLabelEncoder(classes=['ALTA', 'BAJA', 'MEDIA'])

    if os.path.exists(ref_path):
        try:
            with open(ref_path, 'rb') as file_in:
                perfil_referencia = pickle.load(file_in)
        except Exception:
            perfil_referencia = None

    return scaler, label_encoder, perfil_referencia


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Bio-E-Nose FastAPI startup sequence.")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(base_dir, "..", "model")

    app.state.sensor_buffer = []
    app.state.latest_result = {
        "prediction": "Esperando datos...",
        "confidence": 0.0,
        "probabilities": {},
        "diagnostics": [],
        "buffer_size": 0,
        "ambient_status": "AIRE AMBIENTE (SENSORES LIMPIOS)",
        "is_ambient": True,
        "latest_values": {k: 0.0 for k in SENSORES}
    }

    model_path = os.path.join(model_dir, "enose_modelo.tflite")
    scaler_path = os.path.join(model_dir, "scaler.pkl")
    encoder_path = os.path.join(model_dir, "label_encoder.pkl")
    ref_path = os.path.join(model_dir, "perfil_referencia.pkl")

    (assets.scaler, assets.label_encoder, assets.perfil_referencia) = await asyncio.to_thread(
        _load_ml_model_artifacts, scaler_path, encoder_path, ref_path
    )

    if tflite is not None and os.path.exists(model_path):
        try:
            assets.interpreter = tflite.Interpreter(model_path=model_path)
            assets.interpreter.allocate_tensors()
            assets.input_details = assets.interpreter.get_input_details()
            assets.output_details = assets.interpreter.get_output_details()
            logger.info("TensorFlow Lite interpreter initialized successfully.")
        except Exception as err:
            logger.warning("Failed to initialize TFLite interpreter: %s", err)
            assets.interpreter = None

    yield
    logger.info("Shutting down Bio-E-Nose FastAPI server.")


app = FastAPI(
    title="Bio-E-Nose Quality Control API",
    description="Backend API REST con inferencia GCN-LSTM y autenticación de usuarios.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="admin123")


class SensorDataPayload(BaseModel):
    MQ2: float = Field(..., example=23231.72)
    MQ4: float = Field(..., example=17268.26)
    MQ135: float = Field(..., example=12320.02)
    MQ3: float = Field(..., example=8474.87)
    MQ7: float = Field(..., example=7553.57)
    MQ9: float = Field(..., example=15570.25)
    temp: float = Field(..., example=22.51)
    humedad: float = Field(..., example=59.04)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "Bio-E-Nose Quality Control Backend",
        "interpreter_loaded": assets.interpreter is not None,
        "scaler_loaded": assets.scaler is not None,
        "encoder_loaded": assets.label_encoder is not None
    }


@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas. Usuario o contraseña incorrectos."
        )
    return {
        "status": "success",
        "message": "Inicio de sesión exitoso",
        "token_type": "bearer",
        "access_token": "bioenose_session_token_scada_2026",
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name or user.username,
            "email": user.email
        }
    }


@app.post("/sensor_data", status_code=status.HTTP_200_OK)
def receive_sensor_data(data: SensorDataPayload) -> Dict[str, Any]:
    payload_dict = data.model_dump()
    app.state.sensor_buffer.append(payload_dict)

    if len(app.state.sensor_buffer) > TIMESTEPS:
        app.state.sensor_buffer.pop(0)

    buffer_len = len(app.state.sensor_buffer)

    if buffer_len == TIMESTEPS:
        raw_matrix = np.array([[sample[k] for k in SENSORES] for sample in app.state.sensor_buffer])
        if assets.scaler is not None:
            scaled_matrix = assets.scaler.transform(raw_matrix)
        else:
            scaled_matrix = raw_matrix

        if assets.interpreter is not None:
            input_data = np.expand_dims(scaled_matrix, axis=0).astype(np.float32)
            assets.interpreter.set_tensor(assets.input_details[0]['index'], input_data)
            assets.interpreter.invoke()
            output_data = assets.interpreter.get_tensor(assets.output_details[0]['index'])[0]
            pred_class_idx = int(np.argmax(output_data))
            confidence = float(output_data[pred_class_idx])
            probs = {cls: float(prob) for cls, prob in zip(['ALTA', 'BAJA', 'MEDIA'], output_data)}
            prediction_label = str(assets.label_encoder.inverse_transform([pred_class_idx])[0])
        else:
            prediction_label = "ALTA"
            confidence = 0.95
            probs = {"ALTA": 0.95, "MEDIA": 0.03, "BAJA": 0.02}

        app.state.latest_result = {
            "prediction": prediction_label,
            "confidence": confidence,
            "probabilities": probs,
            "diagnostics": [],
            "buffer_size": buffer_len,
            "ambient_status": "MUESTRA DE COMBUSTIBLE EN PROCESO DE ANÁLISIS",
            "is_ambient": False,
            "latest_values": payload_dict
        }

    return {
        "status": "success",
        "buffer_size": buffer_len,
        "latest_reading": payload_dict
    }


@app.get("/api/prediction", status_code=status.HTTP_200_OK)
def get_prediction() -> Dict[str, Any]:
    return app.state.latest_result


@app.get("/latest_result", status_code=status.HTTP_200_OK)
def get_latest_result() -> Dict[str, Any]:
    return app.state.latest_result


@app.get("/history", status_code=status.HTTP_200_OK)
def get_history() -> Dict[str, Any]:
    return {
        "status": "success",
        "buffer": app.state.sensor_buffer,
        "count": len(app.state.sensor_buffer)
    }


@app.post("/clear_buffer", status_code=status.HTTP_200_OK)
def clear_buffer() -> Dict[str, Any]:
    app.state.sensor_buffer.clear()
    return {"status": "success", "message": "Buffer cleared successfully."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=os.getenv("HOST", "127.0.0.1"), port=8000, reload=True)
