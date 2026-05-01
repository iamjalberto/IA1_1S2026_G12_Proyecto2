# Manual de Usuario - HandTalk AI

**Proyecto 2 - Inteligencia Artificial 1**  
**Universidad San Carlos de Guatemala - Facultad de Ingenieria**  
**Grupo 12 | Jose Alberto Alarcon Chigua | 201346084**

---

## Que es HandTalk AI?

HandTalk AI es un sistema que reconoce senas del lenguaje de senas LENSEGUA en tiempo real usando tu camara web. Coloca tu mano frente a la camara, realiza una sena, y el sistema la identifica automaticamente. Luego puedes enviar el mensaje detectado a un grupo de Telegram.

---

## Requisitos antes de comenzar

- Computadora con camara web
- Python 3.10 o superior instalado
- Node.js 18 o superior instalado
- Conexion a internet (para el bot de Telegram)

---

## Parte 1: Instalacion del sistema

### Paso 1: Clonar el repositorio

Abre una terminal y ejecuta:

```bash
git clone https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2
cd IA1_1S2026_G12_Proyecto2/HandTalkAI
```

### Paso 2: Crear el entorno virtual de Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> En Windows usar: `.venv\Scripts\activate`

### Paso 3: Instalar dependencias Python

```bash
pip install -r requirements.txt
```

### Paso 4: Configurar el token de Telegram

```bash
cp .env.example .env
```

El archivo `.env` ya viene configurado con el token del bot del proyecto. No necesitas modificarlo a menos que uses un bot diferente.

### Paso 5: Instalar dependencias del frontend

```bash
cd frontend
npm install
cd ..
```

---

## Parte 2: Preparar el modelo (primera vez)

Antes de usar el sistema necesitas grabar el dataset y entrenar el modelo. Este proceso se hace una sola vez.

### Paso 1: Grabar el dataset

```bash
python scripts/capturar_dataset.py
```

Aparecera una ventana con la imagen de tu camara. Los controles son:

| Tecla | Accion |
|-------|--------|
| `0` al `9` | Selecciona la sena a grabar (ver lista abajo) |
| `ESPACIO` | Inicia la grabacion automatica de 100 muestras |
| `C` | Cambia de camara (si tienes varias) |
| `Q` | Cierra el programa |

**Lista de senas disponibles:**

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

**Como grabar bien las senas:**
1. Presiona el numero de la sena que quieres grabar
2. Coloca tu mano frente a la camara haciendo la sena
3. Presiona `ESPACIO` — el sistema grabara 100 fotos automaticamente
4. Repite para todas las senas

> Consejo: Varía un poco la posicion de la mano mientras graba (un poco arriba, un poco abajo, girada). Esto hace que el modelo sea mas robusto.

### Paso 2: Entrenar el modelo

```bash
python scripts/entrenar_modelo.py
```

El script prueba 4 algoritmos de Machine Learning y selecciona el mejor automaticamente. Al terminar muestra el accuracy obtenido y guarda:
- `modelo/model.pkl`
- `modelo/label_encoder.pkl`
- `modelo/reporte_metricas.txt`

---

## Parte 3: Usar el sistema

### Paso 1: Iniciar el backend

Abre una terminal y ejecuta:

```bash
source .venv/bin/activate
python main.py
```

Debes ver:
```
* Running on http://0.0.0.0:5000
```

### Paso 2: Iniciar el frontend

Abre **otra terminal** y ejecuta:

```bash
cd frontend
npm run dev
```

Debes ver:
```
  VITE ready in ...
  Local: http://localhost:5173/
```

### Paso 3: Abrir la aplicacion

Abre tu navegador y entra a: **http://localhost:5173**

---

## Parte 4: Usar la interfaz

### Vista principal (Detector)

Al abrir la aplicacion veras dos paneles:

**Panel izquierdo — Camara en tiempo real:**
- Muestra el video de tu camara con la mano detectada
- El punto de color en la esquina indica si hay mano detectada (verde) o no (gris)
- Debajo del video aparece la sena detectada y el porcentaje de confianza

**Panel derecho — Capturar sena:**

1. Coloca tu mano frente a la camara y realiza una sena
2. Espera a que el sistema detecte la sena (aparece en el panel izquierdo)
3. Haz clic en **"Capturar sena"** para agregarla al mensaje
4. Puedes capturar varias senas seguidas para formar un mensaje
5. El mensaje acumulado aparece en el area de texto
6. Cuando el mensaje este listo, haz clic en **"Enviar a Telegram"**

> Para que el envio a Telegram funcione, primero debes configurarlo en el Panel Admin (ver Parte 5).

**Botones disponibles:**
- **Capturar sena**: Agrega la sena actual al mensaje
- **Limpiar**: Borra el mensaje acumulado
- **Enviar a Telegram**: Envia el mensaje al grupo de Telegram configurado

---

### Vista de administracion (Panel Admin)

Para acceder al Panel Admin haz clic en **"Panel Admin"** en la barra de navegacion, o entra a **http://localhost:5173/#/admin**.

El panel tiene 4 pestanas:

#### Pestana "Configuracion"

Aqui puedes ajustar:

- **Umbral de confianza**: Que tan seguro debe estar el sistema antes de mostrar una prediccion (deslizador). Valor recomendado: 70%.
- **Formato del mensaje de Telegram**: Como se formateara el mensaje enviado. Puedes usar `{sena}` y `{confianza}` como variables.
- **Chat ID de Telegram**: El ID del grupo de Telegram donde se enviaran los mensajes.
- **Envio a Telegram**: Activa o desactiva el envio.
- **Guardar cambios**: Aplica la configuracion.

#### Pestana "Metricas"

Muestra estadisticas del uso del sistema:
- Total de detecciones realizadas
- Cuantos mensajes se enviaron a Telegram
- Confianza promedio
- Detecciones por clase

#### Pestana "Historial"

Muestra las ultimas 100 detecciones con timestamp, sena detectada y nivel de confianza. Puedes limpiar el historial con el boton correspondiente.

#### Pestana "Modelo"

Muestra el reporte detallado del modelo entrenado: accuracy por clase, matriz de confusion, y comparacion de algoritmos.

---

## Parte 5: Configurar el bot de Telegram

### Como obtener el Chat ID de tu grupo

1. Crea un grupo en Telegram o usa uno existente
2. Agrega el bot **@IA1_G12_bot** al grupo
3. Envia cualquier mensaje en el grupo
4. Abre este enlace en el navegador (reemplaza TOKEN con el token real):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. Busca el campo `"chat"` → `"id"` en la respuesta. Ese es el Chat ID (puede ser negativo si es un grupo).

### Como configurar el Chat ID en la aplicacion

1. Ve al Panel Admin → pestana "Configuracion"
2. Pega el Chat ID en el campo correspondiente
3. Activa el switch "Envio a Telegram"
4. Guarda los cambios
5. Ahora el boton "Enviar a Telegram" en la vista principal enviara mensajes al grupo

### Comandos del bot (@IA1_G12_bot)

Puedes enviarle comandos directamente al bot en Telegram:

| Comando | Respuesta |
|---------|-----------|
| `/hola` | Saludo personalizado |
| `/hora` | Hora actual en Guatemala |
| `/contacto` | Informacion del grupo |
| `/proyecto` | Descripcion del proyecto y repositorio |
| `/senas` | Lista de senas reconocidas por el sistema |
| `/ayuda` | Lista de todos los comandos disponibles |

---

## Parte 6: Usar con Docker (opcional)

Si prefieres no instalar Python ni Node.js, puedes usar Docker:

### Requisitos

- Docker instalado
- Docker Compose instalado

### Levantar el sistema

```bash
# Desde la carpeta HandTalkAI/
docker-compose up --build
```

Esto inicia automaticamente el backend y el frontend. Espera a que ambos esten listos y abre **http://localhost:5173**.

### Detener el sistema

```bash
docker-compose down
```

---

## Soluciones a problemas comunes

**La camara no se detecta:**
- Verifica que ningun otro programa este usando la camara
- Si tienes varias camaras, presiona `C` en `capturar_dataset.py` para cambiar

**"Modelo no entrenado aun" en la interfaz:**
- Asegura de haber corrido `python scripts/entrenar_modelo.py` y que termino sin errores
- Verifica que existe el archivo `modelo/model.pkl`

**El bot de Telegram no envia mensajes:**
- Verifica que el Chat ID este configurado correctamente en el Panel Admin
- Asegura de que la opcion "Envio a Telegram" este activada
- El bot debe estar agregado al grupo de Telegram

**La prediccion siempre muestra "Analizando..." sin detectar la sena:**
- Baja el umbral de confianza en el Panel Admin (prueba con 50%)
- Asegura de tener buena iluminacion
- Coloca la mano a una distancia media de la camara (ni muy lejos ni muy cerca)

**Error al iniciar el backend:**
- Verifica que el entorno virtual esta activado: `source .venv/bin/activate`
- Verifica que todas las dependencias estan instaladas: `pip install -r requirements.txt`
