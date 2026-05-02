import base64
import os
import threading
import time
import cv2
import numpy as np
import requests as http_requests
from flask import Blueprint, Response, jsonify, request
from app.services import detector, predictor
from app.services import telegram_bot, metricas, usuarios_bot
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

# Indice de camara activo; se puede cambiar en tiempo real desde /api/cambiar_camara
# En GCP no hay camara: el hilo simplemente no enviara frames
_camera_index = int(os.environ.get("CAMERA_INDEX", "0"))
_lock_camara = threading.Lock()


def _hilo_camara():
    """
    Corre en un hilo daemon independiente: lee la camara, procesa con MediaPipe
    y actualiza el estado global con el ultimo frame y prediccion.
    Si no hay camara disponible (entorno cloud), el hilo termina sin errores.
    """
    global _hilo_activo

    with _lock_camara:
        idx = _camera_index

    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        # Sin camara (servidor cloud) — no hay stream, pero el resto del sistema funciona
        print(f"[INFO] Camara {idx} no disponible. El stream de video estara inactivo.")
        _hilo_activo = False
        cap.release()
        return

    while _hilo_activo:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        # La normalizacion de quiralidad en detector.normalizar_landmarks() se encarga
        # de hacer el descriptor invariante a la orientacion. Procesamos el frame natural
        # y solo volteamos el anotado para que el usuario vea efecto espejo en el stream.
        frame_anotado, caracteristicas = detector.procesar_frame(frame)
        frame_anotado = cv2.flip(frame_anotado, 1)

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


def _reiniciar_camara(nuevo_indice: int):
    """Detiene el hilo actual y arranca uno nuevo con el indice de camara indicado."""
    global _hilo_activo, _camera_index
    # Señalar al hilo actual que debe terminar
    _hilo_activo = False
    time.sleep(0.3)  # darle tiempo al hilo de salir del loop
    with _lock_camara:
        _camera_index = nuevo_indice
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
    """Envia el mensaje acumulado al bot de Telegram con formato legible."""
    data = request.get_json() or {}
    mensaje = data.get("mensaje", "").strip()
    senas = data.get("senas", [])  # lista de {sena, confianza}

    if not mensaje:
        return jsonify({"exito": False, "mensaje": "El mensaje no puede estar vacio"}), 400

    config = cargar_config()

    if not config.get("telegram_activo", False):
        return jsonify({"exito": False, "mensaje": "El envio a Telegram esta desactivado en el panel admin"}), 400

    # Construir un mensaje HTML bien formateado para Telegram
    lineas = ["<b>HandTalk AI — Mensaje detectado</b>", ""]
    lineas.append(f"<b>Mensaje:</b> {mensaje}")
    if senas:
        lineas.append("")
        lineas.append("<b>Detalle por seña:</b>")
        for item in senas:
            sena = item.get("sena", "?")
            conf = float(item.get("confianza", 0))
            lineas.append(f"  • {sena} — {conf*100:.0f}% confianza")

    texto_final = "\n".join(lineas)

    nombre = data.get("nombre", "").strip().lower()
    if not nombre:
        return jsonify({"exito": False, "mensaje": "Debes registrarte en Telegram primero"}), 400

    chat_id = usuarios_bot.obtener_chat_id(nombre)
    if not chat_id:
        return jsonify({"exito": False, "mensaje": f"El usuario '{nombre}' no esta registrado. Escribe /registrar {nombre} al bot primero."}), 400

    exito, descripcion = telegram_bot.enviar_mensaje(texto_final, chat_id)

    return jsonify({"exito": exito, "mensaje": descripcion})


@main_bp.route("/api/historial")
def historial_publico():
    """Retorna los ultimos 30 registros del historial de detecciones para la vista usuario."""
    return jsonify({"historial": metricas.obtener_historial(30)})


@main_bp.route("/api/predecir_frame", methods=["POST"])
def predecir_frame():
    """
    Recibe un frame JPEG en base64 desde el navegador, lo procesa con MediaPipe
    y devuelve la prediccion + el frame anotado en base64.
    Usado en produccion donde el servidor no tiene camara fisica.
    """
    data = request.get_json(silent=True) or {}
    imagen_b64 = data.get("frame", "")
    if not imagen_b64:
        return jsonify({"exito": False, "mensaje": "Sin frame"}), 400

    # Decodificar base64 a numpy array
    try:
        header, encoded = imagen_b64.split(",", 1) if "," in imagen_b64 else ("", imagen_b64)
        img_bytes = base64.b64decode(encoded)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame_bgr is None:
            raise ValueError("Frame invalido")
    except Exception:
        return jsonify({"exito": False, "mensaje": "Frame invalido"}), 400

    frame_anotado, caracteristicas = detector.procesar_frame(frame_bgr)

    sena = None
    confianza = 0.0
    mano_detectada = caracteristicas is not None

    if mano_detectada and predictor.modelo_disponible():
        sena, confianza = predictor.predecir(caracteristicas)
        config = cargar_config()
        if confianza < config.get("umbral_confianza", 0.70):
            sena = None

        # Actualizar el estado global para que /api/estado siga funcionando
        with _estado_lock:
            _estado["sena_actual"] = sena
            _estado["confianza_actual"] = confianza
            _estado["mano_detectada"] = mano_detectada

    # Codificar frame anotado en JPEG base64 para enviarlo al navegador
    _, buf = cv2.imencode(".jpg", frame_anotado, [cv2.IMWRITE_JPEG_QUALITY, 80])
    frame_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

    return jsonify({
        "exito": True,
        "sena": sena,
        "confianza": round(confianza, 4),
        "mano_detectada": mano_detectada,
        "frame_anotado": frame_b64,
    })


@main_bp.route("/api/bot_username")
def bot_username_publico():
    """Retorna el username del bot de Telegram. Endpoint publico para el modulo de usuario."""
    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token or token == "tu_token_aqui":
        return jsonify({"configurado": False, "username": None})
    try:
        resp = http_requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=5
        )
        if resp.status_code == 200:
            datos = resp.json().get("result", {})
            return jsonify({"configurado": True, "username": datos.get("username")})
    except Exception:
        pass
    return jsonify({"configurado": False, "username": None})


@main_bp.route("/api/registrar_usuario", methods=["POST"])
def registrar_usuario():
    """
    Busca en los ultimos mensajes del bot el comando '/registrar <nombre>'
    enviado por el usuario y guarda su chat_id en usuarios_bot.json.
    """
    data = request.get_json() or {}
    nombre = data.get("nombre", "").strip().lower()
    if not nombre:
        return jsonify({"exito": False, "mensaje": "Nombre vacio"}), 400

    token = os.environ.get("TELEGRAM_TOKEN", "")
    if not token or token == "tu_token_aqui":
        return jsonify({"exito": False, "mensaje": "Token de Telegram no configurado"})

    try:
        resp = http_requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={"limit": 100, "offset": -100},
            timeout=8,
        )
        if resp.status_code != 200:
            return jsonify({"exito": False, "mensaje": "Error al consultar Telegram"})

        updates = resp.json().get("result", [])
        # Buscar el comando /registrar <nombre> en los mensajes mas recientes
        for update in reversed(updates):
            msg = update.get("message", {})
            texto = (msg.get("text") or "").strip().lower()
            # Aceptar tanto '/registrar nombre' como '/registrar@botname nombre'
            partes = texto.split()
            if len(partes) >= 2 and partes[0].startswith("/registrar") and partes[1] == nombre:
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id:
                    usuarios_bot.registrar(nombre, chat_id)
                    return jsonify({"exito": True, "chat_id": chat_id})

        return jsonify({
            "exito": False,
            "mensaje": f"No se encontro el comando /registrar {nombre}. Asegurate de haberlo enviado al bot."
        })
    except Exception as e:
        return jsonify({"exito": False, "mensaje": f"Error: {str(e)}"})


@main_bp.route("/api/desconectar_usuario", methods=["POST"])
def desconectar_usuario():
    """Elimina el registro de un usuario para que deje de recibir mensajes."""
    data = request.get_json() or {}
    nombre = data.get("nombre", "").strip().lower()
    if not nombre:
        return jsonify({"exito": False, "mensaje": "Nombre vacio"}), 400
    eliminado = usuarios_bot.eliminar(nombre)
    if eliminado:
        return jsonify({"exito": True, "mensaje": f"Usuario '{nombre}' desconectado"})
    return jsonify({"exito": False, "mensaje": f"El usuario '{nombre}' no estaba registrado"})


@main_bp.route("/api/salud")
def salud():
    """Health check para que Docker y el frontend sepan si el backend esta listo."""
    return jsonify({"estado": "ok", "modelo_listo": predictor.modelo_disponible()})


@main_bp.route("/api/camaras")
def listar_camaras():
    """Enumera los indices de camara disponibles en el sistema (0..4)."""
    disponibles = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            disponibles.append({"indice": i, "nombre": f"Camara {i}"})
            cap.release()
        else:
            cap.release()
    with _lock_camara:
        actual = _camera_index
    return jsonify({"camaras": disponibles, "actual": actual})


@main_bp.route("/api/cambiar_camara", methods=["POST"])
def cambiar_camara():
    """Cambia la camara activa y reinicia el hilo de captura."""
    data = request.get_json() or {}
    indice = data.get("indice")
    if indice is None or not isinstance(indice, int):
        return jsonify({"exito": False, "mensaje": "Indice invalido"}), 400
    # Reiniciar en hilo separado para no bloquear la respuesta HTTP
    t = threading.Thread(target=_reiniciar_camara, args=(indice,), daemon=True)
    t.start()
    return jsonify({"exito": True, "mensaje": f"Camara cambiada a indice {indice}"})
