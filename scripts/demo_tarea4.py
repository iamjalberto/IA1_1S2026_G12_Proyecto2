"""
HandTalk AI - Reconocedor de senas LENSEGUA
Detecta la mano en tiempo real con MediaPipe y clasifica gestos por posicion de dedos.

Ejecutar:
    source .venv/bin/activate
    python scripts/demo_tarea4.py

Controles dentro de la ventana:
    0-9  Cambiar camara en caliente
    Q    Cerrar
"""

import cv2
import mediapipe as mp

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils
mp_estilos = mp.solutions.drawing_styles

NOMBRES_DEDOS = ["Pulgar", "Indice", "Medio", "Anular", "Menique"]

# Mapeo simplificado de dedos levantados a senas LENSEGUA
# El modelo ML completo (que se entrenara con el dataset) usara landmarks normalizados
GESTOS_LENSEGUA = {
    (0, 0, 0, 0, 0): "silencio",
    (1, 0, 0, 0, 0): "hola",
    (0, 1, 0, 0, 0): "si",
    (0, 0, 0, 0, 1): "no",
    (1, 1, 0, 0, 0): "bien",
    (0, 1, 1, 0, 0): "agua",
    (1, 0, 0, 0, 1): "gracias",
    (1, 1, 1, 1, 1): "ayuda",
}


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


def detectar_dedos_levantados(puntos: list) -> list:
    """
    Detecta cuales dedos estan levantados usando los landmarks de MediaPipe.
    Retorna lista de 5 valores binarios: [pulgar, indice, medio, anular, menique]
    """
    dedos = [0, 0, 0, 0, 0]

    # Pulgar: se compara en eje X porque se mueve de forma horizontal
    if puntos[4][0] < puntos[3][0]:
        dedos[0] = 1

    # Resto de dedos: la punta debe estar mas arriba (menor Y) que la articulacion PIP
    for i, (tip, pip) in enumerate([(8, 6), (12, 10), (16, 14), (20, 18)]):
        if puntos[tip][1] < puntos[pip][1]:
            dedos[i + 1] = 1

    return dedos


def dibujar_hud(frame, dedos: list, gesto: str, mano_detectada: bool, indice_cam: int, camaras: list):
    """Superpone toda la informacion sobre el frame de la camara."""
    h, w = frame.shape[:2]

    # Franja superior con titulo, camara activa y lista de disponibles
    cv2.rectangle(frame, (0, 0), (w, 52), (12, 12, 22), -1)
    cams_txt = "  cam:" + str(indice_cam) + "  [" + "/".join(str(c) for c in camaras) + "]"
    cv2.putText(frame, "HandTalk AI  |  LENSEGUA" + cams_txt,
                (12, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (150, 150, 160), 1)

    color_estado = (0, 220, 80) if mano_detectada else (90, 90, 100)
    estado_txt = "Mano detectada" if mano_detectada else "Esperando mano..."
    cv2.putText(frame, estado_txt + "   [0-9] camara  [Q] salir",
                (12, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.50, color_estado, 1)

    if not mano_detectada:
        return

    # Nombre del gesto en grande, encima del panel inferior
    if gesto:
        cv2.putText(frame, gesto.upper(), (12, h - 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 200, 255), 3)

    # Franja inferior con chips de dedos
    cv2.rectangle(frame, (0, h - 85), (w, h), (12, 12, 22), -1)
    total = sum(dedos)
    cv2.putText(frame, f"Dedos levantados: {total}",
                (12, h - 58), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (190, 190, 190), 2)

    ancho_chip = w // 5 - 6
    for i, (nombre, activo) in enumerate(zip(NOMBRES_DEDOS, dedos)):
        color_bg = (0, 140, 50) if activo else (40, 40, 60)
        color_txt = (255, 255, 255) if activo else (100, 100, 110)
        x0 = 4 + i * (ancho_chip + 6)
        cv2.rectangle(frame, (x0, h - 48), (x0 + ancho_chip, h - 6), color_bg, -1)
        cv2.putText(frame, nombre, (x0 + 6, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, color_txt, 1)


def main():
    camaras = detectar_camaras()

    if not camaras:
        print("Error: no se encontro ninguna camara disponible")
        return

    # Arranca directamente en la primera camara sin mostrar selector
    indice_cam = camaras[0]
    print(f"Iniciando HandTalk AI en camara {indice_cam}")
    print(f"Camaras disponibles: {camaras}")
    print("Usa teclas 0-9 para cambiar de camara en caliente. Q para salir.")

    cap = cv2.VideoCapture(indice_cam)
    if not cap.isOpened():
        print(f"Error: no se pudo abrir la camara {indice_cam}")
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
                break

            # Espejo para que sea mas natural al usuario
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resultado = detector.process(rgb)

            dedos = [0, 0, 0, 0, 0]
            gesto = ""
            mano_detectada = False

            if resultado.multi_hand_landmarks:
                mano_detectada = True
                for mano_lm in resultado.multi_hand_landmarks:
                    mp_dibujo.draw_landmarks(
                        frame, mano_lm, mp_manos.HAND_CONNECTIONS,
                        mp_estilos.get_default_hand_landmarks_style(),
                        mp_estilos.get_default_hand_connections_style()
                    )
                    h_px, w_px = frame.shape[:2]
                    puntos = [
                        (int(lm.x * w_px), int(lm.y * h_px))
                        for lm in mano_lm.landmark
                    ]
                    dedos = detectar_dedos_levantados(puntos)
                    gesto = GESTOS_LENSEGUA.get(tuple(dedos), "")

            dibujar_hud(frame, dedos, gesto, mano_detectada, indice_cam, camaras)
            cv2.imshow("HandTalk AI", frame)

            tecla = cv2.waitKey(1) & 0xFF

            # Cambiar camara en caliente con teclas numericas
            if tecla != 255 and chr(tecla).isdigit() and int(chr(tecla)) in camaras:
                nuevo = int(chr(tecla))
                if nuevo != indice_cam:
                    cap.release()
                    indice_cam = nuevo
                    cap = cv2.VideoCapture(indice_cam)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    print(f"Cambiando a camara {indice_cam}")

            if tecla == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
