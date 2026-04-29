from flask import Blueprint, request, jsonify
from app.config.settings import cargar_config, guardar_config
from app.services import metricas, predictor
import os

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
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
def ver_metricas():
    return jsonify(metricas.obtener_resumen())


@admin_bp.route("/historial")
def ver_historial():
    limite = request.args.get("limite", 50, type=int)
    return jsonify(metricas.obtener_historial(limite))


@admin_bp.route("/limpiar_historial", methods=["POST"])
def limpiar():
    metricas.limpiar_historial()
    return jsonify({"exito": True, "mensaje": "Historial limpiado"})


@admin_bp.route("/modelo_info")
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
