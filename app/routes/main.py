import threading
import time
import cv2
from flask import Blueprint, Response, jsonify, request
from app.services import detector, predictor
from app.services import telegram_bot, metricas
from app.config.settings import cargar_config

main_bp = Blueprint("main", __name__)

# Estado compartido entre el hilo de camara y las rutas Flask
_estado = {
    "frame_jpeg": None,
    "sena_actual": None,
    "confianza_actual": 0.0,
    "mano_detectada": False,
}
_estado_lock = threading.Lock()
_hilo_activo = False


def _hilo_camara():
    """
    Corre en un hilo daemon independiente: lee la camara, procesa con MediaPipe
    y actualiza el estado global con el ultimo frame y prediccion.
    """
    global _hilo_activo

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while _hilo_activo:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        # Espejamos el frame para que se vea como un espejo (mas natural para el usuario)
        frame = cv2.flip(frame, 1)
        frame_anotado, caracteristicas = detector.procesar_frame(frame)

        config = cargar_config()
        umbral = config.get("umbral_confianza", 0.70)

        sena = None
        confianza = 0.0
        mano_detectada = caracteristicas is not None

        if caracteristicas and predictor.modelo_disponible():
            sena_pred, conf_pred = predictor.predecir(caracteristicas)
            if conf_pred >= umbral:
                sena = sena_pred
                confianza = conf_pred

        # Superponer la prediccion sobre el frame
        h, w = frame_anotado.shape[:2]
        cv2.rectangle(frame_anotado, (0, h - 70), (w, h), (20, 20, 20), -1)

        if sena:
            cv2.putText(frame_anotado, sena, (10, h - 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 230, 80), 3)
            cv2.putText(frame_anotado, f"Conf: {confianza:.0%}", (10, h - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 180, 180), 2)
        elif mano_detectada:
            cv2.putText(frame_anotado, "Analizando...", (10, h - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 200, 220), 2)
        else:
            cv2.putText(frame_anotado, "Sin mano detectada", (10, h - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (100, 100, 100), 2)

        # Codificar como JPEG para el stream
        ok, buffer = cv2.imencode(".jpg", frame_anotado, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not ok:
            continue

        with _estado_lock:
            _estado["frame_jpeg"] = buffer.tobytes()
            _estado["sena_actual"] = sena
            _estado["confianza_actual"] = confianza
            _estado["mano_detectada"] = mano_detectada

        time.sleep(0.033)  # ~30fps

    cap.release()


def iniciar_camara():
    """Inicia el hilo de captura. Se llama una sola vez al arrancar la app."""
    global _hilo_activo
    _hilo_activo = True
    hilo = threading.Thread(target=_hilo_camara, daemon=True)
    hilo.start()


def _stream_generator():
    """Generator que produce cada frame JPEG como parte del stream MJPEG."""
    ultimo_frame = None
    while True:
        with _estado_lock:
            frame = _estado.get("frame_jpeg")

        if frame and frame is not ultimo_frame:
            ultimo_frame = frame
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )

        time.sleep(0.033)


@main_bp.route("/video_feed")
def video_feed():
    """Stream MJPEG de la camara con anotaciones en tiempo real."""
    return Response(_stream_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")


@main_bp.route("/api/estado")
def estado():
    """Retorna el estado actual de la camara: ultima seña detectada y confianza."""
    with _estado_lock:
        return jsonify({
            "sena_actual": _estado["sena_actual"],
            "confianza_actual": _estado["confianza_actual"],
            "mano_detectada": _estado["mano_detectada"],
            "modelo_listo": predictor.modelo_disponible()
        })


@main_bp.route("/api/senas")
def senas_disponibles():
    """Lista las senas que el sistema es capaz de reconocer."""
    config = cargar_config()
    return jsonify({"senas": config.get("senas_disponibles", [])})


@main_bp.route("/api/registrar_sena", methods=["POST"])
def registrar_sena():
    """
    El frontend llama a este endpoint cuando el usuario captura una sena
    para que quede registrada en el historial de metricas.
    """
    data = request.get_json() or {}
    sena = data.get("sena", "").strip()
    confianza = float(data.get("confianza", 0.0))

    if not sena:
        return jsonify({"exito": False, "mensaje": "Sena vacia"}), 400

    config = cargar_config()
    if config.get("historial_habilitado", True):
        metricas.registrar(sena, confianza)

    return jsonify({"exito": True})


@main_bp.route("/api/enviar_telegram", methods=["POST"])
def enviar_telegram():
    """Envia el mensaje acumulado al bot de Telegram."""
    data = request.get_json() or {}
    mensaje = data.get("mensaje", "").strip()

    if not mensaje:
        return jsonify({"exito": False, "mensaje": "El mensaje no puede estar vacio"}), 400

    config = cargar_config()

    if not config.get("telegram_activo", False):
        return jsonify({"exito": False, "mensaje": "El envio a Telegram esta desactivado en el panel admin"}), 400

    chat_id = config.get("telegram_chat_id", "")
    exito, descripcion = telegram_bot.enviar_mensaje(mensaje, chat_id)

    return jsonify({"exito": exito, "mensaje": descripcion})


@main_bp.route("/api/salud")
def salud():
    """Health check para que Docker y el frontend sepan si el backend esta listo."""
    return jsonify({"estado": "ok", "modelo_listo": predictor.modelo_disponible()})
