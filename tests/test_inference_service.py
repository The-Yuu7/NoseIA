from fastapi.testclient import TestClient

from conftest import load_by_path

service = load_by_path("inference_service_main", "python/inference/app/main.py")
client = TestClient(service.app)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "healthy"
    assert body["version"] == "1.0.0"


def test_predict():
    body = client.get("/predict").json()
    assert body["status"] == "success"
    assert body["prediction"] in {"ALTA", "MEDIA", "BAJA"}
    assert 0.0 <= body["confidence"] <= 1.0


def test_unknown_route_returns_404():
    assert client.get("/no-existe").status_code == 404
