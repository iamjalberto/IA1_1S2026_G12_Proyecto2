# Manual de Usuario — HandTalk AI

**Proyecto 2 — Inteligencia Artificial 1**
**Universidad San Carlos de Guatemala — Facultad de Ingenieria**
**Grupo 12 | Jose Alberto Alarcon Chigua | 201346084**

---

## Que es HandTalk AI?

HandTalk AI es un sistema que reconoce senas del lenguaje LENSEGUA en tiempo real usando la camara web. Coloca tu mano frente a la camara, realiza una de las senas disponibles, y el sistema la identifica automaticamente mostrando el resultado en pantalla. Luego puedes enviar el mensaje detectado a un grupo de Telegram con un solo clic.

---

## Requisitos

- Computadora con camara web
- Docker instalado (`docker compose` disponible)
- Conexion a internet (para el bot de Telegram)
- Navegador web moderno (Chrome o Firefox recomendado)

---

## Instalacion con Docker (recomendada)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2
cd IA1_1S2026_G12_Proyecto2/HandTalkAI
```

### Paso 2: Configurar variables de entorno

```bash
cp .env.example .env
```

El archivo `.env` ya incluye el token del bot del proyecto. No es necesario modificarlo a menos que uses un bot diferente.

### Paso 3: Levantar el sistema

```bash
docker compose up --build
```

La primera vez tarda unos minutos mientras descarga las imagenes. Las veces siguientes es mas rapido.

### Paso 4: Abrir la aplicacion

Abre tu navegador y entra a: **http://localhost:5173**

---

## Pantalla principal — Vista de usuario

Al abrir la aplicacion veras la pantalla principal con tres secciones:

### Panel izquierdo — Camara en vivo

- Muestra el video de la camara con los landmarks de la mano detectados
- El sistema detecta automaticamente si hay una mano en el cuadro
- Si detecta una sena, la muestra en la parte inferior del video con el porcentaje de confianza

### Panel central — Deteccion

Aqui se muestra en grande la sena que el sistema esta detectando en este momento, junto con su nivel de confianza (0% a 100%).

Cuando el nivel de confianza supere el umbral configurado (por defecto 70%), la sena se muestra claramente. Si la confianza es baja, el sistema muestra "Analizando...".

**Como usar el detector:**

1. Coloca tu mano derecha frente a la camara
2. Realiza una de las senas disponibles (ver lista abajo)
3. Mantente a una distancia de 30 a 60 cm de la camara
4. El sistema detecta la sena automaticamente

### Panel derecho — Acciones

- **Enviar a Telegram**: Envia la sena detectada actualmente al grupo de Telegram configurado
- **Historial**: Muestra las ultimas detecciones realizadas (hora, sena, confianza)
- **Lista de senas**: Muestra todas las senas que el sistema puede reconocer con su descripcion

---

## Senas disponibles

| Sena | Como hacerla |
|------|-------------|
| **hola** | Abre la mano con los 5 dedos extendidos y agitala de un lado a otro a la altura del hombro |
| **si** | Cierra la mano en puno y muevela arriba y abajo, como asintiendo |
| **no** | Extiende el indice y el medio juntos y muevelos de un lado a otro horizontalmente |
| **tu** | Extiende el indice y apunta directamente hacia adelante |
| **yo** | Extiende el indice y apunta hacia tu propio pecho |
| **excelente** | Extiende el pulgar hacia arriba con el resto de dedos cerrados (thumbs up) |
| **te_amo** | Extiende el pulgar, el indice y el menique al mismo tiempo, manteniendo el medio y el anular doblados |
| **igual** | Extiende el indice y el medio en forma de V (signo de la paz) apuntando hacia adelante |
| **nombre** | Forma una N con la mano tocando los dos primeros nudillos contra la frente |
| **mucho** | Junta las dos manos frente al pecho y separalas hacia los lados, indicando amplitud |

> El sistema funciona con cualquier mano (derecha o izquierda).

---

## Enviar un mensaje a Telegram

Para que el envio funcione, el bot debe estar configurado en el Panel Admin (ver seccion siguiente). Una vez configurado:

1. Realiza una sena frente a la camara
2. Espera a que el sistema la detecte con confianza alta
3. Haz clic en **"Enviar a Telegram"**
4. El mensaje llegara al grupo de Telegram configurado

El formato del mensaje enviado es:
```
Deteccion HandTalk AI:
Sena: hola
Confianza: 95%
```

---

## Panel de Administracion

Para acceder al panel de administracion, haz clic en **"Admin"** en la barra de navegacion superior o entra a `http://localhost:5173/#/admin`.

**Credenciales por defecto:**
- Usuario: `admin`
- Contrasena: `handtalk2026`

### Configuracion del sistema

Desde la pestana "Configuracion" puedes ajustar:

| Opcion | Descripcion | Valor recomendado |
|--------|-------------|-------------------|
| Umbral de confianza | Confianza minima para mostrar una prediccion | 70% |
| Formato del mensaje | Como se formatea el mensaje de Telegram | (predefinido) |
| Chat ID de Telegram | ID del grupo donde se enviaran los mensajes | (el de tu grupo) |
| Bot de Telegram activo | Activa o desactiva el envio | Activado |

Despues de cambiar valores, haz clic en **"Guardar cambios"**.

### Metricas de uso

Muestra estadisticas del sistema:
- Total de detecciones realizadas
- Mensajes enviados a Telegram
- Confianza promedio
- Detecciones por sena

### Historial

Lista de las detecciones recientes con hora, sena detectada, confianza y si se envio a Telegram. Se puede limpiar desde este panel.

### Modelo

Muestra el reporte del modelo de Machine Learning entrenado: exactitud por clase, matriz de confusion y comparacion de los 4 algoritmos probados.

### Captura de dataset

Permite capturar nuevas muestras de senas directamente desde el navegador (sin necesitar acceso al servidor):

1. Selecciona la sena que quieres capturar en el campo "Clase"
2. Coloca tu mano frente a la camara del computador
3. Haz clic en "Iniciar captura" y mantente haciendo la sena
4. El sistema captura automaticamente hasta 500 muestras
5. Repite para cada sena

### Entrenamiento

Despues de capturar el dataset, puedes entrenar el modelo:

1. Haz clic en **"Entrenar modelo"**
2. Espera mientras el sistema prueba 4 algoritmos (barra de progreso)
3. Al terminar se muestra el accuracy obtenido
4. El modelo nuevo se carga automaticamente sin reiniciar

---

## Como configurar el bot de Telegram

### Agregar el bot a un grupo

1. Crea un grupo en Telegram o usa uno existente
2. Agrega el bot **@IA1_G12_bot** al grupo
3. El bot ya esta configurado con el chat del grupo del proyecto

### Para usar un grupo propio

1. Agrega **@IA1_G12_bot** a tu grupo
2. Envia cualquier mensaje en el grupo
3. Abre en el navegador: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Busca el campo `"chat" -> "id"` — ese es tu Chat ID
5. Ve al Panel Admin -> Configuracion -> pega el Chat ID y guarda

### Comandos disponibles del bot

Puedes escribirle directamente al bot en Telegram:

| Comando | Que hace |
|---------|---------|
| `/hola` | El bot te responde con un saludo |
| `/hora` | Muestra la hora actual |
| `/senas` | Lista las senas que reconoce el sistema |
| `/ayuda` | Muestra todos los comandos disponibles |

---

## Preguntas frecuentes

**El sistema no detecta mi mano**
- Asegurate de tener buena iluminacion
- Mantente a 30-60 cm de la camara
- Asegurate de que el fondo no sea muy similar al color de tu mano
- Verifica que la camara este activa (icono verde en la barra del navegador)

**La sena se detecta pero con poca confianza**
- Intenta hacer el gesto mas claro y definido
- Mueve un poco la mano hasta encontrar el angulo donde la confianza suba
- Puedes bajar el umbral de confianza en el Panel Admin si necesitas

**El boton "Enviar a Telegram" no funciona**
- Verifica en el Panel Admin que el bot este activado
- Verifica que el Chat ID este configurado correctamente
- El Chat ID de grupos de Telegram generalmente es un numero negativo

**No veo imagen de la camara**
- Si el sistema esta en un servidor remoto (GCP), la camara del servidor puede no estar disponible — el stream estaria inactivo pero el resto del sistema funciona
- En local, verifica que Docker tenga permiso para acceder a la camara

---

## Captura de pantalla de la interfaz

La interfaz principal muestra:

```
┌────────────────────────────────────────────────────────────┐
│  HandTalk AI              [Vista Usuario]  [Admin]         │
├─────────────────────────┬──────────────────────────────────┤
│                         │                                  │
│   [VIDEO EN VIVO]       │   Deteccion actual:              │
│   con landmarks         │                                  │
│   de la mano            │       HOLA                       │
│                         │       Confianza: 95%             │
│                         │                                  │
│                         │   [Enviar a Telegram]            │
│                         │                                  │
├─────────────────────────┴──────────────────────────────────┤
│  Historial de mensajes                  Lista de senas     │
│  15:32  hola    95%  ✓                  hola               │
│  15:30  si      88%  ✓                  si                 │
│  15:28  excelente 91% -                 no  ...            │
└────────────────────────────────────────────────────────────┘
```
