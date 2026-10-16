import pickle

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import auth, database, main, models
from app.database import Base
from app.models import User

PAYLOAD = {
    "MQ2": 23231.72, "MQ4": 17268.26, "MQ135": 12320.02, "MQ3": 8474.87,
    "MQ7": 7553.57, "MQ9": 15570.25, "temp": 22.51, "humedad": 59.04,
}


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        c.post("/clear_buffer")
        yield c


class FakeInterp:
    def __init__(self, model_path=None):
        self.model_path = model_path

    def allocate_tensors(self):
        pass

    def get_input_details(self):
        return [{"index": 0}]

    def get_output_details(self):
        return [{"index": 1}]

    def set_tensor(self, idx, data):
        assert data.shape == (1, 30, 8)

    def invoke(self):
        pass

    def get_tensor(self, idx):
        return np.array([[0.1, 0.2, 0.7]], dtype=np.float32)


# ---------- auth ----------
def test_hash_password_is_deterministic_sha256():
    assert auth.hash_password("abc") == auth.hash_password("abc")
    assert len(auth.hash_password("abc")) == 64
    assert auth.hash_password("abc") != auth.hash_password("abd")


def test_verify_password_plain_hash():
    hashed = auth.hash_password("secreto")
    assert auth.verify_password("secreto", hashed)
    assert not auth.verify_password("otro", hashed)


def test_verify_password_bcrypt_placeholder():
    assert auth.verify_password("admin123", "$2b$12$placeholder")
    assert not auth.verify_password("mala", "$2b$12$placeholder")


def test_authenticate_fallback_admin(db_session):
    user = auth.authenticate_user(db_session, "admin", "admin123")
    assert user is not None and user.username == "admin"
    assert auth.authenticate_user(db_session, "admin@bioenose.com", "admin").email == "admin@bioenose.com"


def test_authenticate_unknown_or_bad_fallback(db_session):
    assert auth.authenticate_user(db_session, "nadie", "x") is None
    assert auth.authenticate_user(db_session, "admin", "incorrecta") is None


def test_authenticate_existing_user(db_session):
    db_session.add(User(username="ana", email="ana@x.com", password_hash=auth.hash_password("pw")))
    db_session.commit()
    assert auth.authenticate_user(db_session, "ana", "pw").username == "ana"
    assert auth.authenticate_user(db_session, "ana@x.com", "pw").username == "ana"
    assert auth.authenticate_user(db_session, "ana", "mal") is None


# ---------- database / models ----------
def test_get_db_yields_and_closes_session():
    gen = database.get_db()
    session = next(gen)
    assert session is not None
    with pytest.raises(StopIteration):
        next(gen)


def test_models_persist_defaults(db_session):
    db_session.add(models.SystemInfo(key="version", value="1"))
    db_session.add(models.SensorReading(
        mq2=1, mq4=1, mq135=1, mq3=1, mq7=1, mq9=1,
        temp_cam=20, humedad_cam=50, temp_reactor=400))
    db_session.commit()
    info = db_session.query(models.SystemInfo).one()
    reading = db_session.query(models.SensorReading).one()
    assert info.created_at is not None
    assert reading.timestamp is not None and reading.calidad_predicha is None


# ---------- main: modelos auxiliares ----------
def test_custom_scaler_zero_at_mean():
    scaler = main.CustomStandardScaler()
    out = scaler.transform(scaler.mean_.copy())
    assert np.allclose(out, 0.0)
    assert np.allclose(scaler.transform(scaler.mean_ + scaler.scale_), 1.0)


def test_custom_label_encoder():
    enc = main.CustomLabelEncoder(["ALTA", "BAJA", "MEDIA"])
    assert enc.inverse_transform(np.array([2, 0])) == ["MEDIA", "ALTA"]


def test_load_artifacts_fallback_defaults(tmp_path):
    scaler, enc, ref = main._load_ml_model_artifacts(
        str(tmp_path / "a"), str(tmp_path / "b"), str(tmp_path / "c"))
    assert isinstance(scaler, main.CustomStandardScaler)
    assert list(enc.classes_) == ["ALTA", "BAJA", "MEDIA"]
    assert ref is None


def test_load_artifacts_from_pickles(tmp_path):
    for name, obj in (("s.pkl", {"k": 1}), ("e.pkl", {"k": 2}), ("r.pkl", np.ones(8))):
        with open(tmp_path / name, "wb") as fh:
            pickle.dump(obj, fh)
    scaler, enc, ref = main._load_ml_model_artifacts(
        str(tmp_path / "s.pkl"), str(tmp_path / "e.pkl"), str(tmp_path / "r.pkl"))
    assert scaler == {"k": 1} and enc == {"k": 2} and np.allclose(ref, 1)


def test_load_artifacts_corrupt_reference(tmp_path):
    (tmp_path / "r.pkl").write_bytes(b"no es pickle")
    _, _, ref = main._load_ml_model_artifacts("x", "y", str(tmp_path / "r.pkl"))
    assert ref is None


# ---------- endpoints ----------
def test_health_reports_assets(client):
    data = client.get("/health").json()
    assert data["scaler_loaded"] is True and data["encoder_loaded"] is True


def test_login_response_contains_user(client):
    body = client.post("/auth/login", json={"username": "admin", "password": "admin123"}).json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"


def test_login_missing_fields_returns_422(client):
    assert client.post("/auth/login", json={"username": "x"}).status_code == 422


def test_sensor_data_invalid_payload_returns_422(client):
    bad = dict(PAYLOAD, MQ2="texto")
    assert client.post("/sensor_data", json=bad).status_code == 422
    missing = {k: v for k, v in PAYLOAD.items() if k != "temp"}
    assert client.post("/sensor_data", json=missing).status_code == 422


def test_buffer_grows_history_and_clear(client):
    for expected in (1, 2, 3):
        assert client.post("/sensor_data", json=PAYLOAD).json()["buffer_size"] == expected
    hist = client.get("/history").json()
    assert hist["count"] == 3 and len(hist["buffer"]) == 3
    assert client.post("/clear_buffer").json()["status"] == "success"
    assert client.get("/history").json()["count"] == 0


def test_prediction_waiting_until_buffer_full(client):
    for _ in range(main.TIMESTEPS - 1):
        client.post("/sensor_data", json=PAYLOAD)
    assert client.get("/api/prediction").json()["prediction"] == "Esperando datos..."


def test_prediction_fallback_without_interpreter(client, monkeypatch):
    monkeypatch.setattr(main.assets, "interpreter", None)
    for _ in range(main.TIMESTEPS):
        client.post("/sensor_data", json=PAYLOAD)
    result = client.get("/latest_result").json()
    assert result["prediction"] == "ALTA"
    assert result["is_ambient"] is False
    assert result["buffer_size"] == main.TIMESTEPS


def test_buffer_is_capped_at_timesteps(client, monkeypatch):
    monkeypatch.setattr(main.assets, "interpreter", None)
    for _ in range(main.TIMESTEPS + 5):
        body = client.post("/sensor_data", json=PAYLOAD).json()
    assert body["buffer_size"] == main.TIMESTEPS


def test_prediction_with_interpreter_and_no_scaler(client, monkeypatch):
    monkeypatch.setattr(main.assets, "interpreter", FakeInterp())
    monkeypatch.setattr(main.assets, "input_details", [{"index": 0}])
    monkeypatch.setattr(main.assets, "output_details", [{"index": 1}])
    monkeypatch.setattr(main.assets, "scaler", None)
    monkeypatch.setattr(main.assets, "label_encoder", main.CustomLabelEncoder(["ALTA", "BAJA", "MEDIA"]))
    for _ in range(main.TIMESTEPS):
        client.post("/sensor_data", json=PAYLOAD)
    result = client.get("/api/prediction").json()
    assert result["prediction"] == "MEDIA"
    assert result["confidence"] == pytest.approx(0.7)
    assert set(result["probabilities"]) == {"ALTA", "BAJA", "MEDIA"}


# ---------- lifespan ----------
def test_lifespan_loads_interpreter(monkeypatch):
    monkeypatch.setattr(main, "tflite", type("T", (), {"Interpreter": FakeInterp}))
    monkeypatch.setattr(main.os.path, "exists", lambda p: True)
    monkeypatch.setattr(main, "_load_ml_model_artifacts", lambda *a: (None, None, None))
    with TestClient(main.app) as c:
        assert c.get("/health").json()["interpreter_loaded"] is True


def test_lifespan_interpreter_failure(monkeypatch):
    class Broken:
        def Interpreter(self, model_path=None):
            raise RuntimeError("modelo corrupto")

    monkeypatch.setattr(main, "tflite", Broken())
    monkeypatch.setattr(main.os.path, "exists", lambda p: True)
    monkeypatch.setattr(main, "_load_ml_model_artifacts", lambda *a: (None, None, None))
    with TestClient(main.app) as c:
        assert c.get("/health").json()["interpreter_loaded"] is False
