import os
import requests
from dotenv import load_dotenv

load_dotenv()

# El token se lee del archivo .env, nunca se hardcodea en el codigo
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")


def _obtener_todos_los_chats() -> list:
    """
    Consulta getUpdates para recopilar todos los chat_id unicos que alguna vez
    enviaron un mensaje al bot. No requiere configuracion manual del chat_id.
    """
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            params={"limit": 100, "offset": -100},
            timeout=5,
        )
        if resp.status_code != 200:
            return []
        chats = {}
        for update in resp.json().get("result", []):
            # Soporta mensajes directos y mensajes de grupos/canales
            chat = (
                update.get("message", {}).get("chat")
                or update.get("channel_post", {}).get("chat")
            )
            if chat and chat.get("id"):
                cid = chat["id"]
                nombre = chat.get("first_name") or chat.get("title") or str(cid)
                chats[cid] = nombre
        return list(chats.keys())
    except Exception:
        return []


def enviar_mensaje(mensaje: str, chat_id: str) -> tuple:
    """
    Envia un mensaje de texto.
    - Si chat_id tiene valor, envia solo a ese chat.
    - Si chat_id esta vacio, hace broadcast a todos los chats que han
      interactuado con el bot.
    Retorna (exito: bool, descripcion: str).
    """
    if not TELEGRAM_TOKEN:
        return False, "TELEGRAM_TOKEN no esta configurado en el archivo .env"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    # Determinar la lista de destinatarios
    if chat_id and str(chat_id).strip():
        destinatarios = [str(chat_id).strip()]
    else:
        destinatarios = [str(c) for c in _obtener_todos_los_chats()]
        if not destinatarios:
            return False, "No hay chats registrados. Envia un mensaje al bot primero."

    exitos = 0
    errores = []
    for cid in destinatarios:
        try:
            resp = requests.post(
                url,
                json={"chat_id": cid, "text": mensaje, "parse_mode": "HTML"},
                timeout=10,
            )
            if resp.status_code == 200:
                exitos += 1
            else:
                errores.append(resp.json().get("description", "Error desconocido"))
        except requests.exceptions.RequestException as e:
            errores.append(str(e))

    if exitos == 0:
        return False, errores[0] if errores else "No se pudo enviar el mensaje"
    if errores:
        return True, f"Enviado a {exitos} chat(s), {len(errores)} fallo(s)"
    destinatarios_str = "todos los chats" if len(destinatarios) > 1 else "1 chat"
    return True, f"Mensaje enviado a {destinatarios_str} correctamente"
