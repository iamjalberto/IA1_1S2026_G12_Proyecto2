<template>
  <div class="vista-admin">
    <!-- Pantalla de login — se muestra si no hay sesion activa -->
    <div
      v-if="!autenticado"
      class="card"
      style="max-width: 360px; margin: 60px auto"
    >
      <h2 class="seccion-titulo">Acceso al panel</h2>
      <hr class="separador" />
      <div class="campo-grupo">
        <label>Usuario</label>
        <input
          v-model="loginForm.usuario"
          class="input"
          type="text"
          placeholder="admin"
          @keyup.enter="iniciarSesion"
        />
      </div>
      <div class="campo-grupo">
        <label>Contrasena</label>
        <input
          v-model="loginForm.contrasena"
          class="input"
          type="password"
          placeholder="..."
          @keyup.enter="iniciarSesion"
        />
      </div>
      <p
        v-if="loginError"
        style="color: #e05252; font-size: 13px; margin-top: 6px"
      >
        {{ loginError }}
      </p>
      <button
        class="btn btn--primario"
        style="margin-top: 14px; width: 100%"
        @click="iniciarSesion"
      >
        Ingresar
      </button>
    </div>

    <!-- Panel principal — solo visible cuando hay sesion -->
    <template v-else>
      <div
        style="
          margin-bottom: 20px;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        "
      >
        <div>
          <h1 style="font-size: 22px; font-weight: 700">
            Panel de Administracion
          </h1>
          <p
            style="color: var(--texto-suave); font-size: 14px; margin-top: 4px"
          >
            Configuracion y monitoreo del sistema HandTalk AI
          </p>
        </div>
        <button
          class="btn"
          style="font-size: 13px; padding: 6px 14px"
          @click="cerrarSesion"
        >
          Cerrar sesion
        </button>
      </div>

      <!-- Tabs de navegacion interna -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab"
          :class="{ 'tab--activa': tabActiva === tab.id }"
          @click="tabActiva = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- TAB: Configuracion -->
      <div v-show="tabActiva === 'config'" class="card">
        <h2 class="seccion-titulo">Parametros del sistema</h2>
        <hr class="separador" />

        <div class="campo-grupo">
          <label
            >Umbral de confianza ({{
              (config.umbral_confianza * 100).toFixed(0)
            }}%)</label
          >
          <input
            type="range"
            min="0.3"
            max="0.99"
            step="0.01"
            v-model.number="config.umbral_confianza"
            style="width: 100%; accent-color: var(--azul)"
          />
          <p class="campo-hint">
            Solo se aceptan predicciones con confianza mayor a este valor.
          </p>
        </div>

        <div class="campo-grupo">
          <label>Formato del mensaje de Telegram</label>
          <textarea
            v-model="config.formato_mensaje"
            rows="3"
            placeholder="Ej: Deteccion HandTalk AI: {sena} ({confianza})"
          ></textarea>
          <p class="campo-hint">
            Usa {sena} y {confianza} como variables dinamicas.
          </p>
        </div>

        <div class="campo-grupo">
          <label>Chat ID de Telegram</label>
          <input
            type="text"
            v-model="config.telegram_chat_id"
            placeholder="-1001234567890"
          />
          <p class="campo-hint">
            ID del grupo o canal donde se enviaran los mensajes.
          </p>
        </div>

        <div class="campo-grupo">
          <label>Envio a Telegram</label>
          <div class="toggle-fila">
            <span>{{
              config.telegram_activo ? "Activado" : "Desactivado"
            }}</span>
            <button
              class="toggle-btn"
              :class="{ activo: config.telegram_activo }"
              @click="config.telegram_activo = !config.telegram_activo"
            >
              <div class="toggle-circulo"></div>
            </button>
          </div>
        </div>

        <div class="campo-grupo">
          <label>Historial de detecciones</label>
          <div class="toggle-fila">
            <span>{{
              config.historial_habilitado ? "Habilitado" : "Deshabilitado"
            }}</span>
            <button
              class="toggle-btn"
              :class="{ activo: config.historial_habilitado }"
              @click="
                config.historial_habilitado = !config.historial_habilitado
              "
            >
              <div class="toggle-circulo"></div>
            </button>
          </div>
        </div>

        <hr class="separador" />

        <button
          class="btn btn-azul"
          :disabled="guardando"
          @click="guardarConfig"
        >
          {{ guardando ? "Guardando..." : "Guardar configuracion" }}
        </button>
      </div>

      <!-- TAB: Metricas -->
      <div v-show="tabActiva === 'metricas'" class="card">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
          "
        >
          <h2 class="seccion-titulo">Metricas de desempeno</h2>
          <button
            class="btn btn-gris"
            style="padding: 6px 14px; font-size: 12px"
            @click="cargarMetricas"
          >
            Actualizar
          </button>
        </div>
        <hr class="separador" />

        <div class="metricas-grid">
          <div class="metrica-card">
            <div class="metrica-valor">{{ resumen.total_detecciones }}</div>
            <div class="metrica-label">Total de detecciones</div>
          </div>
          <div class="metrica-card">
            <div class="metrica-valor">
              {{ resumen.total_enviados_telegram }}
            </div>
            <div class="metrica-label">Enviados a Telegram</div>
          </div>
          <div class="metrica-card">
            <div class="metrica-valor">
              {{ (resumen.confianza_promedio * 100).toFixed(1) }}%
            </div>
            <div class="metrica-label">Confianza promedio</div>
          </div>
          <div class="metrica-card">
            <div class="metrica-valor">
              {{ Object.keys(resumen.por_clase || {}).length }}
            </div>
            <div class="metrica-label">Clases detectadas</div>
          </div>
        </div>

        <div
          v-if="Object.keys(resumen.por_clase || {}).length > 0"
          style="margin-top: 20px"
        >
          <h3
            style="
              font-size: 14px;
              font-weight: 600;
              margin-bottom: 12px;
              color: var(--texto-suave);
            "
          >
            Por clase
          </h3>
          <div class="tabla-contenedor">
            <table class="tabla">
              <thead>
                <tr>
                  <th>Seña</th>
                  <th>Detecciones</th>
                  <th>Confianza prom.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(datos, sena) in resumen.por_clase" :key="sena">
                  <td>
                    <span class="badge badge-azul">{{ sena }}</span>
                  </td>
                  <td>{{ datos.total }}</td>
                  <td>
                    <div class="barra-confianza" style="max-width: 120px">
                      <div
                        class="barra-confianza__relleno"
                        :style="{ width: datos.confianza_promedio * 100 + '%' }"
                      ></div>
                    </div>
                    <small
                      >{{ (datos.confianza_promedio * 100).toFixed(1) }}%</small
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div
          v-else
          style="color: var(--texto-suave); font-size: 14px; padding: 20px 0"
        >
          Todavia no hay detecciones registradas.
        </div>
      </div>

      <!-- TAB: Historial -->
      <div v-show="tabActiva === 'historial'" class="card">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
          "
        >
          <h2 class="seccion-titulo">Historial de detecciones</h2>
          <div style="display: flex; gap: 8px">
            <button
              class="btn btn-gris"
              style="padding: 6px 14px; font-size: 12px"
              @click="cargarHistorial"
            >
              Actualizar
            </button>
            <button
              class="btn btn-rojo"
              style="padding: 6px 14px; font-size: 12px"
              @click="limpiarHistorial"
            >
              Limpiar
            </button>
          </div>
        </div>
        <hr class="separador" />

        <div
          v-if="historial.length === 0"
          style="color: var(--texto-suave); font-size: 14px; padding: 20px 0"
        >
          No hay registros en el historial.
        </div>

        <div v-else class="tabla-contenedor">
          <table class="tabla">
            <thead>
              <tr>
                <th>Fecha y hora</th>
                <th>Seña</th>
                <th>Confianza</th>
                <th>Telegram</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(reg, i) in historial" :key="i">
                <td style="color: var(--texto-suave); font-size: 12px">
                  {{ reg.timestamp }}
                </td>
                <td>
                  <span class="badge badge-azul">{{ reg.sena }}</span>
                </td>
                <td>{{ (reg.confianza * 100).toFixed(0) }}%</td>
                <td>
                  <span v-if="reg.enviado_telegram" class="badge badge-verde"
                    >Si</span
                  >
                  <span v-else class="badge badge-gris">No</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- TAB: Modelo -->
      <div v-show="tabActiva === 'modelo'" class="card">
        <h2 class="seccion-titulo">Entrenamiento y modelo</h2>
        <hr class="separador" />

        <!-- Boton de entrenamiento -->
        <div style="margin-bottom: 24px">
          <p
            style="
              font-size: 14px;
              color: var(--texto-suave);
              margin-bottom: 12px;
            "
          >
            Entrena el clasificador con todas las muestras del dataset. Se
            prueban KNN, SVM, Random Forest y Regresion Logistica — se guarda el
            de mayor exactitud.
          </p>
          <button
            class="btn btn--primario"
            @click="iniciarEntrenamiento"
            :disabled="entrenando"
            style="min-width: 200px"
          >
            {{ entrenando ? "Entrenando..." : "Entrenar modelo" }}
          </button>

          <!-- Barra de progreso indeterminada mientras entrena -->
          <div
            v-if="entrenando"
            style="
              margin-top: 12px;
              height: 4px;
              background: #1a1d2a;
              border-radius: 2px;
              overflow: hidden;
              max-width: 400px;
            "
          >
            <div class="barra-entrenando"></div>
          </div>

          <p
            v-if="mensajeEntrenamiento"
            :style="{
              marginTop: '10px',
              fontSize: '13px',
              color: resultadoEntrenamiento === false ? '#e05252' : '#00cc88',
            }"
          >
            {{ mensajeEntrenamiento }}
          </p>
        </div>

        <hr class="separador" />

        <!-- Reporte del modelo actual -->
        <div
          v-if="!reporteModelo.disponible"
          style="color: var(--texto-suave); font-size: 14px; padding: 16px 0"
        >
          No hay modelo entrenado todavia. Usa el boton de arriba para entrenar.
        </div>

        <div v-else>
          <pre
            style="
              background: #1a1d2a;
              padding: 16px;
              border-radius: 8px;
              font-size: 12px;
              line-height: 1.6;
              overflow-x: auto;
              white-space: pre-wrap;
              color: #c8d0e0;
            "
            >{{ reporteModelo.reporte }}</pre
          >
        </div>
      </div>

      <!-- TAB: Senas -->
      <div v-show="tabActiva === 'senas'" class="card">
        <h2 class="seccion-titulo">Gestion de senas disponibles</h2>
        <hr class="separador" />

        <div
          class="campo-grupo"
          style="display: flex; gap: 10px; align-items: flex-end"
        >
          <div style="flex: 1">
            <label>Nueva sena (solo letras, numeros y guion bajo)</label>
            <input
              v-model="nuevaSena"
              class="input"
              type="text"
              placeholder="ej: buenos_dias"
              @keyup.enter="agregarSena"
            />
          </div>
          <button class="btn btn--primario" @click="agregarSena">
            Agregar
          </button>
        </div>

        <div style="margin-top: 20px">
          <p
            style="
              font-size: 13px;
              color: var(--texto-suave);
              margin-bottom: 10px;
            "
          >
            Total: {{ senas.length }} senas registradas
          </p>
          <div
            v-if="senas.length === 0"
            style="color: var(--texto-suave); font-size: 14px"
          >
            No hay senas registradas.
          </div>
          <div
            v-for="sena in senas"
            :key="sena"
            style="
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 10px 14px;
              background: #1a1d2a;
              border-radius: 8px;
              margin-bottom: 8px;
            "
          >
            <div style="display: flex; align-items: center; gap: 10px; flex: 1">
              <span style="font-size: 15px; font-weight: 500">{{ sena }}</span>
              <span style="font-size: 12px; color: var(--texto-suave)">
                {{ progreso[sena] ?? "..." }} / {{ MUESTRAS_MAX }} muestras
              </span>
            </div>
            <div style="display: flex; gap: 6px">
              <button
                class="btn btn--primario"
                style="font-size: 12px; padding: 4px 10px"
                @click="abrirCaptura(sena)"
              >
                Capturar
              </button>
              <button
                class="btn"
                style="font-size: 12px; padding: 4px 10px; color: #e0a052"
                @click="reiniciarMuestras(sena)"
              >
                Reiniciar
              </button>
              <button
                class="btn"
                style="font-size: 12px; padding: 4px 10px; color: #e05252"
                @click="eliminarSena(sena)"
              >
                Eliminar
              </button>
            </div>
          </div>
        </div>

        <!-- Panel de captura — modal overlay -->
        <Teleport to="body">
          <div
            v-if="claseCapturando"
            style="
              position: fixed;
              inset: 0;
              background: rgba(0, 0, 0, 0.82);
              z-index: 1000;
              display: flex;
              align-items: center;
              justify-content: center;
              padding: 16px;
            "
            @keydown.esc.window="cerrarCaptura"
          >
            <div
              style="
                background: #13151f;
                border: 1px solid #2a2d3e;
                border-radius: 16px;
                padding: 28px;
                width: 100%;
                max-width: 700px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
              "
            >
              <!-- Header del modal -->
              <div
                style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  margin-bottom: 20px;
                "
              >
                <h3 style="margin: 0; font-size: 18px">
                  Capturando seña:
                  <span style="color: #0df">{{ claseCapturando }}</span>
                </h3>
                <div style="display: flex; gap: 8px; align-items: center">
                  <select
                    v-if="camarasDisponibles.length > 1"
                    v-model="camaraSeleccionada"
                    class="input"
                    style="font-size: 12px; padding: 4px 8px; height: auto"
                    @change="iniciarStream"
                  >
                    <option
                      v-for="cam in camarasDisponibles"
                      :key="cam.deviceId"
                      :value="cam.deviceId"
                    >
                      {{ cam.label }}
                    </option>
                  </select>
                  <button
                    class="btn"
                    style="font-size: 12px; padding: 4px 12px"
                    @click="cerrarCaptura"
                  >
                    Cerrar (ESC)
                  </button>
                </div>
              </div>

              <div
                style="
                  display: flex;
                  gap: 24px;
                  align-items: flex-start;
                  flex-wrap: wrap;
                "
              >
                <!-- Preview: muestra el frame anotado del servidor (con landmarks) -->
                <div style="position: relative; flex-shrink: 0">
                  <!-- Video oculto: solo sirve para capturar frames al canvas -->
                  <video
                    ref="videoRef"
                    autoplay
                    playsinline
                    muted
                    style="
                      position: absolute;
                      opacity: 0;
                      pointer-events: none;
                      width: 1px;
                      height: 1px;
                    "
                  ></video>
                  <!-- Imagen con el frame anotado por el backend (muestra landmarks) -->
                  <img
                    v-if="framePreview"
                    :src="'data:image/jpeg;base64,' + framePreview"
                    style="
                      width: 320px;
                      border-radius: 10px;
                      display: block;
                      background: #000;
                      border: 2px solid;
                    "
                    :style="{
                      borderColor: deteccionActiva ? '#00ee55' : '#2a2d3e',
                    }"
                  />
                  <div
                    v-else
                    style="
                      width: 320px;
                      height: 240px;
                      border-radius: 10px;
                      background: #0a0b14;
                      border: 2px solid #2a2d3e;
                      display: flex;
                      align-items: center;
                      justify-content: center;
                      color: #555;
                      font-size: 13px;
                    "
                  >
                    Iniciando camara...
                  </div>
                  <!-- Indicador de detección -->
                  <div
                    style="
                      position: absolute;
                      top: 10px;
                      right: 10px;
                      display: flex;
                      align-items: center;
                      gap: 5px;
                      background: rgba(0, 0, 0, 0.65);
                      padding: 3px 8px;
                      border-radius: 20px;
                      font-size: 11px;
                    "
                  >
                    <div
                      :style="{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: deteccionActiva ? '#00ee55' : '#555',
                        boxShadow: deteccionActiva ? '0 0 6px #00ee55' : 'none',
                      }"
                    ></div>
                    <span
                      :style="{ color: deteccionActiva ? '#00ee55' : '#777' }"
                    >
                      {{ deteccionActiva ? "Mano detectada" : "Sin mano" }}
                    </span>
                  </div>
                </div>

                <!-- Controles -->
                <div style="flex: 1; min-width: 180px">
                  <p style="margin: 0 0 6px; font-size: 22px; font-weight: 700">
                    {{ conteoCaptura }}
                    <span style="font-size: 14px; color: var(--texto-suave)"
                      >/ {{ MUESTRAS_MAX }}</span
                    >
                  </p>
                  <!-- Barra de progreso -->
                  <div
                    style="
                      height: 8px;
                      background: #1a1d2a;
                      border-radius: 4px;
                      margin-bottom: 20px;
                      overflow: hidden;
                    "
                  >
                    <div
                      :style="{
                        width:
                          Math.min((conteoCaptura / MUESTRAS_MAX) * 100, 100) +
                          '%',
                        height: '100%',
                        background: '#0df',
                        borderRadius: '4px',
                        transition: 'width 0.2s',
                      }"
                    ></div>
                  </div>

                  <button
                    v-if="!capturaActiva"
                    class="btn btn--primario"
                    style="width: 100%; margin-bottom: 10px; padding: 12px"
                    @click="iniciarCaptura"
                    :disabled="conteoCaptura >= MUESTRAS_MAX"
                  >
                    {{
                      conteoCaptura >= MUESTRAS_MAX
                        ? "Completada"
                        : "Iniciar grabacion"
                    }}
                  </button>
                  <button
                    v-else
                    class="btn"
                    style="
                      width: 100%;
                      margin-bottom: 10px;
                      padding: 12px;
                      color: #e0a052;
                    "
                    @click="detenerCaptura"
                  >
                    Detener
                  </button>

                  <p
                    style="
                      font-size: 12px;
                      color: var(--texto-suave);
                      margin: 0;
                    "
                  >
                    Coloca la mano en el encuadre y presiona Iniciar.<br />
                    El borde verde confirma que el servidor detecta tu mano.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Teleport>
      </div>

      <!-- Toast -->
      <Transition name="toast">
        <div v-if="toast.visible" class="toast" :class="toast.tipo">
          {{ toast.texto }}
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from "vue";

const tabs = [
  { id: "config", label: "Configuracion" },
  { id: "metricas", label: "Metricas" },
  { id: "historial", label: "Historial" },
  { id: "modelo", label: "Modelo" },
  { id: "senas", label: "Senas" },
];

const autenticado = ref(false);
const loginForm = ref({ usuario: "", contrasena: "" });
const loginError = ref("");

const nuevaSena = ref("");
const senas = ref([]);
const progreso = ref({});

// Estado del panel de captura web
const MUESTRAS_MAX = 500;
const videoRef = ref(null);
const claseCapturando = ref(null);
const capturaActiva = ref(false);
const conteoCaptura = ref(0);
const deteccionActiva = ref(false);
const framePreview = ref(""); // frame anotado con landmarks devuelto por el servidor
const camarasDisponibles = ref([]); // lista de { deviceId, label }
const camaraSeleccionada = ref(""); // deviceId activo
let streamCamara = null;
let intervalCaptura = null;

const tabActiva = ref("config");
const guardando = ref(false);
const toast = ref({ visible: false, texto: "", tipo: "exito" });

const config = ref({
  umbral_confianza: 0.7,
  formato_mensaje:
    "Deteccion HandTalk AI:\nSena: {sena}\nConfianza: {confianza}",
  telegram_activo: false,
  telegram_chat_id: "",
  historial_habilitado: true,
});

const resumen = ref({
  total_detecciones: 0,
  total_enviados_telegram: 0,
  confianza_promedio: 0,
  por_clase: {},
});

const historial = ref([]);

const reporteModelo = ref({ disponible: false, reporte: null });

// Estado del entrenamiento
const entrenando = ref(false);
const mensajeEntrenamiento = ref("");
const resultadoEntrenamiento = ref(null);
let pollingEntrenamiento = null;

function mostrarToast(texto, tipo = "exito") {
  toast.value = { visible: true, texto, tipo };
  setTimeout(() => {
    toast.value.visible = false;
  }, 3000);
}

async function cargarDatos() {
  try {
    const res = await fetch("/admin/", { credentials: "include" });
    if (res.ok) {
      const data = await res.json();
      // Solo sobreescribimos los campos que vienen del servidor, preservando ediciones locales
      Object.assign(config.value, data.config);
      resumen.value = data.resumen;
    }
  } catch {
    /* sin conexion */
  }
}

async function cargarMetricas() {
  try {
    const res = await fetch("/admin/metricas", { credentials: "include" });
    if (res.ok) {
      resumen.value = await res.json();
    }
  } catch {
    /* sin conexion */
  }
}

async function cargarHistorial() {
  try {
    const res = await fetch("/admin/historial?limite=100", {
      credentials: "include",
    });
    if (res.ok) {
      historial.value = await res.json();
    }
  } catch {
    /* sin conexion */
  }
}

async function guardarConfig() {
  guardando.value = true;
  try {
    const res = await fetch("/admin/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(config.value),
    });
    const data = await res.json();
    if (data.exito) {
      mostrarToast("Configuracion guardada correctamente", "exito");
    } else {
      mostrarToast("Error al guardar la configuracion", "error");
    }
  } catch {
    mostrarToast("Error de conexion con el backend", "error");
  } finally {
    guardando.value = false;
  }
}

async function limpiarHistorial() {
  if (!confirm("Seguro que quieres limpiar todo el historial?")) return;
  try {
    await fetch("/admin/limpiar_historial", {
      method: "POST",
      credentials: "include",
    });
    historial.value = [];
    resumen.value = {
      total_detecciones: 0,
      total_enviados_telegram: 0,
      confianza_promedio: 0,
      por_clase: {},
    };
    mostrarToast("Historial limpiado", "exito");
  } catch {
    mostrarToast("Error al limpiar el historial", "error");
  }
}

async function cargarModeloInfo() {
  try {
    const res = await fetch("/admin/modelo_info", { credentials: "include" });
    if (res.ok) {
      reporteModelo.value = await res.json();
    }
  } catch {
    /* sin conexion */
  }
}

async function iniciarEntrenamiento() {
  mensajeEntrenamiento.value = "";
  resultadoEntrenamiento.value = null;
  entrenando.value = true;

  try {
    const res = await fetch("/admin/entrenar", {
      method: "POST",
      credentials: "include",
    });
    const data = await res.json();
    if (!data.iniciado) {
      mensajeEntrenamiento.value = data.mensaje;
      entrenando.value = false;
      return;
    }
    // Polling cada 2 segundos hasta que termine
    pollingEntrenamiento = setInterval(async () => {
      try {
        const r = await fetch("/admin/estado_entrenamiento", {
          credentials: "include",
        });
        if (r.ok) {
          const estado = await r.json();
          if (!estado.en_proceso) {
            clearInterval(pollingEntrenamiento);
            pollingEntrenamiento = null;
            entrenando.value = false;
            resultadoEntrenamiento.value = estado.exito;
            mensajeEntrenamiento.value = estado.mensaje;
            if (estado.exito) {
              // Recargar el reporte para mostrar las nuevas metricas
              await cargarModeloInfo();
              mostrarToast("Modelo entrenado correctamente", "exito");
            } else {
              mostrarToast(estado.mensaje, "error");
            }
          }
        }
      } catch {
        // ignorar error de red transitorio
      }
    }, 2000);
  } catch {
    mensajeEntrenamiento.value = "Error de conexion con el servidor";
    entrenando.value = false;
  }
}

async function iniciarSesion() {
  loginError.value = "";
  try {
    const res = await fetch("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(loginForm.value),
    });
    const data = await res.json();
    if (data.exito) {
      autenticado.value = true;
      cargarDatos();
      cargarHistorial();
      cargarModeloInfo();
      cargarSenas();
      cargarProgreso();
    } else {
      loginError.value = data.mensaje || "Credenciales incorrectas";
    }
  } catch {
    loginError.value = "Error de conexion con el servidor";
  }
}

async function cerrarSesion() {
  await fetch("/admin/logout", { method: "POST", credentials: "include" });
  autenticado.value = false;
  loginForm.value = { usuario: "", contrasena: "" };
}

async function cargarSenas() {
  try {
    const res = await fetch("/admin/senas", { credentials: "include" });
    if (res.ok) {
      const data = await res.json();
      senas.value = data.senas;
    }
  } catch {
    /* sin conexion */
  }
}

async function cargarProgreso() {
  try {
    const res = await fetch("/admin/progreso_captura", {
      credentials: "include",
    });
    if (res.ok) {
      const data = await res.json();
      progreso.value = data.progreso;
    }
  } catch {
    /* sin conexion */
  }
}

async function abrirCaptura(sena) {
  // Si se abre otra sena, cerramos la anterior primero
  if (claseCapturando.value && claseCapturando.value !== sena) {
    cerrarCaptura();
  }
  // Si se toca la misma sena, hacer toggle del panel
  if (claseCapturando.value === sena) {
    cerrarCaptura();
    return;
  }
  claseCapturando.value = sena;
  conteoCaptura.value = progreso.value[sena] ?? 0;
  deteccionActiva.value = false;

  await iniciarStream();
}

async function iniciarStream() {
  // Detener stream anterior si existe
  if (streamCamara) {
    streamCamara.getTracks().forEach((t) => t.stop());
    streamCamara = null;
  }
  framePreview.value = "";

  const constraints = camaraSeleccionada.value
    ? { video: { deviceId: { exact: camaraSeleccionada.value } } }
    : { video: true };

  try {
    streamCamara = await navigator.mediaDevices.getUserMedia(constraints);
    await listarCamaras();
    await nextTick();
    if (videoRef.value) {
      videoRef.value.srcObject = streamCamara;
    }
  } catch (e) {
    mostrarToast("No se pudo acceder a la camara: " + e.message, "error");
    claseCapturando.value = null;
    streamCamara = null;
  }
}

async function listarCamaras() {
  try {
    const dispositivos = await navigator.mediaDevices.enumerateDevices();
    camarasDisponibles.value = dispositivos
      .filter((d) => d.kind === "videoinput")
      .map((d, i) => ({
        deviceId: d.deviceId,
        label: d.label || `Camara ${i + 1}`,
      }));
    // Si no hay seleccion y hay camaras, preseleccionar la primera
    if (!camaraSeleccionada.value && camarasDisponibles.value.length > 0) {
      camaraSeleccionada.value = camarasDisponibles.value[0].deviceId;
    }
  } catch {
    /* si falla enumerateDevices, no es critico */
  }
}

function cerrarCaptura() {
  detenerCaptura();
  claseCapturando.value = null;
  framePreview.value = "";
  if (streamCamara) {
    streamCamara.getTracks().forEach((t) => t.stop());
    streamCamara = null;
  }
}

function iniciarCaptura() {
  if (capturaActiva.value || !claseCapturando.value) return;
  if (conteoCaptura.value >= MUESTRAS_MAX) return;
  capturaActiva.value = true;
  intervalCaptura = setInterval(enviarFrame, 100); // ~10fps
}

function detenerCaptura() {
  capturaActiva.value = false;
  if (intervalCaptura) {
    clearInterval(intervalCaptura);
    intervalCaptura = null;
  }
}

async function enviarFrame() {
  if (!capturaActiva.value || !videoRef.value || !claseCapturando.value) return;
  if (conteoCaptura.value >= MUESTRAS_MAX) {
    detenerCaptura();
    progreso.value[claseCapturando.value] = MUESTRAS_MAX;
    mostrarToast(`Captura de '${claseCapturando.value}' completada`, "exito");
    return;
  }

  const canvas = document.createElement("canvas");
  canvas.width = videoRef.value.videoWidth || 320;
  canvas.height = videoRef.value.videoHeight || 240;
  canvas.getContext("2d").drawImage(videoRef.value, 0, 0);
  const frame = canvas
    .toDataURL("image/jpeg", 0.7)
    .replace(/^data:image\/jpeg;base64,/, "");

  try {
    const res = await fetch("/admin/capturar_frame", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ clase: claseCapturando.value, frame }),
    });
    if (res.ok) {
      const data = await res.json();
      deteccionActiva.value = data.detectado;
      // Actualizar el preview con el frame anotado devuelto por el servidor
      if (data.preview) {
        framePreview.value = data.preview;
      }
      if (data.detectado) {
        conteoCaptura.value = data.count;
        progreso.value[claseCapturando.value] = data.count;
      }
      if (data.lleno) {
        detenerCaptura();
        mostrarToast(
          `Captura de '${claseCapturando.value}' completada`,
          "exito",
        );
      }
    }
  } catch {
    // Ignorar errores de red transitorios durante la captura
  }
}

async function reiniciarMuestras(sena) {
  if (!confirm(`Borrar todas las muestras de '${sena}'?`)) return;
  try {
    const res = await fetch(`/admin/borrar_muestras/${sena}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (res.ok) {
      progreso.value[sena] = 0;
      if (claseCapturando.value === sena) {
        conteoCaptura.value = 0;
      }
      mostrarToast(`Muestras de '${sena}' borradas`, "exito");
    }
  } catch {
    mostrarToast("Error de conexion", "error");
  }
}

// Cargar el progreso cada vez que se abre el tab de senas
watch(tabActiva, (tab) => {
  if (tab === "senas" && autenticado.value) {
    cargarProgreso();
  }
});

// Detener camara si el componente se desmonta
onUnmounted(() => {
  cerrarCaptura();
});

async function agregarSena() {
  const nombre = nuevaSena.value.trim();
  if (!nombre) return;
  try {
    const res = await fetch("/admin/senas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ sena: nombre }),
    });
    const data = await res.json();
    if (data.exito) {
      senas.value = data.senas;
      nuevaSena.value = "";
      mostrarToast(`Sena '${nombre}' agregada`, "exito");
    } else {
      mostrarToast(data.mensaje, "error");
    }
  } catch {
    mostrarToast("Error de conexion", "error");
  }
}

async function eliminarSena(nombre) {
  if (!confirm(`Eliminar la sena '${nombre}'?`)) return;
  try {
    const res = await fetch(`/admin/senas/${nombre}`, {
      method: "DELETE",
      credentials: "include",
    });
    const data = await res.json();
    if (data.exito) {
      senas.value = data.senas;
      mostrarToast(`Sena '${nombre}' eliminada`, "exito");
    } else {
      mostrarToast(data.mensaje, "error");
    }
  } catch {
    mostrarToast("Error de conexion", "error");
  }
}

onMounted(async () => {
  // Verificar si ya hay sesion activa (por si el usuario recarga la pagina)
  try {
    const res = await fetch("/admin/verificar", { credentials: "include" });
    if (res.ok) {
      const data = await res.json();
      autenticado.value = data.autenticado;
      if (autenticado.value) {
        cargarDatos();
        cargarHistorial();
        cargarModeloInfo();
        cargarSenas();
        cargarProgreso();
      }
    }
  } catch {
    /* sin conexion */
  }
});
</script>

<style scoped>
.vista-admin {
  max-width: 900px;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--borde);
  padding-bottom: 0;
}

.tab {
  padding: 10px 20px;
  background: none;
  border: none;
  color: var(--texto-suave);
  font-size: 14px;
  font-weight: 500;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition:
    color 0.15s,
    border-color 0.15s;
  border-radius: 0;
}

.tab:hover {
  color: var(--texto);
}

.tab--activa {
  color: var(--texto);
  border-bottom-color: var(--azul);
  font-weight: 600;
}

.seccion-titulo {
  font-size: 16px;
  font-weight: 600;
}

.campo-grupo {
  margin-bottom: 18px;
}

.campo-hint {
  font-size: 12px;
  color: var(--texto-suave);
  margin-top: 5px;
}

/* Toggle switch */
.toggle-fila {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-btn {
  width: 46px;
  height: 26px;
  background: #2d3348;
  border: none;
  border-radius: 13px;
  padding: 3px;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}

.toggle-btn.activo {
  background: var(--azul);
  justify-content: flex-end;
}

.toggle-circulo {
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 50%;
  transition: margin 0.2s;
}

/* Metricas */
.metricas-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 700px) {
  .metricas-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metrica-card {
  background: #12151f;
  border: 1px solid var(--borde);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.metrica-valor {
  font-size: 28px;
  font-weight: 700;
  color: var(--azul);
}

.metrica-label {
  font-size: 12px;
  color: var(--texto-suave);
  margin-top: 4px;
}

/* Tabla */
.tabla-contenedor {
  overflow-x: auto;
}

.tabla {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.tabla th {
  text-align: left;
  padding: 10px 14px;
  background: #12151f;
  color: var(--texto-suave);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--borde);
}

.tabla td {
  padding: 10px 14px;
  border-bottom: 1px solid #1a1d27;
  vertical-align: middle;
}

.tabla tr:last-child td {
  border-bottom: none;
}

.tabla tr:hover td {
  background: #1a1d27;
}

/* Toast transition */
.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.25s,
    transform 0.25s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Barra de progreso indeterminada durante el entrenamiento */
@keyframes barra-slide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(400%);
  }
}
.barra-entrenando {
  width: 25%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #0df, transparent);
  animation: barra-slide 1.4s ease-in-out infinite;
}
</style>
