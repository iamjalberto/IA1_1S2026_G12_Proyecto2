# Manual Tecnico - HandTalk AI

**Proyecto 2 - Inteligencia Artificial 1**  
**Universidad San Carlos de Guatemala - Facultad de Ingenieria**  
**Grupo 12 | Jose Alberto Alarcon Chigua | 201346084**

---

## 1. Descripcion general del sistema

HandTalk AI es un sistema de reconocimiento de senas del lenguaje LENSEGUA en tiempo real. Captura video desde una camara web, detecta la mano del usuario con MediaPipe, extrae 63 caracteristicas numericas (landmarks normalizados) y las clasifica con un modelo de Machine Learning entrenado con scikit-learn. El resultado se muestra en una interfaz Vue 3 y puede enviarse a un grupo de Telegram.

---

## 2. Arquitectura general

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Navegador)                      │
│                    Vue 3 + Vite  :5173                          │
│   VistaUsuario.vue          VistaAdmin.vue                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │  HTTP (proxy Vite → Flask)
┌──────────────────────▼──────────────────────────────────────────┐
│                     BACKEND (Flask :5000)                       │
│                                                                 │
│  /video_feed  ←── MJPEG stream (hilo de camara)                 │
│  /api/estado  ←── ultima prediccion                             │
│  /api/senas   ←── lista de clases disponibles                   │
│  /api/enviar_telegram  ←── envia mensaje al bot                 │
│  /api/registrar_sena   ←── guarda en historial                  │
│  /admin/*     ←── configuracion y metricas                      │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ detector.py │  │predictor.py  │  │ telegram_bot.py     │    │
│  │ (MediaPipe) │  │ (model.pkl)  │  │ (requests HTTP API) │    │
│  └──────┬──────┘  └──────┬───────┘  └─────────────────────┘    │
└─────────┼────────────────┼─────────────────────────────────────┘
          │                │
┌─────────▼────────────────▼─────────────────────────────────────┐
│                    CAMARA WEB (OpenCV)                          │
└─────────────────────────────────────────────────────────────────┘

  Bot de Telegram: Cloudflare Worker (handtalk-ai-bot)
  URL: https://handtalk-ai-bot.iam-289.workers.dev
```

---

## 3. Descripcion de archivos y carpetas

### Raiz del proyecto

| Archivo | Descripcion |
|---------|-------------|
| `main.py` | Entry point del backend Flask. Inicia el hilo de camara y arranca el servidor |
| `requirements.txt` | Dependencias Python del proyecto |
| `Dockerfile` | Imagen Docker del backend |
| `docker-compose.yml` | Orquestacion de backend + frontend |
| `.env` | Variables de entorno locales (no se sube al repo) |
| `.env.example` | Plantilla del .env para nuevos desarrolladores |

### `app/`

| Archivo | Descripcion |
|---------|-------------|
| `__init__.py` | Factory de Flask: registra blueprints y habilita CORS |
| `config/settings.py` | Lee y escribe `config/config.json`. Contiene valores por defecto |
| `routes/main.py` | Blueprint principal: stream MJPEG, estado, envio a Telegram, senas disponibles |
| `routes/admin.py` | Blueprint admin: config, metricas, historial, info del modelo |
| `services/detector.py` | Inicializa MediaPipe Hands, normaliza landmarks, dibuja anotaciones |
| `services/predictor.py` | Carga `model.pkl` de forma lazy y realiza predicciones |
| `services/metricas.py` | Lee y escribe `logs/historial.json` con cada deteccion registrada |
| `services/telegram_bot.py` | Envia mensajes de texto a la API de Telegram via HTTP |

### `scripts/`

| Archivo | Descripcion |
|---------|-------------|
| `capturar_dataset.py` | Herramienta interactiva para grabar el dataset con la camara |
| `entrenar_modelo.py` | Entrena 4 algoritmos, selecciona el mejor y guarda `model.pkl` |
| `demo_tarea4.py` | Demo standalone sin Flask para probar la deteccion rapida |

### `frontend/`

| Archivo | Descripcion |
|---------|-------------|
| `src/views/VistaUsuario.vue` | Vista principal: stream MJPEG, prediccion, captura de senas, envio a Telegram |
| `src/views/VistaAdmin.vue` | Panel admin: configuracion, metricas, historial, info del modelo |
| `src/App.vue` | Layout principal con navbar y router-view |
| `src/router/index.js` | Rutas: `/` → VistaUsuario, `/admin` → VistaAdmin |
| `vite.config.js` | Proxy de Vite: redirige `/api`, `/admin`, `/video_feed` al backend Flask |
| `Dockerfile` | Imagen Docker del frontend |

### `worker/`

| Archivo | Descripcion |
|---------|-------------|
| `src/index.ts` | Bot de Telegram: comandos /hola, /hora, /contacto, /proyecto, /senas, /ayuda |
| `wrangler.toml` | Configuracion de Cloudflare Workers (nombre: handtalk-ai-bot) |
| `package.json` | Dependencias del worker (grammy, @cloudflare/workers-types) |

### `dataset/`, `modelo/`, `logs/`, `config/`

| Carpeta | Contenido |
|---------|-----------|
| `dataset/dataset.csv` | Landmarks normalizados de cada muestra: 63 columnas + etiqueta |
| `modelo/model.pkl` | Modelo entrenado serializado con pickle |
| `modelo/label_encoder.pkl` | LabelEncoder de scikit-learn para decodificar predicciones |
| `modelo/reporte_metricas.txt` | Accuracy, precision, recall, F1 y matriz de confusion |
| `logs/historial.json` | Registro de todas las detecciones con timestamp y confianza |
| `config/config.json` | Configuracion activa del sistema (editada desde el panel admin) |

---

## 4. Pipeline de Machine Learning

### 4.1 Extraccion de caracteristicas

MediaPipe Hands detecta 21 landmarks tridimensionales (x, y, z) de la mano. El proceso de normalizacion en `detector.py` es:

1. Restar la posicion de la muneca (landmark 0) para centrar todos los puntos
2. Dividir entre la distancia maxima para normalizar la escala
3. Aplanar la matriz 21x3 en un vector de 63 valores

Este enfoque hace que las caracteristicas sean invariantes a la posicion de la mano en el frame y al tamano (distancia a la camara).

### 4.2 Dataset

- Formato: CSV con columnas `landmark_0` ... `landmark_62`, `clase`
- 10 clases: hola, gracias, si, no, ayuda, agua, bien, mal, por_favor, casa
- 100 muestras por clase (1000 filas en total)

### 4.3 Entrenamiento

El script `entrenar_modelo.py` prueba 4 algoritmos:

| Algoritmo | Parametros principales |
|-----------|----------------------|
| KNN | k=5, distancia euclidiana |
| SVM RBF | C=10, kernel RBF, probability=True |
| Random Forest | 150 arboles, random_state=42 |
| Regresion Logistica | max_iter=1000, C=1.0 |

Se selecciona el de mayor accuracy en el conjunto de prueba (80/20 split). El modelo ganador se guarda como `model.pkl`.

---

## 5. API REST del backend

### Endpoints publicos (usuario)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/video_feed` | Stream MJPEG de la camara con anotaciones |
| GET | `/api/estado` | `{ sena_actual, confianza_actual, mano_detectada, modelo_listo }` |
| GET | `/api/senas` | `{ senas: [...] }` lista de clases disponibles |
| POST | `/api/registrar_sena` | Guarda una deteccion en el historial |
| POST | `/api/enviar_telegram` | Envia `{ mensaje }` al bot de Telegram |
| GET | `/api/salud` | Health check: `{ estado: "ok", modelo_listo }` |

### Endpoints admin

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/admin/` | Config actual + resumen de metricas + estado del modelo |
| POST | `/admin/config` | Actualiza campos de configuracion |
| GET | `/admin/metricas` | Estadisticas agregadas del historial |
| GET | `/admin/historial?limite=N` | Ultimas N detecciones |
| POST | `/admin/limpiar_historial` | Borra el historial completo |
| GET | `/admin/modelo_info` | Disponibilidad del modelo y reporte de metricas |

---

## 6. Configuracion del sistema (config.json)

```json
{
  "umbral_confianza": 0.70,
  "senas_disponibles": ["hola", "gracias", ...],
  "formato_mensaje": "Deteccion HandTalk AI:\nSena: {sena}\nConfianza: {confianza:.0%}",
  "telegram_activo": false,
  "telegram_chat_id": "",
  "historial_habilitado": true,
  "max_historial": 200
}
```

Para cambiar el comportamiento del sistema sin tocar codigo, editar estos valores desde el Panel Admin en `/admin` o directamente en `config/config.json`.

---

## 7. Bot de Telegram

El bot `@IA1_G12_bot` corre como Cloudflare Worker en `https://handtalk-ai-bot.iam-289.workers.dev`. Funciona con webhook: Telegram envia cada mensaje al Worker, que responde y termina (no hay proceso permanente).

### Como modificar el bot

```bash
cd worker/
# Editar src/index.ts con los cambios
wrangler deploy
```

### Como agregar un nuevo comando

```typescript
bot.command("nuevo_comando", async (ctx) => {
  await ctx.reply("Respuesta del nuevo comando");
});
```

### Como enviar mensajes desde el backend al grupo

El backend usa `telegram_bot.py` que llama directamente a la API REST de Telegram `sendMessage`. Para que funcione:

1. El usuario agrega `@IA1_G12_bot` a un grupo de Telegram
2. Envia `/start` en el grupo para obtener el Chat ID
3. Configura el Chat ID en el Panel Admin y activa "Envio a Telegram"

---

## 8. Contenerizacion con Docker

### Construir y levantar

```bash
# Levantar todo el sistema
docker-compose up --build

# Solo el backend
docker build -t handtalk-backend .
docker run -p 5000:5000 --device /dev/video0 handtalk-backend
```

### Variables de entorno en Docker

El `docker-compose.yml` carga el archivo `.env` automaticamente. Asegurarse de que `.env` exista antes de hacer `docker-compose up`.

### Camara en Docker

El contenedor necesita acceso al dispositivo de camara. Si la camara no es `/dev/video0`, editar el campo `devices` en `docker-compose.yml`:

```yaml
devices:
  - "/dev/video2:/dev/video0"  # si tu camara es /dev/video2
```

---

## 9. Como extender el sistema

### Agregar una nueva sena

1. Editar `CLASES` en `scripts/capturar_dataset.py` agregando el nombre de la sena
2. Grabar muestras con `python scripts/capturar_dataset.py`
3. Reentrenar el modelo: `python scripts/entrenar_modelo.py`
4. Actualizar `senas_disponibles` en `config/config.json` (o desde el Panel Admin)
5. Actualizar la lista `SENAS_DISPONIBLES` en `worker/src/index.ts` y redesplegar

### Cambiar el algoritmo de ML

En `scripts/entrenar_modelo.py`, modificar el diccionario `candidatos` dentro de `main()`. Agregar o quitar algoritmos de scikit-learn. El script siempre selecciona el de mejor accuracy automaticamente.

### Cambiar el umbral de confianza

Desde el Panel Admin en la interfaz web, o editando `umbral_confianza` en `config/config.json`. Rango recomendado: 0.60 - 0.90.

---

## 10. Dependencias

### Python (`requirements.txt`)

| Libreria | Version | Uso |
|---------|---------|-----|
| flask | 3.1.3 | Framework web del backend |
| flask-cors | 5.0.1 | Habilita CORS para el frontend |
| opencv-python | 4.11.0.86 | Captura de camara y procesamiento de imagen |
| mediapipe | 0.10.21 | Deteccion de landmarks de la mano |
| scikit-learn | 1.8.0 | Entrenamiento y prediccion del modelo |
| numpy | - | Operaciones con arrays de landmarks |
| python-dotenv | - | Carga del archivo .env |
| requests | - | Llamadas a la API de Telegram |

### Node.js (worker)

| Paquete | Version | Uso |
|---------|---------|-----|
| grammy | ^1.30.0 | Framework del bot de Telegram |
| @cloudflare/workers-types | ^4.0.0 | Tipos TypeScript para Cloudflare Workers |
