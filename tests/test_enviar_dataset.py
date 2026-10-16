import pandas as pd
import pytest

from conftest import load_by_path

SENSORES = ["MQ2", "MQ4", "MQ135", "MQ3", "MQ7", "MQ9", "temp", "humedad"]


@pytest.fixture
def mod(monkeypatch, tmp_path):
    m = load_by_path("enviar_dataset_under_test", "python/inference/enviar_dataset.py")
    rows = []
    for muestra, etiqueta in ((1, "ALTA"), (2, "MEDIA"), (3, "BAJA")):
        for i in range(3):
            row = {s: float(i + muestra) for s in SENSORES}
            row.update(muestra_id=muestra, etiqueta=etiqueta, tipo_plastico="PE", temp_max=430.0)
            rows.append(row)
    csv_path = tmp_path / "datos_reales.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    monkeypatch.setattr(m, "DATASET_PATH", str(csv_path))
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    monkeypatch.setenv("API_ALLOWED_HOSTS", "10.0.0.5,srv")
    return m


class Resp:
    def __init__(self, code=200, body=None):
        self.status_code = code
        self._body = body or {"buffer_size": 1}

    def json(self):
        return self._body


def feed(monkeypatch, answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(it))


def test_flujo_completo_envia_lecturas(mod, monkeypatch, capsys):
    posts = []
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())

    def fake_post(url, json=None, timeout=0):
        posts.append((url, json))
        return Resp()

    monkeypatch.setattr(mod.requests, "post", fake_post)
    # servidor, lote 1, velocidad 1 (tiempo real), Enter, salir
    feed(monkeypatch, ["localhost", "1", "1", "", "s"])
    mod.main()
    urls = [u for u, _ in posts]
    assert urls[0] == "https://localhost:8000/clear_buffer"
    assert urls.count("https://localhost:8000/sensor_data") == 3
    assert posts[1][1]["MQ2"] == 1.0
    out = capsys.readouterr().out
    assert "Grado A (Conforme)" in out and "Modo Tiempo Real" in out


def test_servidor_inalcanzable_termina(mod, monkeypatch):
    def boom(url, timeout=0):
        raise ConnectionError("sin red")

    monkeypatch.setattr(mod.requests, "get", boom)
    feed(monkeypatch, [""])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1


def test_dataset_inexistente_termina(mod, monkeypatch):
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())
    monkeypatch.setattr(mod, "DATASET_PATH", "/no/existe.csv")
    feed(monkeypatch, ["http://srv:9000"])
    with pytest.raises(SystemExit):
        mod.main()


def test_entradas_invalidas_y_lote_aleatorio(mod, monkeypatch, capsys):
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())
    monkeypatch.setattr(mod.requests, "post", lambda url, json=None, timeout=0: Resp())
    monkeypatch.setattr(mod.rng, "randint", lambda a, b: 3)
    # inválido, fuera de rango, aleatorio (lote 3 = BAJA), cámara rápida, Enter, salir
    feed(monkeypatch, ["", "abc", "99", "r", "", "", "s"])
    mod.main()
    out = capsys.readouterr().out
    assert "Entrada no válida" in out
    assert "entre 1 y 3" in out
    assert "lote aleatorio: 3" in out
    assert "Grado C (No Conforme)" in out
    assert "Cámara Rápida activado" in out


def test_purga_y_envio_con_errores_del_servidor(mod, monkeypatch, capsys):
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())

    def post(url, json=None, timeout=0):
        return Resp(500)

    monkeypatch.setattr(mod.requests, "post", post)
    feed(monkeypatch, ["10.0.0.5:8000", "2", "2", "", "s"])
    mod.main()
    out = capsys.readouterr().out
    assert "código 500" in out
    assert "API respondió 500" in out
    assert "Grado B (Desviado)" in out


def test_purga_con_excepcion_continua(mod, monkeypatch, capsys):
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())

    def post(url, json=None, timeout=0):
        if url.endswith("/clear_buffer"):
            raise TimeoutError("lento")
        return Resp()

    monkeypatch.setattr(mod.requests, "post", post)
    feed(monkeypatch, ["", "1", "", "", "s"])
    mod.main()
    assert "No se pudo purgar" in capsys.readouterr().out


def test_cancelacion_con_ctrl_c(mod, monkeypatch, capsys):
    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=0: Resp())

    def post(url, json=None, timeout=0):
        if url.endswith("/sensor_data"):
            raise KeyboardInterrupt()
        return Resp()

    monkeypatch.setattr(mod.requests, "post", post)
    feed(monkeypatch, ["", "1", "", "", "s"])
    mod.main()
    assert "Envío cancelado" in capsys.readouterr().out


def test_resolver_servidor_acepta_hosts_permitidos(mod):
    assert mod.resolver_servidor("") == "https://localhost:8000"
    assert mod.resolver_servidor("localhost") == "https://localhost:8000"
    assert mod.resolver_servidor("http://srv:9000") == "http://srv:9000"
    assert mod.resolver_servidor("10.0.0.5:8029") == "https://10.0.0.5:8029"


@pytest.mark.parametrize("entrada", [
    "http://evil.example.com",
    "http://169.254.169.254/latest/meta-data",
    "localhost:99999",
    "localhost:abc",
    "http://[::1",
])
def test_resolver_servidor_rechaza_entradas_peligrosas(mod, entrada):
    assert mod.resolver_servidor(entrada) is None


def test_host_no_permitido_termina(mod, monkeypatch, capsys):
    feed(monkeypatch, ["http://evil.example.com"])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 1
    assert "no permitido" in capsys.readouterr().out
