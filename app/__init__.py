from flask import Flask
from flask_cors import CORS
from app.routes.main import main_bp
from app.routes.admin import admin_bp


def crear_app() -> Flask:
    """Factory de la aplicacion Flask. Expone solo API REST, sin templates."""
    app = Flask(__name__)

    # Habilitamos CORS para que el frontend Vite pueda hacer fetch sin restricciones
    CORS(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    return app
