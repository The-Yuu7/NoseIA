import csv
import os
import sys

import numpy as np
import pytest

MODULES = ["rpi", "diag"]


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)


def read_log(workdir):
    with open(workdir / "data" / "bitacora_ciclos.csv", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.parametrize("key", MODULES)
def test_encontrar_archivo(inferencia_modules, tmp_path, key):
    mod = inferencia_modules[key]
    (tmp_path / "a.txt").write_text("x")
    assert mod.encontrar_archivo("a.txt", ["/no/existe", str(tmp_path)]) == str(tmp_path / "a.txt")
    assert mod.encontrar_archivo("b.txt", [str(tmp_path)]) is None


@pytest.mark.parametrize("key", MODULES)
def test_obtener_ram_usada_con_y_sin_psutil(inferencia_modules, monkeypatch, key):
    mod = inferencia_modules[key]

    class FakeProcess:
        def __init__(self, pid):
            pass

        def memory_info(self):
            return type("M", (), {"rss": 100 * 1024 * 1024})()

    fake_psutil = type("P", (), {"Process": FakeProcess})
    monkeypatch.setattr(mod, "psutil", fake_psutil, raising=False)
    monkeypatch.setattr(mod, "psutil_available", True)
    assert mod.obtener_ram_usada() == 100.0
    monkeypatch.setattr(mod, "psutil_available", False)
    assert 30 < mod.obtener_ram_usada() < 70


@pytest.mark.parametrize("key", MODULES)
def test_bitacora_numeracion_y_guardado(inferencia_modules, tmp_path, key):
    mod = inferencia_modules[key]
    ruta = str(tmp_path / "sub" / "bitacora.csv")
    assert mod.obtener_proximo_lote_bitacora(ruta) == 1
    fila = {c: 1 for c in [
        'Lote_N', 'Fecha_Hora', 'Tipo_Plastico', 'Temp_Max_C', 'Frec_Muestreo_Hz',
        'Res_ADC_bits', 'Latencia_Inferencia_ms', 'RAM_Usada_MB',
        'Clase_Predictiva_IA', 'Confianza_porc', 'Etiqueta_Real', 'Concordancia']}
    fila['Lote_N'] = 7
    mod.guardar_en_bitacora(fila, ruta)
    mod.guardar_en_bitacora(dict(fila, Lote_N=8), ruta)
    with open(ruta) as fh:
        assert len(fh.readlines()) == 3  # una cabecera + dos filas
    assert mod.obtener_proximo_lote_bitacora(ruta) == 9


@pytest.mark.parametrize("key", MODULES)
def test_bitacora_corrupta_reinicia_en_1(inferencia_modules, tmp_path, key):
    mod = inferencia_modules[key]
    ruta = tmp_path / "mala.csv"
    ruta.write_text("otra,cosa\n1,2\n")
    assert mod.obtener_proximo_lote_bitacora(str(ruta)) == 1
    ruta.write_text("")
    assert mod.obtener_proximo_lote_bitacora(str(ruta)) == 1


# ---------- diagnóstico ----------
def test_diagnostico_sin_perfil(inferencia_modules):
    out = inferencia_modules["diag"].diagnosticar_diferencias(np.zeros((30, 8)), None)
    assert len(out) == 1 and "Sin perfil" in out[0]


def test_diagnostico_sin_desviaciones(inferencia_modules):
    out = inferencia_modules["diag"].diagnosticar_diferencias(np.zeros((30, 8)), np.zeros(8))
    assert "Sin alertas" in out[0]


def test_diagnostico_alertas_alto_y_bajo(inferencia_modules):
    ventana = np.zeros((30, 8))
    ventana[:, 4] = 2.5    # MQ7 alto
    ventana[:, 7] = -3.0   # humedad bajo
    out = inferencia_modules["diag"].diagnosticar_diferencias(ventana, np.zeros(8))
    assert len(out) == 2
    assert "MQ7 ALTO" in out[0] and "CO elevado" in out[0]
    assert "humedad BAJO" in out[1]


def test_diagnostico_umbral_exacto_no_alerta(inferencia_modules):
    ventana = np.ones((30, 8))  # diferencia == 1.0, no supera el umbral
    out = inferencia_modules["diag"].diagnosticar_diferencias(ventana, np.zeros(8))
    assert "Sin alertas" in out[0]


def test_diagnostico_sensor_sin_descripcion(inferencia_modules, monkeypatch):
    mod = inferencia_modules["diag"]
    monkeypatch.setattr(mod, "DIAGNOSTICOS", {})
    ventana = np.zeros((30, 8))
    ventana[:, 0] = 5
    out = mod.diagnosticar_diferencias(ventana, np.zeros(8))
    assert out == ["  [ALERTA] MQ2 ALTO (desviación: +5.00 std dev)"]


# ---------- main(): simulación ----------
@pytest.mark.parametrize("key", MODULES)
def test_main_simulacion_genera_bitacora(inferencia_modules, workdir, monkeypatch, capsys, key):
    mod = inferencia_modules[key]
    monkeypatch.setattr(sys, "argv", ["prog", "--sim", "--test"])
    mod.main()
    rows = read_log(workdir)
    assert len(rows) == 1
    row = rows[0]
    assert row["Lote_N"] == "1" and row["Clase_Predictiva_IA"] == "ALTA"
    assert row["Concordancia"] == "ACERTADO"
    assert float(row["Confianza_porc"]) == pytest.approx(70.0)
    assert row["Tipo_Plastico"] == "PP"
    assert "Ciclo de Lote completado" in capsys.readouterr().out


@pytest.mark.parametrize("key", MODULES)
def test_main_simulacion_segundo_lote_y_fallido(inferencia_modules, workdir, monkeypatch, key):
    import pandas as pd
    df = pd.read_csv(workdir / "datos_etiquetados.csv")
    df["clase_calidad"] = "BAJA"
    df.to_csv(workdir / "datos_etiquetados.csv", index=False)
    monkeypatch.setattr(sys, "argv", ["prog", "--sim", "--test"])
    mod = inferencia_modules[key]
    mod.main()
    mod.main()
    rows = read_log(workdir)
    assert [r["Lote_N"] for r in rows] == ["1", "2"]
    assert rows[0]["Concordancia"] == "FALLIDO"


def test_main_diag_imprime_analisis(inferencia_modules, workdir, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["prog", "--sim", "--test"])
    inferencia_modules["diag"].main()
    assert "ANÁLISIS DE DESVIACIÓN" in capsys.readouterr().out


@pytest.mark.parametrize("key", MODULES)
def test_main_sin_archivos_requeridos(inferencia_modules, tmp_path, monkeypatch, key):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["prog", "--sim"])
    with pytest.raises(SystemExit) as exc:
        inferencia_modules[key].main()
    assert exc.value.code == 1


@pytest.mark.parametrize("key", MODULES)
def test_main_falla_interprete(inferencia_modules, workdir, monkeypatch, key):
    mod = inferencia_modules[key]

    class Roto:
        def Interpreter(self, model_path=None):
            raise ValueError("modelo inválido")

    monkeypatch.setattr(mod, "tflite", Roto())
    monkeypatch.setattr(sys, "argv", ["prog", "--sim"])
    with pytest.raises(SystemExit):
        mod.main()


@pytest.mark.parametrize("key", MODULES)
def test_main_sin_dataset_de_simulacion(inferencia_modules, workdir, monkeypatch, key):
    os.remove(workdir / "datos_etiquetados.csv")
    monkeypatch.setattr(sys, "argv", ["prog", "--sim"])
    with pytest.raises(SystemExit):
        inferencia_modules[key].main()


@pytest.mark.parametrize("key", MODULES)
def test_main_keyboard_interrupt(inferencia_modules, workdir, monkeypatch, capsys, key):
    mod = inferencia_modules[key]
    monkeypatch.setattr(mod.np, "array", lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(sys, "argv", ["prog", "--sim", "--test"])
    mod.main()
    assert not (workdir / "data").exists()


# ---------- main(): modo serial físico ----------
class FakeSerial:
    instances = []

    def __init__(self, port, baud, timeout=None):
        self.closed = False
        self.lines = [b"", b"abc,def\n", b"1,2,3\n"]
        FakeSerial.instances.append(self)

    def readline(self):
        if self.lines:
            return self.lines.pop(0)
        return b"1000,2000,3000,4000,5000,6000,22.5,60.0\n"

    def close(self):
        self.closed = True


@pytest.mark.parametrize("key", MODULES)
def test_main_modo_serial(inferencia_modules, workdir, monkeypatch, key):
    mod = inferencia_modules[key]
    monkeypatch.setattr(mod, "serial", FakeSerial, raising=False)
    monkeypatch.setattr(mod, "pyserial_available", True)
    # el módulo usa serial.Serial(...): exponemos la clase con ese nombre
    monkeypatch.setattr(mod, "serial", type("S", (), {"Serial": FakeSerial}), raising=False)
    respuestas = iter(["2", "455.5", "3", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))
    monkeypatch.setattr(sys, "argv", ["prog", "--port", "/dev/fake"])
    mod.main()
    row = read_log(workdir)[0]
    assert row["Tipo_Plastico"] == "PP"
    assert row["Temp_Max_C"] == "455.5"
    assert row["Etiqueta_Real"] == "BAJA"
    assert FakeSerial.instances[-1].closed is True


@pytest.mark.parametrize("key", MODULES)
def test_main_serial_entradas_invalidas_usan_defaults(inferencia_modules, workdir, monkeypatch, key):
    mod = inferencia_modules[key]
    monkeypatch.setattr(mod, "pyserial_available", True)
    monkeypatch.setattr(mod, "serial", type("S", (), {"Serial": FakeSerial}), raising=False)
    respuestas = iter(["9", "no-numero", "9", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(respuestas))
    monkeypatch.setattr(sys, "argv", ["prog"])
    mod.main()
    row = read_log(workdir)[0]
    assert row["Tipo_Plastico"] == "MIX"
    assert row["Temp_Max_C"] == "430.0"
    assert row["Etiqueta_Real"] == "ALTA"


@pytest.mark.parametrize("key", MODULES)
def test_main_serial_no_disponible_cae_a_simulacion(inferencia_modules, workdir, monkeypatch, key):
    mod = inferencia_modules[key]

    class SerialRoto:
        @staticmethod
        def Serial(*a, **k):
            raise OSError("puerto ocupado")

    monkeypatch.setattr(mod, "pyserial_available", True)
    monkeypatch.setattr(mod, "serial", SerialRoto, raising=False)
    monkeypatch.setattr(sys, "argv", ["prog", "--test"])
    mod.main()
    assert len(read_log(workdir)) == 1
