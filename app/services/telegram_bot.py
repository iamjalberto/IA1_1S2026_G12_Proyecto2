import os
import requests
from dotenv import load_dotenv

load_dotenv()

# El token se lee del archivo .env, nunca se hardcodea en el codigo
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")


def enviar_mensaje(mensaje: str, chat_id: str) -> tuple:
    """
    Envia un mensaje de texto al chat de Telegram indicado.
    Retorna (exito: bool, descripcion: str).
    """
    if not TELEGRAM_TOKEN:
        return False, "TELEGRAM_TOKEN no esta configurado en el archivo .env"

    if not chat_id:
        return False, "El Chat ID no esta configurado en el panel de administracion"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "HTML"
    }

    try:
        respuesta = requests.post(url, json=payload, timeout=10)
        if respuesta.status_code == 200:
            return True, "Mensaje enviado correctamente a Telegram"
        else:
            datos = respuesta.json()
            return False, datos.get("description", "Error desconocido de la API de Telegram")
    except requests.exceptions.Timeout:
        return False, "Tiempo de espera agotado al contactar Telegram"
    except requests.exceptions.RequestException as e:
        return False, f"Error de conexion: {str(e)}"
