import os
from functools import wraps
from flask import Blueprint, request, jsonify, session
from app.config.settings import cargar_config, guardar_config
from app.services import metricas, predictor

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Credenciales leidas desde el entorno (definidas en .env)
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin123")


def requiere_login(f):
    """Decorador que protege un endpoint: retorna 401 si no hay sesion activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_autenticado"):
            return jsonify({"error": "No autorizado", "autenticado": False}), 401
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/login", methods=["POST"])
def login():
    """Valida usuario y contrasena, inicia sesion si son correctos."""
    data = request.get_json() or {}
    usuario = data.get("usuario", "")
    contrasena = data.get("contrasena", "")
    if usuario == ADMIN_USER and contrasena == ADMIN_PASS:
        session["admin_autenticado"] = True
        return jsonify({"exito": True, "mensaje": "Sesion iniciada"})
    return jsonify({"exito": False, "mensaje": "Credenciales incorrectas"}), 401


@admin_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesion del administrador."""
    session.clear()
    return jsonify({"exito": True, "mensaje": "Sesion cerrada"})


@admin_bp.route("/verificar")
def verificar():
    """Permite al frontend saber si hay sesion activa sin llamar un endpoint protegido."""
    return jsonify({"autenticado": bool(session.get("admin_autenticado"))})


@admin_bp.route("/")
@requiere_login
def index():
    """Resumen general del panel admin en formato JSON."""
    config = cargar_config()
    resumen = metricas.obtener_resumen()
    modelo_listo = predictor.modelo_disponible()
    return jsonify({
        "config": config,
        "resumen": resumen,
        "modelo_listo": modelo_listo
    })


@admin_bp.route("/config", methods=["POST"])
@requiere_login
def actualizar_config():
    """Actualiza los campos de configuracion recibidos desde el panel admin."""
    data = request.get_json()
    config = cargar_config()

    # Solo permitimos modificar estos campos para evitar inyeccion de campos no esperados
    campos_permitidos = [
        "umbral_confianza",
        "formato_mensaje",
        "telegram_activo",
        "telegram_chat_id",
        "historial_habilitado"
    ]

    for campo in campos_permitidos:
        if campo in data:
            config[campo] = data[campo]

    guardar_config(config)
    return jsonify({"exito": True, "mensaje": "Configuracion guardada correctamente"})


@admin_bp.route("/metricas")
@requiere_login
def ver_metricas():
    return jsonify(metricas.obtener_resumen())


@admin_bp.route("/historial")
@requiere_login
def ver_historial():
    limite = request.args.get("limite", 50, type=int)
    return jsonify(metricas.obtener_historial(limite))


@admin_bp.route("/limpiar_historial", methods=["POST"])
@requiere_login
def limpiar():
    metricas.limpiar_historial()
    return jsonify({"exito": True, "mensaje": "Historial limpiado"})


@admin_bp.route("/modelo_info")
@requiere_login
def modelo_info():
    """Retorna el reporte de metricas del modelo entrenado si existe."""
    ruta_reporte = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "modelo", "reporte_metricas.txt")
    )

    if not predictor.modelo_disponible():
        return jsonify({"disponible": False, "reporte": None})

    reporte_texto = None
    if os.path.exists(ruta_reporte):
        with open(ruta_reporte, "r", encoding="utf-8") as f:
            reporte_texto = f.read()

    return jsonify({"disponible": True, "reporte": reporte_texto})


# --- CRUD de señas disponibles ---

@admin_bp.route("/senas", methods=["GET"])
@requiere_login
def listar_senas():
    """Retorna la lista actual de senas disponibles en el sistema."""
    config = cargar_config()
    return jsonify({"senas": config.get("senas_disponibles", [])})


@admin_bp.route("/senas", methods=["POST"])
@requiere_login
def agregar_sena():
    """Agrega una nueva sena a la lista de senas disponibles."""
    data = request.get_json() or {}
    nueva = data.get("sena", "").strip().lower()

    if not nueva:
        return jsonify({"exito": False, "mensaje": "El nombre de la sena no puede estar vacio"}), 400

    # Solo letras, numeros y guion bajo para evitar caracteres raros
    if not all(c.isalnum() or c == "_" for c in nueva):
        return jsonify({"exito": False, "mensaje": "El nombre solo puede tener letras, numeros y guion bajo"}), 400

    config = cargar_config()
    senas = config.get("senas_disponibles", [])

    if nueva in senas:
        return jsonify({"exito": False, "mensaje": f"La sena '{nueva}' ya existe"}), 409

    senas.append(nueva)
    config["senas_disponibles"] = senas
    guardar_config(config)
    return jsonify({"exito": True, "mensaje": f"Sena '{nueva}' agregada", "senas": senas})


@admin_bp.route("/senas/<nombre>", methods=["DELETE"])
@requiere_login
def eliminar_sena(nombre):
    """Elimina una sena de la lista de senas disponibles."""
    config = cargar_config()
    senas = config.get("senas_disponibles", [])

    if nombre not in senas:
        return jsonify({"exito": False, "mensaje": f"La sena '{nombre}' no existe"}), 404

    senas.remove(nombre)
    config["senas_disponibles"] = senas
    guardar_config(config)
    return jsonify({"exito": True, "mensaje": f"Sena '{nombre}' eliminada", "senas": senas})
