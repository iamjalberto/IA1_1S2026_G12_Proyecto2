from app import crear_app
from app.routes.main import iniciar_camara

app = crear_app()

if __name__ == "__main__":
    # Iniciar el hilo de camara antes de arrancar Flask
    iniciar_camara()
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
