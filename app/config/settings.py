import json
import os

# Ruta al archivo de configuracion del sistema
RUTA_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.json")
RUTA_CONFIG = os.path.normpath(RUTA_CONFIG)

# Valores por defecto, se usan si no existe config.json
CONFIG_DEFAULT = {
    "umbral_confianza": 0.70,
    "senas_disponibles": [
        "excelente", "hola", "igual", "mucho", "no",
        "nombre", "si", "te_amo", "tu", "yo"
    ],
    "senas_descripciones": {},
    "formato_mensaje": "Deteccion HandTalk AI:\nSena: {sena}\nConfianza: {confianza:.0%}",
    "telegram_activo": False,
    "telegram_chat_id": "",
    "historial_habilitado": True,
    "max_historial": 200
}


def cargar_config() -> dict:
    """Carga la configuracion desde config.json, o retorna los valores por defecto."""
    os.makedirs(os.path.dirname(RUTA_CONFIG), exist_ok=True)

    if not os.path.exists(RUTA_CONFIG):
        guardar_config(CONFIG_DEFAULT)
        return CONFIG_DEFAULT.copy()

    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Si falta algun campo nuevo, completarlo con el default
    for clave, valor in CONFIG_DEFAULT.items():
        if clave not in config:
            config[clave] = valor

    return config


def guardar_config(config: dict) -> None:
    """Persiste la configuracion en config.json."""
    os.makedirs(os.path.dirname(RUTA_CONFIG), exist_ok=True)
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
