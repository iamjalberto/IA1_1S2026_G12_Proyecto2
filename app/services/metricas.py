import json
import os
from datetime import datetime

RUTA_LOG = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "historial.json")
RUTA_LOG = os.path.normpath(RUTA_LOG)


def _cargar_historial() -> list:
    os.makedirs(os.path.dirname(RUTA_LOG), exist_ok=True)
    if not os.path.exists(RUTA_LOG):
        return []
    with open(RUTA_LOG, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_historial(historial: list) -> None:
    with open(RUTA_LOG, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)


def registrar(sena: str, confianza: float, enviado_telegram: bool = False, max_registros: int = 200) -> None:
    """Agrega una deteccion al historial y recorta si supera el maximo."""
    historial = _cargar_historial()
    historial.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sena": sena,
        "confianza": round(confianza, 4),
        "enviado_telegram": enviado_telegram
    })
    # Mantener solo los registros mas recientes para no crecer indefinidamente
    if len(historial) > max_registros:
        historial = historial[-max_registros:]
    _guardar_historial(historial)


def obtener_historial(limite: int = 50) -> list:
    """Retorna los ultimos N registros ordenados del mas reciente al mas antiguo."""
    historial = _cargar_historial()
    return historial[-limite:][::-1]


def obtener_resumen() -> dict:
    """Calcula estadisticas agregadas del historial de detecciones."""
    historial = _cargar_historial()

    if not historial:
        return {
            "total_detecciones": 0,
            "total_enviados_telegram": 0,
            "confianza_promedio": 0.0,
            "por_clase": {}
        }

    total_enviados = sum(1 for r in historial if r.get("enviado_telegram"))
    confianza_total = sum(r["confianza"] for r in historial)

    por_clase = {}
    for registro in historial:
        sena = registro["sena"]
        if sena not in por_clase:
            por_clase[sena] = {"total": 0, "suma_confianza": 0.0}
        por_clase[sena]["total"] += 1
        por_clase[sena]["suma_confianza"] += registro["confianza"]

    # Calcular promedios por clase
    for sena in por_clase:
        total = por_clase[sena]["total"]
        por_clase[sena]["confianza_promedio"] = round(
            por_clase[sena]["suma_confianza"] / total, 4
        )
        del por_clase[sena]["suma_confianza"]

    return {
        "total_detecciones": len(historial),
        "total_enviados_telegram": total_enviados,
        "confianza_promedio": round(confianza_total / len(historial), 4),
        "por_clase": por_clase
    }


def limpiar_historial() -> None:
    """Borra todos los registros del historial."""
    _guardar_historial([])
