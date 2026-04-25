"""
Script de entrenamiento del modelo de clasificacion de senas.
Prueba cuatro algoritmos (KNN, SVM, Random Forest, Regresion Logistica),
selecciona el de mejor exactitud y lo guarda como modelo/model.pkl.
Tambien guarda el LabelEncoder y un reporte detallado de metricas.
"""

import os
import csv
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

RUTA_CSV = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "dataset", "dataset.csv")
)
RUTA_MODELO_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "modelo")
)


def cargar_dataset(ruta_csv: str):
    """Lee dataset.csv y retorna X (features) e y (etiquetas) como arrays numpy."""
    X, y = [], []
    with open(ruta_csv, "r") as f:
        lector = csv.reader(f)
        next(lector)  # saltar encabezado
        for fila in lector:
            if len(fila) < 2:
                continue
            y.append(fila[0])
            X.append([float(v) for v in fila[1:]])
    return np.array(X), np.array(y)


def entrenar_y_evaluar(nombre: str, modelo, X_train, X_test, y_train, y_test, encoder):
    """Entrena un modelo, lo evalua y retorna (exactitud, modelo_entrenado, reporte_str)."""
    modelo.fit(X_train, y_train)
    predicciones = modelo.predict(X_test)
    exactitud = accuracy_score(y_test, predicciones)

    reporte = classification_report(
        y_test, predicciones,
        target_names=encoder.classes_,
        zero_division=0
    )

    print(f"\n{'='*50}")
    print(f"  {nombre}")
    print(f"  Exactitud: {exactitud:.4f} ({exactitud:.1%})")
    print(reporte)

    return exactitud, modelo, reporte


def main():
    print("=== Entrenamiento del Modelo - HandTalk AI ===\n")

    if not os.path.exists(RUTA_CSV):
        print(f"ERROR: No se encontro el dataset en {RUTA_CSV}")
        print("Primero ejecuta: python scripts/capturar_dataset.py")
        return

    X, y = cargar_dataset(RUTA_CSV)
    print(f"Dataset cargado: {len(X)} muestras, {len(set(y))} clases")
    print(f"Clases: {sorted(set(y))}")

    if len(X) < 10:
        print("ERROR: Se necesitan al menos 10 muestras para entrenar.")
        return

    # Codificar etiquetas de texto a numeros
    encoder = LabelEncoder()
    y_enc = encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
    )
    print(f"Entrenamiento: {len(X_train)} muestras, Prueba: {len(X_test)} muestras\n")

    # Los cuatro algoritmos sugeridos por el enunciado
    candidatos = {
        "KNN (k=5)": KNeighborsClassifier(n_neighbors=5),
        "SVM RBF": SVC(kernel="rbf", probability=True, C=10, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=150, random_state=42),
        "Regresion Logistica": LogisticRegression(
            max_iter=1000, C=1.0, random_state=42, multi_class="auto"
        ),
    }

    resultados = {}
    for nombre, modelo in candidatos.items():
        exactitud, modelo_entrenado, reporte = entrenar_y_evaluar(
            nombre, modelo, X_train, X_test, y_train, y_test, encoder
        )
        resultados[nombre] = (exactitud, modelo_entrenado, reporte)

    # Elegir el modelo de mejor exactitud
    mejor_nombre = max(resultados, key=lambda n: resultados[n][0])
    mejor_exactitud, mejor_modelo, mejor_reporte = resultados[mejor_nombre]

    print(f"\n{'='*50}")
    print(f"  Mejor modelo: {mejor_nombre}")
    print(f"  Exactitud final: {mejor_exactitud:.4f} ({mejor_exactitud:.1%})")

    os.makedirs(RUTA_MODELO_DIR, exist_ok=True)

    # Guardar modelo y encoder
    with open(os.path.join(RUTA_MODELO_DIR, "model.pkl"), "wb") as f:
        pickle.dump(mejor_modelo, f)

    with open(os.path.join(RUTA_MODELO_DIR, "label_encoder.pkl"), "wb") as f:
        pickle.dump(encoder, f)

    # Matriz de confusion del mejor modelo
    predicciones_finales = mejor_modelo.predict(X_test)
    matriz = confusion_matrix(y_test, predicciones_finales)

    # Reporte de metricas completo para la documentacion
    with open(os.path.join(RUTA_MODELO_DIR, "reporte_metricas.txt"), "w", encoding="utf-8") as f:
        f.write("Reporte de Metricas - HandTalk AI\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Mejor modelo seleccionado: {mejor_nombre}\n")
        f.write(f"Exactitud en conjunto de prueba: {mejor_exactitud:.4f}\n\n")
        f.write("Resultados por algoritmo:\n")
        for nombre, (exactitud, _, _) in resultados.items():
            f.write(f"  {nombre}: {exactitud:.4f}\n")
        f.write("\nReporte detallado (mejor modelo):\n")
        f.write(mejor_reporte)
        f.write("\nMatriz de confusion:\n")
        f.write(f"Clases: {list(encoder.classes_)}\n")
        f.write(str(matriz) + "\n")

    print(f"\nArchivos guardados en '{RUTA_MODELO_DIR}/':")
    print("  model.pkl")
    print("  label_encoder.pkl")
    print("  reporte_metricas.txt")


if __name__ == "__main__":
    main()
