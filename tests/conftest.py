import importlib.util
import os
import pickle
import sys
import types

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFERENCE_DIR = os.path.join(ROOT, "python", "inference")


class FakeInterpreter:
    """Intérprete TFLite falso: devuelve siempre la misma distribución de probabilidades."""

    def __init__(self, model_path=None):
        self.model_path = model_path
        self._tensor = None

    def allocate_tensors(self):
        return None

    def get_input_details(self):
        return [{"index": 0}]

    def get_output_details(self):
        return [{"index": 1}]

    def set_tensor(self, index, data):
        self._tensor = data

    def invoke(self):
        return None

    def get_tensor(self, index):
        return np.array([[0.7, 0.2, 0.1]], dtype=np.float32)


class IdentityScaler:
    def transform(self, x):
        return np.asarray(x, dtype=float)


class FakeEncoder:
    classes_ = np.array(["ALTA", "BAJA", "MEDIA"])


def load_by_path(name, relative_path):
    path = os.path.join(ROOT, relative_path)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def fake_tflite(monkeypatch):
    """Registra un módulo tflite_runtime falso para que los scripts importen sin TensorFlow."""
    pkg = types.ModuleType("tflite_runtime")
    interp = types.ModuleType("tflite_runtime.interpreter")
    interp.Interpreter = FakeInterpreter
    pkg.interpreter = interp
    monkeypatch.setitem(sys.modules, "tflite_runtime", pkg)
    monkeypatch.setitem(sys.modules, "tflite_runtime.interpreter", interp)
    return interp


@pytest.fixture
def inferencia_modules(fake_tflite):
    return {
        "rpi": load_by_path("inferencia_rpi_under_test", "python/inference/inferencia_rpi.py"),
        "diag": load_by_path(
            "inferencia_diag_under_test", "python/inference/inferencia_con_diagnostico.py"
        ),
    }


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """Directorio de trabajo con modelo falso, pickles y dataset de simulación."""
    import pandas as pd

    (tmp_path / "enose_modelo.tflite").write_bytes(b"fake")
    for name, obj in (("scaler.pkl", IdentityScaler()), ("label_encoder.pkl", FakeEncoder())):
        with open(tmp_path / name, "wb") as fh:
            pickle.dump(obj, fh)
    with open(tmp_path / "perfil_referencia.pkl", "wb") as fh:
        pickle.dump(np.zeros(8), fh)

    sensores = ['MQ2', 'MQ4', 'MQ135', 'MQ3', 'MQ7', 'MQ9', 'temp', 'humedad']
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(40, 8)) * 3, columns=sensores)
    df["tipo_plastico"] = "PP"
    df["temp_max"] = 450.0
    df["clase_calidad"] = "ALTA"
    df.to_csv(tmp_path / "datos_etiquetados.csv", index=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path
