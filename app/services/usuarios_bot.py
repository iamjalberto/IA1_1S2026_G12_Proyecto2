import json
import os
import threading

# Ruta al archivo donde se persisten los usuarios registrados y sus chat_ids
_RUTA = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "usuarios_bot.json")
)
_lock = threading.Lock()


def _cargar() -> dict:
    """Lee el archivo JSON de usuarios. Retorna dict vacio si no existe o esta corrupto."""
    if not os.path.exists(_RUTA):
        return {}
    with open(_RUTA, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _guardar(datos: dict) -> None:
    """Persiste el diccionario de usuarios en el archivo JSON."""
    os.makedirs(os.path.dirname(_RUTA), exist_ok=True)
    with open(_RUTA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def obtener_chat_id(nombre: str) -> str | None:
    """Retorna el chat_id de un usuario registrado, o None si no existe."""
    with _lock:
        datos = _cargar()
        return datos.get(nombre.strip().lower())


def registrar(nombre: str, chat_id: str) -> None:
    """Guarda o actualiza el chat_id asociado a un nombre de usuario."""
    with _lock:
        datos = _cargar()
        datos[nombre.strip().lower()] = str(chat_id)
        _guardar(datos)


def eliminar(nombre: str) -> bool:
    """Elimina el registro de un usuario. Retorna True si existia, False si no."""
    with _lock:
        datos = _cargar()
        clave = nombre.strip().lower()
        if clave in datos:
            del datos[clave]
            _guardar(datos)
            return True
        return False
