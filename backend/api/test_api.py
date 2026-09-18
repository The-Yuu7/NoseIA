from fastapi.testclient import TestClient
from app.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


def test_login_success():
    with TestClient(app) as client:
        response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data


def test_login_invalid():
    with TestClient(app) as client:
        response = client.post("/auth/login", json={"username": "wrong_user", "password": "wrong_password"})
        assert response.status_code == 401


def test_sensor_data_streaming():
    payload = {
        "MQ2": 23231.72,
        "MQ4": 17268.26,
        "MQ135": 12320.02,
        "MQ3": 8474.87,
        "MQ7": 7553.57,
        "MQ9": 15570.25,
        "temp": 22.51,
        "humedad": 59.04
    }
    with TestClient(app) as client:
        response = client.post("/sensor_data", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "success"


def test_prediction_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/prediction")
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
