import csv
import os
import pickle
import threading
from functools import wraps

import numpy as np
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


# --- Entrenamiento del modelo desde el panel ---

# Estado global del proceso de entrenamiento para poder consultarlo con polling
_estado_entrenamiento = {
    "en_proceso": False,
    "exito": None,       # True/False cuando termina, None mientras corre
    "mensaje": "",
    "paso": "",          # descripcion del paso actual
    "progreso": 0.0,     # 0.0 a 1.0
}
_lock_entrenamiento = threading.Lock()


def _actualizar_paso(paso: str, progreso: float) -> None:
    """Actualiza el estado del entrenamiento de forma thread-safe."""
    with _lock_entrenamiento:
        _estado_entrenamiento["paso"] = paso
        _estado_entrenamiento["progreso"] = progreso


def _ejecutar_entrenamiento():
    """
    Corre el entrenamiento en un hilo separado para no bloquear Flask.
    Prueba KNN, SVM, Random Forest y Regresion Logistica, guarda el mejor.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.model_selection import train_test_split
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.svm import SVC

    global _estado_entrenamiento

    ruta_csv = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "dataset.csv")
    )
    ruta_modelo_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "modelo")
    )

    try:
        if not os.path.exists(ruta_csv):
            raise FileNotFoundError("No se encontro dataset.csv. Captura muestras primero.")

        _actualizar_paso("Cargando dataset...", 0.05)
        X, y = [], []
        with open(ruta_csv, "r") as f:
            reader = csv.reader(f)
            next(reader)
            for fila in reader:
                if len(fila) >= 2:
                    y.append(fila[0])
                    X.append([float(v) for v in fila[1:]])

        X, y = np.array(X), np.array(y)
        clases_unicas = sorted(set(y))

        if len(X) < 10:
            raise ValueError(f"Se necesitan al menos 10 muestras (hay {len(X)}).")
        if len(clases_unicas) < 2:
            raise ValueError("Se necesitan al menos 2 clases distintas para entrenar.")

        _actualizar_paso(f"Dataset listo: {len(X)} muestras, {len(clases_unicas)} clases. Preparando datos...", 0.10)
        encoder = LabelEncoder()
        y_enc = encoder.fit_transform(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
        )

        candidatos = {
            "KNN (k=5)": KNeighborsClassifier(n_neighbors=5),
            "SVM RBF": SVC(kernel="rbf", probability=True, C=10, random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=150, random_state=42),
            "Regresion Logistica": LogisticRegression(
                max_iter=1000, C=1.0, random_state=42, multi_class="auto"
            ),
        }

        # Cada modelo ocupa un tramo de 0.15 a 0.80 del progreso total
        resultados = {}
        n_modelos = len(candidatos)
        for i, (nombre, modelo) in enumerate(candidatos.items()):
            progreso_inicio = 0.15 + i * (0.65 / n_modelos)
            _actualizar_paso(f"Entrenando {nombre}... ({i+1}/{n_modelos})", progreso_inicio)
            modelo.fit(X_train, y_train)
            preds = modelo.predict(X_test)
            exactitud = accuracy_score(y_test, preds)
            reporte = classification_report(
                y_test, preds, target_names=encoder.classes_, zero_division=0
            )
            resultados[nombre] = (exactitud, modelo, reporte)
            _actualizar_paso(
                f"{nombre} listo — exactitud: {exactitud:.1%}",
                progreso_inicio + (0.65 / n_modelos) * 0.9,
            )

        mejor_nombre = max(resultados, key=lambda n: resultados[n][0])
        mejor_exactitud, mejor_modelo, mejor_reporte = resultados[mejor_nombre]

        _actualizar_paso(f"Guardando modelo ({mejor_nombre})...", 0.88)
        os.makedirs(ruta_modelo_dir, exist_ok=True)
        with open(os.path.join(ruta_modelo_dir, "model.pkl"), "wb") as f:
            pickle.dump(mejor_modelo, f)
        with open(os.path.join(ruta_modelo_dir, "label_encoder.pkl"), "wb") as f:
            pickle.dump(encoder, f)

        preds_finales = mejor_modelo.predict(X_test)
        matriz = confusion_matrix(y_test, preds_finales)

        resumen_algoritmos = "\n".join(
            f"  {n}: {resultados[n][0]:.4f}" for n in resultados
        )
        reporte_completo = (
            f"Reporte de Metricas - HandTalk AI\n{'='*50}\n\n"
            f"Mejor modelo: {mejor_nombre}\n"
            f"Exactitud: {mejor_exactitud:.4f} ({mejor_exactitud:.1%})\n"
            f"Muestras totales: {len(X)}\n"
            f"Clases: {clases_unicas}\n\n"
            f"Resultados por algoritmo:\n{resumen_algoritmos}\n\n"
            f"Reporte detallado (mejor modelo):\n{mejor_reporte}\n"
            f"Matriz de confusion:\n{matriz}\n"
        )

        with open(os.path.join(ruta_modelo_dir, "reporte_metricas.txt"), "w", encoding="utf-8") as f:
            f.write(reporte_completo)

        # Recargar el modelo en el predictor activo sin necesidad de reiniciar Flask
        _actualizar_paso("Recargando modelo en el servidor...", 0.97)
        predictor.recargar_modelo()

        with _lock_entrenamiento:
            _estado_entrenamiento["en_proceso"] = False
            _estado_entrenamiento["exito"] = True
            _estado_entrenamiento["paso"] = "Completado"
            _estado_entrenamiento["progreso"] = 1.0
            _estado_entrenamiento["mensaje"] = (
                f"Entrenamiento completado. Mejor modelo: {mejor_nombre} "
                f"({mejor_exactitud:.1%} exactitud) con {len(X)} muestras."
            )

    except Exception as e:
        with _lock_entrenamiento:
            _estado_entrenamiento["en_proceso"] = False
            _estado_entrenamiento["exito"] = False
            _estado_entrenamiento["paso"] = "Error"
            _estado_entrenamiento["progreso"] = 0.0
            _estado_entrenamiento["mensaje"] = f"Error durante el entrenamiento: {str(e)}"


@admin_bp.route("/entrenar", methods=["POST"])
@requiere_login
def entrenar():
    """Lanza el entrenamiento del modelo en un hilo de fondo."""
    with _lock_entrenamiento:
        if _estado_entrenamiento["en_proceso"]:
            return jsonify({"iniciado": False, "mensaje": "Ya hay un entrenamiento en curso."})
        _estado_entrenamiento["en_proceso"] = True
        _estado_entrenamiento["exito"] = None
        _estado_entrenamiento["mensaje"] = "Entrenando..."
        _estado_entrenamiento["paso"] = "Iniciando..."
        _estado_entrenamiento["progreso"] = 0.0

    hilo = threading.Thread(target=_ejecutar_entrenamiento, daemon=True)
    hilo.start()
    return jsonify({"iniciado": True, "mensaje": "Entrenamiento iniciado."})


@admin_bp.route("/estado_entrenamiento", methods=["GET"])
@requiere_login
def estado_entrenamiento():
    """Permite al frontend consultar si el entrenamiento termino y con que resultado."""
    with _lock_entrenamiento:
        estado = dict(_estado_entrenamiento)
    return jsonify(estado)


# --- CRUD de señas disponibles ---

@admin_bp.route("/senas", methods=["GET"])
@requiere_login
def listar_senas():
    """Retorna la lista actual de senas disponibles con sus descripciones."""
    config = cargar_config()
    descripciones = config.get("senas_descripciones", {})
    return jsonify({"senas": config.get("senas_disponibles", []), "descripciones": descripciones})


@admin_bp.route("/senas", methods=["POST"])
@requiere_login
def agregar_sena():
    """Agrega una nueva sena a la lista de senas disponibles."""
    data = request.get_json() or {}
    nueva = data.get("sena", "").strip().lower()
    descripcion = data.get("descripcion", "").strip()[:300]  # max 300 chars

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
    if descripcion:
        descripciones = config.get("senas_descripciones", {})
        descripciones[nueva] = descripcion
        config["senas_descripciones"] = descripciones
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
