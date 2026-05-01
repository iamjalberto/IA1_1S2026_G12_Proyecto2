import mediapipe as mp
import numpy as np
import cv2

mp_manos = mp.solutions.hands
mp_dibujo = mp.solutions.drawing_utils

# Instancia global de MediaPipe para toda la app, evita recargarla en cada frame
_detector_manos = mp_manos.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


def normalizar_landmarks(hand_landmarks) -> list:
    """
    Extrae los 21 landmarks de la mano y los normaliza:
    - Centra en la muneca (landmark 0)
    - Escala por la distancia maxima para que sea invariante al tamano de la mano
    - Normaliza quiralidad: si el pulgar (landmark 1) queda a la derecha (x1 > 0),
      invierte todos los x. Asi el modelo recibe siempre la misma orientacion
      sin importar si se usa mano izquierda, derecha o hay un flip en el frame.
    Retorna una lista plana de 63 valores (21 puntos * 3 coordenadas).
    """
    puntos = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])

    # Centrar todos los puntos respecto a la muneca
    puntos -= puntos[0]

    # Normalizar la escala para que no dependa de que tan cerca este la mano
    distancia_max = np.max(np.abs(puntos))
    if distancia_max > 0:
        puntos /= distancia_max

    # Normalizar quiralidad: forzar que el pulgar siempre quede a la izquierda (x1 < 0).
    # Esto hace el descriptor invariante a si el frame esta volteado o no.
    if puntos[1][0] > 0:
        puntos[:, 0] *= -1

    return puntos.flatten().tolist()


def procesar_frame(frame_bgr):
    """
    Recibe un frame en BGR, detecta la mano con MediaPipe y dibuja los landmarks.
    Retorna:
      - frame_anotado: el mismo frame con los landmarks dibujados
      - caracteristicas: lista de 63 valores normalizados, o None si no hay mano
    """
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    resultado = _detector_manos.process(rgb)

    frame_anotado = frame_bgr.copy()
    caracteristicas = None

    if resultado.multi_hand_landmarks:
        for mano_lm in resultado.multi_hand_landmarks:
            mp_dibujo.draw_landmarks(frame_anotado, mano_lm, mp_manos.HAND_CONNECTIONS)
            # Solo tomamos la primera mano detectada
            caracteristicas = normalizar_landmarks(mano_lm)
            break

    return frame_anotado, caracteristicas
