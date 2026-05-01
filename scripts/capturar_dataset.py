"""
Script para recolectar el dataset de senas de LENSEGUA.
Usa MediaPipe para detectar la mano y extrae 63 landmarks normalizados por captura.
Los datos se guardan en dataset/dataset.csv.

Controles:
  [0-9]   Seleccionar la clase (sena) a capturar
  ESPACIO Iniciar captura automatica de MUESTRAS_POR_CLASE frames
  R       Reiniciar (borrar) muestras de la clase actual
  C       Cambiar camara (cuando no esta grabando)
  Q / ESC Salir
"""

import csv
import os
import sys

import cv2
import mediapipe as mp
import numpy as np

# Las 10 senas de LENSEGUA que vamos a reconocer
CLASES = [
    "hola",
    "si",
    "no",
    "tu",
    "yo",
    "excelente",
    "te_amo",
    "igual",
    "nombre",
    "mucho",
]

# Descripcion de como realizar cada sena — se muestra en pantalla durante la captura
DESCRIPCIONES = {
    "hola":      "Mano extendida, palma al frente, dedos ligeramente abiertos",
    "si":        "Pulgar apuntando hacia arriba, demas dedos cerrados",
    "no":        "Pulgar apuntando hacia abajo, demas dedos cerrados",
    "tu":        "Indice extendido apuntando hacia la camara (hacia adelante)",
    "yo":        "Indice extendido apuntando hacia tu propio pecho",
    "excelente": "Signo clasico de excelente: pulgar e indice formando circulo",
    "te_amo":    "Pulgar, indice y menique extendidos (signo ILY)",
    "igual":     "Dos dedos (V) inclinados horizontalmente",
    "nombre":    "Letra N del alfabeto LENSEGUA",
    "mucho":     "Dedos juntos en punta (como gesto italiano de cantidad)",
}

# Cuantas muestras capturar por clase — 500 a ~10fps = ~50 segundos por sena
MUESTRAS_POR_CLASE = 500

# Cuantas capturas de pantalla guardar por sena como evidencia de recoleccion
EVIDENCIAS_POR_CLASE = 5

# Carpeta donde se guardan las capturas de evidencia
RUTA_EVIDENCIA = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "dataset", "evidencia")
)

# Ruta del CSV donde se acumula el dataset
RUTA_CSV = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "dataset", "dataset.csv")
)

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils


def normalizar_landmarks(hand_landmarks) -> list:
    """
    Normaliza los 21 landmarks de la mano:
    - Los centra en la muneca (landmark 0)
    - Los escala por la distancia maxima para invarianza de tamano
    """
    puntos = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
    puntos -= puntos[0]
    distancia_max = np.max(np.abs(puntos))
    if distancia_max > 0:
        puntos /= distancia_max
    return puntos.flatten().tolist()


def contar_muestras(ruta_csv: str) -> dict:
    """Cuenta cuantas muestras hay de cada clase en el CSV existente."""
    conteo = {clase: 0 for clase in CLASES}
    if not os.path.exists(ruta_csv):
        return conteo
    with open(ruta_csv, "r") as f:
        lector = csv.reader(f)
        next(lector, None)  # saltar encabezado
        for fila in lector:
            if fila and fila[0] in conteo:
                conteo[fila[0]] += 1
    return conteo


def borrar_clase(ruta_csv: str, clase: str) -> None:
    """
    Elimina del CSV todas las filas que pertenecen a la clase indicada.
    Util para volver a grabar una sena desde cero si la captura salio mal.
    """
    if not os.path.exists(ruta_csv):
        return
    with open(ruta_csv, "r") as f:
        filas = list(csv.reader(f))
    # La primera fila es el encabezado, se conserva siempre
    encabezado = filas[0] if filas else []
    resto = [fila for fila in filas[1:] if fila and fila[0] != clase]
    with open(ruta_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(encabezado)
        writer.writerows(resto)
    print(f"  Clase '{clase}' reiniciada — muestras borradas del CSV.")


def inicializar_csv(ruta_csv: str) -> None:
    """Crea el CSV con encabezado si aun no existe."""
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    if not os.path.exists(ruta_csv):
        with open(ruta_csv, "w", newline="") as f:
            writer = csv.writer(f)
            # 63 columnas: x0,y0,z0 ... x20,y20,z20
            encabezado = ["clase"] + [f"{coord}{i}" for i in range(21) for coord in ("x", "y", "z")]
            writer.writerow(encabezado)
        print(f"Dataset creado en: {ruta_csv}")


def detectar_camaras() -> list:
    """Prueba indices 0-9 y retorna los que tienen camara funcional."""
    disponibles = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                disponibles.append(i)
        cap.release()
    return disponibles


def seleccionar_camara(camaras: list) -> int:
    """
    Muestra una pantalla de seleccion de camara con preview en vivo.
    El usuario presiona el numero de la camara que quiere usar y ENTER para confirmar.
    Si solo hay una camara, la retorna directamente sin mostrar pantalla.
    """
    if len(camaras) == 1:
        return camaras[0]

    seleccion = camaras[0]
    cap = cv2.VideoCapture(seleccion)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\nVarias camaras detectadas. Selecciona una en la ventana de preview.")

    while True:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            # Overlay de seleccion
            cv2.rectangle(frame, (0, 0), (w, 54), (10, 10, 30), -1)
            cv2.putText(frame, "Seleccionar camara — presiona numero y ENTER para confirmar",
                        (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 200, 255), 1)
            cv2.putText(frame, f"Camara actual: {seleccion}   |   Camaras disponibles: {camaras}",
                        (10, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (150, 230, 150), 1)

            y = 80
            for i, cam in enumerate(camaras):
                color = (0, 230, 255) if cam == seleccion else (120, 120, 120)
                cv2.putText(frame, f"[{i}] Camara {cam}", (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                y += 30

            cv2.imshow("Seleccion de Camara - HandTalk AI", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == 13:  # ENTER confirma
            break
        elif ord("0") <= tecla <= ord("9"):
            idx = tecla - ord("0")
            if idx < len(camaras) and camaras[idx] != seleccion:
                seleccion = camaras[idx]
                cap.release()
                cap = cv2.VideoCapture(seleccion)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cap.release()
    cv2.destroyAllWindows()
    return seleccion


def main():
    inicializar_csv(RUTA_CSV)

    clase_actual = 0
    capturando = False
    frames_capturados = 0
    # Guardamos solo 1 de cada 3 frames para capturar a ~10fps en lugar de 30fps.
    # Asi cada muestra es visualmente diferente y el modelo aprende mas variacion.
    CAPTURA_CADA_N_FRAMES = 3
    frame_contador = 0
    evidencias_guardadas = 0  # cuantas capturas de evidencia llevamos en esta clase

    os.makedirs(RUTA_EVIDENCIA, exist_ok=True)

    # Detectar camaras disponibles y dejar al usuario elegir
    camaras = detectar_camaras()
    if not camaras:
        print("ERROR: No se encontro ninguna camara disponible.")
        sys.exit(1)
    indice_cam = seleccionar_camara(camaras)

    cap = cv2.VideoCapture(indice_cam)
    if not cap.isOpened():
        print("ERROR: No se pudo acceder a la camara.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\n=== Recoleccion de Dataset - HandTalk AI ===")
    print(f"Camaras disponibles: {camaras}")
    print("Clases disponibles:")
    for i, c in enumerate(CLASES):
        print(f"  [{i}] {c}")
    print("\nSelecciona clase con [0-9], inicia con ESPACIO, C para cambiar camara, Q para salir\n")

    with mp_manos.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as detector:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultado = detector.process(rgb)

            conteo = contar_muestras(RUTA_CSV)

            if resultado.multi_hand_landmarks:
                for mano_lm in resultado.multi_hand_landmarks:
                    mp_dibujo.draw_landmarks(frame, mano_lm, mp_manos.HAND_CONNECTIONS)

                    # Guardar muestra si estamos en modo captura, a ~10fps
                    if capturando and frames_capturados < MUESTRAS_POR_CLASE:
                        if frame_contador % CAPTURA_CADA_N_FRAMES == 0:
                            caracteristicas = normalizar_landmarks(mano_lm)
                            with open(RUTA_CSV, "a", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow([CLASES[clase_actual]] + caracteristicas)
                            frames_capturados += 1

                    if capturando and frames_capturados >= MUESTRAS_POR_CLASE:
                        capturando = False
                        print(f"  Clase '{CLASES[clase_actual]}': {frames_capturados} muestras guardadas.")
                    break

            # Guardar capturas de evidencia en momentos distribuidos de la grabacion.
            # Se toman en los puntos: 10%, 30%, 50%, 70%, 90% del total.
            if capturando and evidencias_guardadas < EVIDENCIAS_POR_CLASE:
                puntos = [int(MUESTRAS_POR_CLASE * p) for p in (0.10, 0.30, 0.50, 0.70, 0.90)]
                if frames_capturados in puntos:
                    nombre_archivo = (
                        f"{CLASES[clase_actual]}_"
                        f"{evidencias_guardadas + 1}de{EVIDENCIAS_POR_CLASE}.jpg"
                    )
                    ruta_img = os.path.join(RUTA_EVIDENCIA, nombre_archivo)
                    cv2.imwrite(ruta_img, frame)
                    evidencias_guardadas += 1

            h_f, w_f = frame.shape[:2]

            # Barra superior con titulo y boton de camara
            cv2.rectangle(frame, (0, 0), (w_f, 44), (12, 12, 22), -1)
            cv2.putText(frame, "HandTalk AI  |  Captura de Dataset  |  LENSEGUA",
                        (10, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (150, 150, 160), 1)

            # Boton visual de camara en la esquina superior derecha
            color_btn = (30, 100, 30) if len(camaras) > 1 else (40, 40, 40)
            cv2.rectangle(frame, (w_f - 160, 4), (w_f - 4, 40), color_btn, -1)
            cv2.rectangle(frame, (w_f - 160, 4), (w_f - 4, 40), (80, 180, 80), 1)
            cam_btn_txt = f"CAM {indice_cam}  [C] cambiar"
            cv2.putText(frame, cam_btn_txt, (w_f - 154, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (180, 255, 180), 1)

            # Panel lateral de informacion (debajo de la barra)
            cv2.rectangle(frame, (0, 44), (310, 270), (15, 15, 15), -1)
            cv2.putText(frame, f"Clase: {CLASES[clase_actual]}", (8, 72),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 230, 255), 2)
            cv2.putText(frame, f"Muestras: {conteo[CLASES[clase_actual]]}",
                        (8, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 220, 50), 2)

            # Descripcion de como hacer la sena — se parte en dos lineas si es larga
            desc = DESCRIPCIONES.get(CLASES[clase_actual], "")
            palabras = desc.split()
            linea1, linea2 = "", ""
            for palabra in palabras:
                if len(linea1) + len(palabra) < 32:
                    linea1 += palabra + " "
                else:
                    linea2 += palabra + " "
            cv2.putText(frame, linea1.strip(), (8, 122),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
            if linea2.strip():
                cv2.putText(frame, linea2.strip(), (8, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)

            if capturando:
                # Borde verde cuando esta capturando
                cv2.rectangle(frame, (2, 2), (w_f - 2, h_f - 2), (0, 220, 50), 4)
                cv2.putText(frame, f"GRABANDO {frames_capturados}/{MUESTRAS_POR_CLASE}",
                            (8, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 50), 2)
            else:
                cv2.putText(frame, "ESPACIO: capturar  R: reiniciar  Q/ESC: salir",
                            (8, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

            # Lista de clases con contador
            y = 180
            for i, clase in enumerate(CLASES):
                color = (0, 230, 255) if i == clase_actual else (120, 120, 120)
                cv2.putText(frame, f"[{i}] {clase}: {conteo[clase]}",
                            (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1)
                y += 17

            cv2.imshow("Captura de Dataset - HandTalk AI", frame)
            frame_contador += 1

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("q") or tecla == 27:  # Q o ESC para salir
                break
            elif ord("0") <= tecla <= ord("9"):
                idx = tecla - ord("0")
                if idx < len(CLASES):
                    clase_actual = idx
                    capturando = False
                    frames_capturados = 0
                    evidencias_guardadas = 0
            elif tecla == ord("c") and len(camaras) > 1 and not capturando:
                # Ciclar a la siguiente camara disponible
                pos_actual = camaras.index(indice_cam)
                indice_cam = camaras[(pos_actual + 1) % len(camaras)]
                cap.release()
                cap = cv2.VideoCapture(indice_cam)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print(f"Camara cambiada a: {indice_cam}")
            elif tecla == ord("r") and not capturando:
                # Borrar todas las muestras de la clase actual para volver a grabarla
                borrar_clase(RUTA_CSV, CLASES[clase_actual])
                frames_capturados = 0
                evidencias_guardadas = 0
            elif tecla == ord(" ") and not capturando:
                capturando = True
                frames_capturados = 0
                evidencias_guardadas = 0
                print(f"Capturando '{CLASES[clase_actual]}'...")

    cap.release()
    cv2.destroyAllWindows()

    print("\nResumen final del dataset:")
    conteo = contar_muestras(RUTA_CSV)
    for clase, n in conteo.items():
        barra = "#" * (n // 10)
        print(f"  {clase:12s}: {n:4d}  {barra}")


if __name__ == "__main__":
    main()
