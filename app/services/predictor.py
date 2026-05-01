import os
import pickle
import numpy as np

MODELO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "modelo")
MODELO_DIR = os.path.normpath(MODELO_DIR)

# Cargamos en memoria la primera vez que se necesitan para no leer disco en cada prediccion
_modelo = None
_encoder = None


def _cargar_modelos() -> bool:
    """Carga model.pkl y label_encoder.pkl en memoria. Retorna True si tuvo exito."""
    global _modelo, _encoder

    ruta_modelo = os.path.join(MODELO_DIR, "model.pkl")
    ruta_encoder = os.path.join(MODELO_DIR, "label_encoder.pkl")

    if not os.path.exists(ruta_modelo) or not os.path.exists(ruta_encoder):
        return False

    with open(ruta_modelo, "rb") as f:
        _modelo = pickle.load(f)

    with open(ruta_encoder, "rb") as f:
        _encoder = pickle.load(f)

    return True


def modelo_disponible() -> bool:
    """Verifica si el archivo model.pkl existe en disco."""
    return os.path.exists(os.path.join(MODELO_DIR, "model.pkl"))


def predecir(caracteristicas: list) -> tuple:
    """
    Recibe los 63 landmarks normalizados y retorna (etiqueta, confianza).
    Si el modelo no esta cargado, intenta cargarlo.
    Retorna (None, 0.0) si no hay modelo disponible.
    """
    global _modelo, _encoder

    if _modelo is None:
        if not _cargar_modelos():
            return None, 0.0

    X = np.array([caracteristicas])

    # Usamos probabilidades si el modelo las soporta (SVM con probability=True, RandomForest, etc.)
    if hasattr(_modelo, "predict_proba"):
        probabilidades = _modelo.predict_proba(X)[0]
        idx = int(np.argmax(probabilidades))
        confianza = float(probabilidades[idx])
    else:
        idx = int(_modelo.predict(X)[0])
        confianza = 1.0

    etiqueta = _encoder.inverse_transform([idx])[0]
    return etiqueta, confianza


def recargar_modelo() -> bool:
    """
    Fuerza la recarga del modelo desde disco.
    Se llama despues de un reentrenamiento para que el predictor use el nuevo modelo
    sin necesidad de reiniciar Flask.
    """
    global _modelo, _encoder
    _modelo = None
    _encoder = None
    return _cargar_modelos()
