from app import crear_app
from app.routes.main import iniciar_camara
import os

app = crear_app()

if __name__ == "__main__":
    # En entornos cloud/Docker se puede deshabilitar el hilo de camara del servidor.
    # La captura de video para el panel admin se hace desde el navegador via getUserMedia.
    if os.environ.get("DISABLE_CAMERA", "").lower() not in ("1", "true", "yes"):
        iniciar_camara()
    else:
        print("[INFO] Hilo de camara del servidor deshabilitado (DISABLE_CAMERA=true).")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
