"""
Endpoints para capturar muestras del dataset directamente desde el navegador.

El flujo es:
  1. El admin abre el panel de captura en el navegador.
  2. El navegador accede a la camara local del usuario via getUserMedia.
  3. Cada 100ms el frontend captura un frame, lo codifica en JPEG base64 y lo
     envia a POST /admin/capturar_frame.
  4. El servidor decodifica la imagen, la procesa con MediaPipe y guarda los
     landmarks normalizados en el CSV del dataset.

Esto permite que la aplicacion corra en la nube sin necesitar camara en el servidor.
"""

import base64
import csv
import os
import re
import threading

import cv2
import mediapipe as mp
import numpy as np
from flask import Blueprint, jsonify, request

from app.routes.admin import requiere_login

captura_bp = Blueprint("captura", __name__)

# Inicializamos el detector una sola vez al importar el modulo.
# Crearlo por request tarda ~120ms de overhead, lo que haria imposible capturar a 10fps.
_mp_manos_mod = mp.solutions.hands
_mp_dibujo = mp.solutions.drawing_utils
_mp_estilos = mp.solutions.drawing_styles
_detector = _mp_manos_mod.Hands(
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# Lock para evitar escrituras concurrentes al CSV si llegan dos frames casi al mismo tiempo
_lock_csv = threading.Lock()

MUESTRAS_MAX = 500

RUTA_CSV = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "dataset.csv")
)


def _normalizar_landmarks(hand_landmarks) -> list:
    """Misma normalizacion que usa el script local de captura."""
    puntos = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
    puntos -= puntos[0]
    distancia_max = np.max(np.abs(puntos))
    if distancia_max > 0:
        puntos /= distancia_max
    return puntos.flatten().tolist()


def _contar_muestras_clase(clase: str) -> int:
    if not os.path.exists(RUTA_CSV):
        return 0
    count = 0
    with open(RUTA_CSV, "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row and row[0] == clase:
                count += 1
    return count


def _asegurar_csv() -> None:
    """Crea el CSV con su encabezado si todavia no existe."""
    os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)
    if not os.path.exists(RUTA_CSV):
        with open(RUTA_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            encabezado = ["clase"] + [
                f"{coord}{i}" for i in range(21) for coord in ("x", "y", "z")
            ]
            writer.writerow(encabezado)


@captura_bp.route("/admin/capturar_frame", methods=["POST"])
@requiere_login
def capturar_frame():
    """
    Recibe un frame JPEG en base64 del navegador, lo procesa con MediaPipe
    y si detecta una mano guarda los landmarks en el CSV.
    """
    data = request.get_json(silent=True) or {}
    clase = (data.get("clase") or "").strip()
    frame_b64 = data.get("frame") or ""

    if not clase or not frame_b64:
        return jsonify({"error": "Faltan datos"}), 400

    # Validar que el nombre de clase solo tenga caracteres seguros
    if not re.fullmatch(r"[a-zA-Z0-9_]+", clase):
        return jsonify({"error": "Nombre de clase invalido"}), 400

    count_actual = _contar_muestras_clase(clase)

    # No guardar mas si ya se alcanzo el maximo para esta clase
    if count_actual >= MUESTRAS_MAX:
        return jsonify({"detectado": False, "count": count_actual, "lleno": True})

    # Decodificar la imagen JPEG enviada como base64 desde el canvas del navegador
    try:
        img_bytes = base64.b64decode(frame_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        return jsonify({"detectado": False, "count": count_actual})

    if frame is None:
        return jsonify({"detectado": False, "count": count_actual})

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultado = _detector.process(rgb)

    # Dibujar landmarks sobre el frame para devolvérselo al navegador como preview
    frame_anotado = frame.copy()
    detectado = bool(resultado.multi_hand_landmarks)
    if detectado:
        for mano_lm in resultado.multi_hand_landmarks:
            _mp_dibujo.draw_landmarks(
                frame_anotado,
                mano_lm,
                _mp_manos_mod.HAND_CONNECTIONS,
                _mp_estilos.get_default_hand_landmarks_style(),
                _mp_estilos.get_default_hand_connections_style(),
            )

    # Codificar frame anotado como JPEG base64 para el preview del navegador
    ok, buf = cv2.imencode(".jpg", frame_anotado, [cv2.IMWRITE_JPEG_QUALITY, 72])
    frame_preview = base64.b64encode(buf.tobytes()).decode() if ok else ""

    if not detectado:
        return jsonify({"detectado": False, "count": count_actual, "preview": frame_preview})

    caracteristicas = _normalizar_landmarks(resultado.multi_hand_landmarks[0])

    _asegurar_csv()
    with _lock_csv:
        with open(RUTA_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([clase] + caracteristicas)

    count_actual += 1
    return jsonify({
        "detectado": True,
        "count": count_actual,
        "lleno": count_actual >= MUESTRAS_MAX,
        "preview": frame_preview,
    })


@captura_bp.route("/admin/progreso_captura", methods=["GET"])
@requiere_login
def progreso_captura():
    """Retorna cuantas muestras hay guardadas por cada clase configurada."""
    from app.config.settings import cargar_config

    config = cargar_config()
    clases = config.get("senas_disponibles", [])
    progreso = {clase: _contar_muestras_clase(clase) for clase in clases}
    return jsonify({"progreso": progreso, "max": MUESTRAS_MAX})


@captura_bp.route("/admin/borrar_muestras/<clase>", methods=["DELETE"])
@requiere_login
def borrar_muestras(clase):
    """
    Elimina del CSV todas las filas que pertenecen a la clase indicada.
    Equivale a la tecla R del script local de captura.
    """
    if not re.fullmatch(r"[a-zA-Z0-9_]+", clase):
        return jsonify({"error": "Nombre de clase invalido"}), 400

    if not os.path.exists(RUTA_CSV):
        return jsonify({"exito": True, "count": 0})

    with _lock_csv:
        with open(RUTA_CSV, "r") as f:
            filas = list(csv.reader(f))
        encabezado = filas[0] if filas else []
        resto = [fila for fila in filas[1:] if fila and fila[0] != clase]
        with open(RUTA_CSV, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(encabezado)
            writer.writerows(resto)

    return jsonify({"exito": True, "count": 0})
