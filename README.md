# HandTalk AI — Proyecto 2

**Curso:** Inteligencia Artificial 1
**Universidad San Carlos de Guatemala — Facultad de Ingenieria**
**Grupo 12**

## Integrantes

| Nombre | Carne |
|--------|-------|
| Jose Alberto Alarcon Chigua | 201346084 |

## Descripcion

HandTalk AI es un sistema de reconocimiento de senas del lenguaje LENSEGUA en tiempo real. Usa la camara web para detectar la mano del usuario, extrae 63 landmarks normalizados con MediaPipe Hands y clasifica la sena con un modelo SVM RBF entrenado con scikit-learn (99.98% de exactitud en cross-validation). El resultado se muestra en una interfaz Vue 3 y puede enviarse como mensaje al bot de Telegram @IA1_G12_bot.

## Senas reconocidas (10 clases)

| Sena | Descripcion |
|------|-------------|
| hola | Mano abierta con 5 dedos, agitarla de lado a lado |
| si | Puno cerrado, mover arriba y abajo |
| no | Indice y medio juntos, mover de lado a lado |
| tu | Indice apuntando hacia adelante |
| yo | Indice apuntando hacia el propio pecho |
| excelente | Pulgar hacia arriba (thumbs up) |
| te_amo | Pulgar, indice y menique extendidos |
| igual | Indice y medio en V (signo de paz) |
| nombre | Nudillos contra la frente |
| mucho | Dos manos separandose hacia los lados |

## Inicio rapido

```bash
# 1. Clonar el repositorio
git clone https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2
cd IA1_1S2026_G12_Proyecto2/HandTalkAI

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Levantar todo el sistema con Docker
docker compose up --build

# 4. Abrir en el navegador
# Vista usuario: http://localhost:5173
# Panel admin:   http://localhost:5173/#/admin  (admin / handtalk2026)
```

## Arquitectura

```
dataset.csv (5000 muestras)
      |
      v
Entrenamiento (Panel Admin)
  KNN / SVM RBF / Random Forest / Regresion Logistica
  -> mejor modelo: SVM RBF (99.98% CV)
  -> guardado en modelo/model.pkl
      |
      v
Backend Flask :5000
  - hilo de camara (MediaPipe + SVM en tiempo real)
  - endpoints REST publicos y admin
      |
      v
Frontend Vue 3 :5173 (Nginx)
  - stream MJPEG en vivo
  - deteccion en tiempo real
  - envio a Telegram
      |
      v
Bot Telegram @IA1_G12_bot
```

## Tecnologias

| Capa | Tecnologia | Version |
|------|-----------|---------|
| Deteccion de mano | MediaPipe Hands | 0.10.21 |
| Vision por computadora | OpenCV | 4.11.0 |
| Machine Learning | scikit-learn | 1.8.0 |
| Backend API | Flask + flask-cors | 3.1.3 |
| Frontend | Vue 3 + Vite | 3.x |
| Contenedores | Docker + Docker Compose | 28.x |
| Mensajeria | Telegram Bot API | REST |

## Estructura del proyecto

```
HandTalkAI/
├── app/
│   ├── config/settings.py       # Configuracion del sistema
│   ├── routes/
│   │   ├── main.py              # Endpoints publicos (stream, estado, telegram)
│   │   ├── admin.py             # Panel admin (config, metricas, entrenamiento)
│   │   └── captura.py           # Captura de dataset desde browser
│   └── services/
│       ├── detector.py          # MediaPipe + normalizacion de landmarks
│       ├── predictor.py         # Carga y prediccion del modelo
│       ├── metricas.py          # Historial de detecciones
│       └── telegram_bot.py      # Envio de mensajes a Telegram
├── frontend/src/views/
│   ├── VistaUsuario.vue         # Pantalla principal
│   └── VistaAdmin.vue           # Panel de administracion
├── dataset/dataset.csv          # 5000 muestras de landmarks
├── modelo/model.pkl             # SVM RBF entrenado
├── config/config.json           # Configuracion activa
└── docs/
    ├── manual_tecnico.md        # Manual tecnico completo
    └── manual_usuario.md        # Guia de usuario
```

## Documentacion

- [Manual Tecnico](docs/manual_tecnico.md)
- [Manual de Usuario](docs/manual_usuario.md)

## Licencia

MIT — ver [LICENSE](LICENSE)
