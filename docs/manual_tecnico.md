# Manual Tecnico — HandTalk AI

**Proyecto 2 — Inteligencia Artificial 1**
**Universidad San Carlos de Guatemala — Facultad de Ingenieria**
**Grupo 12 | Jose Alberto Alarcon Chigua | 201346084**

---

## 1. Descripcion general del sistema

HandTalk AI es un sistema web de reconocimiento de senas del lenguaje LENSEGUA en tiempo real. Captura video desde la camara del servidor, detecta la mano con MediaPipe Hands, extrae 63 caracteristicas numericas (landmarks normalizados) y las clasifica con un modelo SVM RBF entrenado con scikit-learn. El resultado se muestra en una interfaz Vue 3 y puede enviarse a un chat de Telegram mediante el bot @IA1_G12_bot.

El sistema esta completamente contenido en Docker (dos contenedores: backend Flask y frontend Nginx) y puede desplegarse en local o en un servidor cloud como Google Cloud Platform.

---

## 2. Arquitectura general

```
┌──────────────────────────────────────────────────────────────┐
│                  CLIENTE (Navegador)                         │
│              Vue 3 + Vite  :5173                             │
│                                                              │
│   VistaUsuario.vue              VistaAdmin.vue               │
│   - Stream en vivo              - Config del sistema         │
│   - Prediccion en tiempo real   - Metricas de uso            │
│   - Envio a Telegram            - Entrenamiento del modelo   │
│   - Historial de detecciones    - Captura del dataset        │
│   - Lista de senas              - Historial y logs           │
└──────────────────────────┬───────────────────────────────────┘
                           │  HTTP / MJPEG (proxy Nginx → Flask)
┌──────────────────────────▼───────────────────────────────────┐
│                  BACKEND (Flask :5000)                       │
│                                                              │
│  Rutas publicas:                                             │
│  GET  /video_feed          <- stream MJPEG con anotaciones   │
│  GET  /api/estado          <- ultima prediccion + confianza  │
│  GET  /api/senas           <- clases disponibles del modelo  │
│  GET  /api/historial       <- ultimas 30 detecciones         │
│  POST /api/capturar_sena   <- guarda deteccion en historial  │
│  POST /api/enviar_telegram <- envia mensaje al bot           │
│  GET  /api/salud           <- health check                   │
│  GET  /api/camaras         <- lista camaras disponibles      │
│  POST /api/cambiar_camara  <- cambia indice de camara activa │
│  GET  /admin/config_publica                                  │
│                                                              │
│  Rutas admin (requieren sesion):                             │
│  GET/POST /admin/config    <- ver y editar config.json       │
│  GET  /admin/metricas      <- estadisticas agregadas         │
│  GET  /admin/historial     <- historial paginado             │
│  POST /admin/limpiar_historial                               │
│  GET  /admin/modelo_info   <- reporte del modelo actual      │
│  POST /admin/entrenar      <- lanza entrenamiento en hilo    │
│  GET  /admin/estado_entrenamiento <- progreso del training   │
│  POST /admin/capturar_frame <- frame base64 -> landmarks CSV │
│  GET  /admin/progreso_captura <- conteo de muestras          │
│                                                              │
│  ┌────────────────┐ ┌───────────────┐ ┌──────────────────┐  │
│  │  detector.py   │ │ predictor.py  │ │ telegram_bot.py  │  │
│  │ (MediaPipe)    │ │ (model.pkl)   │ │ (API REST TG)    │  │
│  └───────┬────────┘ └───────┬───────┘ └──────────────────┘  │
└──────────┼──────────────────┼───────────────────────────────┘
           │                  │
┌──────────▼──────────────────▼──────────────────────────────┐
│         CAMARA  /  MODELO  /  DATASET                       │
│  cv2.VideoCapture     modelo/model.pkl    dataset.csv       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Estructura de archivos

```
HandTalkAI/
├── main.py                          # Entry point: inicia camara y servidor Flask
├── requirements.txt                 # Dependencias Python
├── Dockerfile                       # Imagen Docker del backend
├── docker-compose.yml               # Orquestacion backend + frontend
├── .env                             # Variables de entorno (no versionado)
├── .env.example                     # Plantilla del .env
│
├── app/
│   ├── __init__.py                  # Factory de Flask: blueprints, CORS
│   ├── config/settings.py           # Lee/escribe config/config.json
│   ├── routes/
│   │   ├── main.py                  # Endpoints publicos
│   │   ├── admin.py                 # Endpoints admin + entrenamiento
│   │   └── captura.py               # Captura de dataset desde browser
│   └── services/
│       ├── detector.py              # MediaPipe: normaliza landmarks + quiralidad
│       ├── predictor.py             # Carga model.pkl y realiza predicciones
│       ├── metricas.py              # Lee/escribe logs/historial.json
│       └── telegram_bot.py          # Envia mensajes a la API de Telegram
│
├── frontend/
│   ├── Dockerfile                   # Build Vite + Nginx
│   ├── vite.config.js               # Proxy /api y /admin -> backend :5000
│   └── src/
│       ├── App.vue                  # Layout con navbar
│       ├── router/index.js          # Rutas: / y /admin
│       └── views/
│           ├── VistaUsuario.vue     # Pantalla principal del usuario
│           └── VistaAdmin.vue       # Panel de administracion
│
├── dataset/
│   ├── dataset.csv                  # 5000 muestras: 63 features + etiqueta
│   └── evidencia/                   # Capturas de pantalla por clase
│
├── modelo/
│   ├── model.pkl                    # Modelo SVM RBF serializado
│   ├── label_encoder.pkl            # LabelEncoder para decodificar predicciones
│   └── reporte_metricas.txt         # Accuracy, F1, matriz de confusion
│
├── config/config.json               # Configuracion activa del sistema
├── logs/historial.json              # Registro de detecciones
└── docs/
    ├── manual_tecnico.md
    └── manual_usuario.md
```

---

## 4. Pipeline de Machine Learning

### 4.1 Extraccion de caracteristicas

MediaPipe Hands detecta 21 landmarks tridimensionales (x, y, z). El proceso en `detector.py`:

1. **Centrar en muneca**: restar landmark 0, invariante a posicion en el frame.
2. **Normalizar escala**: dividir por distancia maxima, invariante al tamano de la mano.
3. **Normalizar quiralidad**: si el pulgar (landmark 1) tiene `x > 0`, invertir todos los x. Hace el descriptor identico independiente de si el frame esta volteado o de que mano usa el usuario.
4. **Aplanar**: matriz 21×3 -> vector de 63 valores.

```python
puntos -= puntos[0]                    # centrar en muneca
puntos /= np.max(np.abs(puntos))       # normalizar escala
if puntos[1][0] > 0:                   # normalizar quiralidad
    puntos[:, 0] *= -1
return puntos.flatten().tolist()       # 63 features
```

### 4.2 Dataset

| Parametro | Valor |
|-----------|-------|
| Formato | CSV: columna `clase` + 63 columnas de landmarks (x0..z20) |
| Clases | hola, si, no, tu, yo, excelente, te_amo, igual, nombre, mucho |
| Muestras por clase | 500 |
| Total | 5,000 filas |
| Captura | Panel Admin del sistema via getUserMedia del navegador |

La captura se hace desde el panel web (ruta `/admin/capturar_frame`). El admin selecciona la clase y el frontend envia frames JPEG en base64 al backend cada 100ms. El backend procesa con MediaPipe y guarda los landmarks normalizados en el CSV.

### 4.3 Entrenamiento

Se lanzan 4 algoritmos en paralelo y se selecciona el de mayor accuracy en cross-validation 5-fold:

| Algoritmo | Parametros | Accuracy CV |
|-----------|-----------|-------------|
| KNN | k=5 | 99.90% |
| **SVM RBF** | **C=10, gamma='scale'** | **99.98%** |
| Random Forest | 150 arboles | 100.00% |
| Regresion Logistica | max_iter=1000 | 99.90% |

El modelo ganador (SVM RBF) se guarda en `modelo/model.pkl`.

### 4.4 Inferencia en tiempo real

El hilo de camara (`_hilo_camara`) corre a ~30 fps:

```
frame BGR
   -> detector.procesar_frame()  -> vector 63 features
   -> predictor.predecir()       -> clase + confianza
   -> si confianza >= umbral: mostrar prediccion
   -> cv2.flip(frame_anotado, 1) -> stream espejo para el usuario
```

---

## 5. Flujo de envio a Telegram

```
Usuario hace sena -> sistema detecta clase + confianza
   -> clic en "Enviar a Telegram"
   -> POST /api/enviar_telegram { mensaje, sena, confianza }
   -> telegram_bot.py llama api.telegram.org/bot{TOKEN}/sendMessage
   -> mensaje llega al chat configurado (chat_id en config.json)
```

---

## 6. Configuracion (config.json)

```json
{
  "umbral_confianza": 0.70,
  "senas_disponibles": ["hola", "si", "no", "tu", "yo",
                         "excelente", "te_amo", "igual", "nombre", "mucho"],
  "formato_mensaje": "Deteccion HandTalk AI:\nSena: {sena}\nConfianza: {confianza:.0%}",
  "telegram_activo": true,
  "telegram_chat_id": "885855465",
  "historial_habilitado": true,
  "max_historial": 200
}
```

Los cambios se aplican sin reiniciar el servidor. Se editan desde el Panel Admin o directamente en el archivo.

---

## 7. Variables de entorno (.env)

| Variable | Descripcion | Valor por defecto |
|----------|-------------|-------------------|
| `TELEGRAM_TOKEN` | Token del bot de Telegram | (ver .env.example) |
| `ADMIN_USER` | Usuario del panel admin | `admin` |
| `ADMIN_PASSWORD` | Contrasena del panel admin | `handtalk2026` |
| `CAMERA_INDEX` | Indice de camara a usar | `0` |
| `DISABLE_CAMERA` | Si `true`, no abre camara (modo cloud) | `false` |

---

## 8. Contenerizacion con Docker

### Levantar en local

```bash
git clone https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2
cd IA1_1S2026_G12_Proyecto2/HandTalkAI
cp .env.example .env
docker compose up --build
```

Acceder en: `http://localhost:5173` — admin en `http://localhost:5173/#/admin`

### Levantar en GCP (sin camara)

```bash
export DISABLE_CAMERA=true
docker compose up -d
```

Con `DISABLE_CAMERA=true` el hilo de camara no intenta abrir ningun dispositivo. La captura del dataset y todo lo demas funciona normalmente via browser.

---

## 9. Como agregar una nueva sena

1. Panel Admin -> "Captura de dataset" -> elegir nombre de nueva clase
2. Capturar 100-500 muestras con la nueva sena frente a la camara
3. Panel Admin -> "Entrenamiento" -> clic en "Entrenar modelo"
4. El sistema actualiza automaticamente `config.json` con la nueva clase

---

## 10. Tecnologias utilizadas

| Capa | Tecnologia | Version |
|------|-----------|---------|
| Deteccion de mano | MediaPipe Hands | 0.10.21 |
| Vision por computadora | OpenCV | 4.11.0 |
| Machine Learning | scikit-learn | 1.8.0 |
| Backend API | Flask + flask-cors | 3.1.3 |
| Frontend | Vue 3 + Vite | 3.x / 6.x |
| Contenedores | Docker + Docker Compose | 28.x |
| Bot mensajeria | Telegram Bot API | REST |

---

## 11. Diagramas

### Diagrama de flujo — Deteccion en tiempo real

```
  Camara (cv2.VideoCapture)
          |
          v
  MediaPipe Hands detecta 21 puntos (x, y, z)
          |
          v
  Normalizacion de landmarks:
    1. Centrar en muneca (restar landmark 0)
    2. Normalizar escala (dividir por max distancia)
    3. Normalizar quiralidad (invertir x si pulgar > 0)
    -> vector de 63 features
          |
          v
  SVM RBF predice clase + confianza
          |
          v
  confianza >= 0.70?
    SI -> mostrar sena en stream y en UI
    NO -> mostrar "Analizando..."
          |
          v (usuario decide enviar)
  POST /api/enviar_telegram
          |
          v
  Telegram API -> mensaje al chat configurado
```

### Diagrama de flujo — Entrenamiento

```
  Panel Admin: clic "Entrenar modelo"
          |
          v
  Leer dataset.csv (5000 filas, 63 features)
          |
          v
  Cross-validation 5-fold para 4 algoritmos:
    KNN / SVM RBF / Random Forest / Regresion Logistica
          |
          v
  Seleccionar mejor accuracy
          |
          v
  Entrenar en dataset completo
          |
          v
  Guardar model.pkl + label_encoder.pkl + reporte_metricas.txt
          |
          v
  Recargar predictor.py en caliente (sin reiniciar Flask)
```
