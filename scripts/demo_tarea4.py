"""
Demo para Tarea 4 - HandTalk AI
Muestra: captura de camara, deteccion de mano con MediaPipe y conteo de dedos levantados.
Basado en los ejemplos del auxiliar (Clase 10).

Ejecutar:
    source .venv/bin/activate
    python scripts/demo_tarea4.py

Controles:
    Q  Cerrar la ventana
"""

import cv2
import mediapipe as mp

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils
mp_estilos = mp.solutions.drawing_styles

# Nombres de los 5 dedos para mostrar en pantalla
NOMBRES_DEDOS = ["Pulgar", "Indice", "Medio", "Anular", "Menique"]

# Señas de LESEGUA reconocidas por estado de dedos levantados
# Esto es una version simplificada; el modelo ML completo usa landmarks normalizados
GESTOS_LESEGUA = {
    (0, 0, 0, 0, 0): "silencio",
    (1, 0, 0, 0, 0): "hola (pulgar)",
    (0, 1, 0, 0, 0): "si (indice)",
    (0, 0, 0, 0, 1): "no (menique)",
    (1, 1, 0, 0, 0): "bien",
    (0, 1, 1, 0, 0): "agua",
    (1, 0, 0, 0, 1): "gracias",
    (1, 1, 1, 1, 1): "ayuda (mano abierta)",
}


def detectar_dedos_levantados(puntos: list) -> list:
    """
    Detecta cuales dedos estan levantados comparando posiciones de landmarks.
    Devuelve lista de 5 valores binarios: [pulgar, indice, medio, anular, menique]
    """
    dedos = [0, 0, 0, 0, 0]

    # Pulgar: comparamos en el eje X porque se mueve horizontal
    if puntos[4][0] < puntos[3][0]:
        dedos[0] = 1

    # Los demas dedos: la punta (tip) debe estar mas arriba que la articulacion media
    pares = [(8, 6), (12, 10), (16, 14), (20, 18)]
    for i, (tip, mid) in enumerate(pares):
        if puntos[tip][1] < puntos[mid][1]:
            dedos[i + 1] = 1

    return dedos


def dibujar_hud(frame, dedos: list, gesto: str, mano_detectada: bool):
    """
    Dibuja el HUD (heads-up display) con la informacion de deteccion sobre el frame.
    """
    h, w = frame.shape[:2]

    # Barra de estado arriba
    cv2.rectangle(frame, (0, 0), (w, 50), (15, 15, 25), -1)
    estado_txt = "MANO DETECTADA" if mano_detectada else "Esperando mano..."
    color_estado = (0, 220, 80) if mano_detectada else (100, 100, 110)
    cv2.putText(frame, "HandTalk AI  |  Tarea 4  |  " + estado_txt,
                (12, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color_estado, 2)

    if not mano_detectada:
        return

    # Panel inferior con el gesto y el conteo
    cv2.rectangle(frame, (0, h - 90), (w, h), (15, 15, 25), -1)

    total_dedos = sum(dedos)
    cv2.putText(frame, f"Dedos levantados: {total_dedos}",
                (12, h - 56), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)

    # Indicadores individuales de cada dedo
    for i, (nombre, activo) in enumerate(zip(NOMBRES_DEDOS, dedos)):
        color = (0, 220, 80) if activo else (60, 60, 80)
        x = 12 + i * 120
        cv2.rectangle(frame, (x, h - 46), (x + 112, h - 8), color, -1)
        cv2.putText(frame, nombre, (x + 6, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255) if activo else (120, 120, 130), 1)

    # Nombre del gesto reconocido
    if gesto:
        cv2.putText(frame, gesto.upper(), (12, h - 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)


def main():
    print("=== HandTalk AI - Demo Tarea 4 ===")
    print("Presiona Q para salir")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo abrir la camara")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    with mp_manos.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as detector:

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error al leer frame de la camara")
                break

            # Espejamos para que sea mas natural (como mirarse al espejo)
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultado = detector.process(rgb)

            dedos = [0, 0, 0, 0, 0]
            gesto = ""
            mano_detectada = False

            if resultado.multi_hand_landmarks:
                mano_detectada = True
                for mano_lm in resultado.multi_hand_landmarks:
                    # Dibujar los 21 landmarks y sus conexiones
                    mp_dibujo.draw_landmarks(
                        frame,
                        mano_lm,
                        mp_manos.HAND_CONNECTIONS,
                        mp_estilos.get_default_hand_landmarks_style(),
                        mp_estilos.get_default_hand_connections_style()
                    )

                    h_px, w_px = frame.shape[:2]
                    puntos = [
                        (int(lm.x * w_px), int(lm.y * h_px))
                        for lm in mano_lm.landmark
                    ]

                    dedos = detectar_dedos_levantados(puntos)
                    gesto = GESTOS_LESEGUA.get(tuple(dedos), "gesto personalizado")

                    # Mostramos en consola para el video
                    print(f"Dedos: {dedos}  |  Gesto: {gesto}")

            dibujar_hud(frame, dedos, gesto, mano_detectada)

            cv2.imshow("HandTalk AI - Demo Tarea 4", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("Demo cerrado.")


if __name__ == "__main__":
    main()
