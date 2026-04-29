# HandTalk AI - Proyecto 2

**Curso:** Inteligencia Artificial 1  
**Universidad San Carlos de Guatemala - Facultad de Ingenieria**  
**Grupo 12**

## Integrantes

| Nombre | Carne |
|--------|-------|
| Jose Alberto Alarcon Chigua | 201346084 |

## Descripcion

HandTalk AI es un sistema de reconocimiento de senas del lenguaje LENSEGUA en tiempo real. Usa la camara web para detectar la mano del usuario, extrae los landmarks con MediaPipe y clasifica la sena con un modelo de machine learning entrenado con scikit-learn. El resultado se muestra en una interfaz web y puede enviarse como mensaje al bot de Telegram del grupo.

## Senas reconocidas

| Numero | Sena |
|--------|------|
| 0 | hola |
| 1 | gracias |
| 2 | si |
| 3 | no |
| 4 | ayuda |
| 5 | agua |
| 6 | bien |
| 7 | mal |
| 8 | por_favor |
| 9 | casa |

## Arquitectura

```
capturar_dataset.py  →  dataset.csv  →  entrenar_modelo.py  →  model.pkl
                                                                    ↓
                                               Flask backend (port 5000)
                                                      ↓
                                            Vue 3 frontend (port 5173)
                                                      ↓
                                              Bot de Telegram
```

## Tecnologias

| Capa | Tecnologia |
|------|-----------|
| Deteccion de mano | MediaPipe Hands |
| Clasificacion | scikit-learn (Random Forest / SVM / KNN / Regresion Logistica) |
| Backend API | Flask 3 + flask-cors |
| Frontend | Vue 3 + Vite |
| Bot mensajeria | python-telegram-bot (Cloudflare Workers) |
| Contenedores | Docker + Docker Compose |

## Estructura del proyecto

```
HandTalkAI/
├── app/
│   ├── __init__.py          # Factory de Flask
│   ├── config/
│   │   └── settings.py      # Carga y guarda config.json
│   ├── routes/
│   │   ├── main.py          # Endpoints usuario: /video_feed, /api/estado, etc.
│   │   └── admin.py         # Endpoints admin: /admin/config, /admin/metricas
│   └── services/
│       ├── detector.py      # MediaPipe: extrae 63 landmarks normalizados
│       ├── predictor.py     # Carga model.pkl y predice
│       ├── metricas.py      # Historial de detecciones
│       └── telegram_bot.py  # Envia mensajes via API de Telegram
├── frontend/
│   └── src/
│       ├── views/
│       │   ├── VistaUsuario.vue   # Camara + captura de senas
│       │   └── VistaAdmin.vue     # Panel de administracion
│       └── router/                # Vue Router
├── scripts/
│   ├── capturar_dataset.py  # Grabar muestras del dataset con la camara
│   ├── entrenar_modelo.py   # Entrenar y guardar model.pkl
│   └── demo_tarea4.py       # Demo standalone (sin Flask)
├── dataset/
│   └── dataset.csv          # Dataset con landmarks de las senas
├── modelo/
│   ├── model.pkl            # Modelo entrenado
│   ├── label_encoder.pkl    # Codificador de etiquetas
│   └── reporte_metricas.txt # Reporte de accuracy por clase
├── Dockerfile
├── docker-compose.yml
├── main.py                  # Entry point del backend Flask
└── requirements.txt
```

## Instalacion y uso local

### Requisitos

- Python 3.10+
- Node.js 18+
- Camara web

### 1. Clonar el repositorio

```bash
git clone https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2
cd IA1_1S2026_G12_Proyecto2/HandTalkAI
```

### 2. Crear entorno virtual e instalar dependencias Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env y colocar el token del bot de Telegram
```

### 4. Grabar el dataset

```bash
python scripts/capturar_dataset.py
# Controles:
#   [0-9]    Seleccionar sena (ver lista arriba)
#   ESPACIO  Iniciar captura automatica (100 muestras)
#   C        Cambiar camara
#   Q        Salir
```

### 5. Entrenar el modelo

```bash
python scripts/entrenar_modelo.py
# Guarda model.pkl, label_encoder.pkl y reporte_metricas.txt en modelo/
```

### 6. Iniciar el backend

```bash
python main.py
# Flask corre en http://localhost:5000
```

### 7. Iniciar el frontend (otra terminal)

```bash
cd frontend
npm install
npm run dev
# Vite corre en http://localhost:5173
```

## Uso con Docker

```bash
docker-compose up --build
# Backend: http://localhost:5000
# Frontend: http://localhost:5173
```

## Bot de Telegram

El bot `@IA1_G12_bot` esta integrado en dos formas:
1. **Tarea 5** (standalone): Cloudflare Worker en `https://ia1-tarea5-bot.iam-289.workers.dev`
2. **Proyecto 2** (integrado): El panel admin permite configurar el Chat ID al que se envian las detecciones

Para habilitar el envio desde el proyecto, activa "Envio a Telegram" en el panel de administracion e ingresa el Chat ID del grupo.

## Licencia

MIT
