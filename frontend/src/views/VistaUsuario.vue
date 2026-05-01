<template>
  <div class="vista-usuario">
    <!-- Panel izquierdo: camara en tiempo real -->
    <section class="panel-camara card">
      <div class="panel-camara__header">
        <h2 class="panel-titulo">Camara en tiempo real</h2>
        <span
          class="punto-vivo"
          :class="estado.mano_detectada ? 'verde' : 'gris'"
        ></span>
      </div>

      <div class="camara-contenedor">
        <!-- La imagen apunta al stream MJPEG del backend via proxy Vite -->
        <!-- Se usa :src dinamico para que Vite no intente resolver la URL como modulo local -->
        <img
          :src="urlStreamCamara"
          alt="Stream de camara"
          class="camara-imagen"
        />
        <div v-if="!estado.modelo_listo" class="camara-overlay">
          <p>Modelo no entrenado aun</p>
          <p
            style="font-size: 12px; color: var(--texto-suave); margin-top: 6px"
          >
            Ejecuta el script de entrenamiento primero
          </p>
        </div>
      </div>

      <!-- Prediccion actual debajo de la camara -->
      <div class="prediccion-card">
        <div class="prediccion-sena">
          <span v-if="estado.sena_actual" class="prediccion-sena__texto">
            {{ estado.sena_actual }}
          </span>
          <span
            v-else-if="estado.mano_detectada"
            class="prediccion-sena__analizando"
          >
            Analizando...
          </span>
          <span v-else class="prediccion-sena__vacio">
            Sin mano detectada
          </span>
        </div>

        <template v-if="estado.sena_actual">
          <div style="margin-top: 10px">
            <div class="conf-fila">
              <span style="font-size: 13px; color: var(--texto-suave)"
                >Confianza</span
              >
              <span style="font-size: 13px; font-weight: 600">
                {{ (estado.confianza_actual * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="barra-confianza" style="margin-top: 6px">
              <div
                class="barra-confianza__relleno"
                :style="{ width: estado.confianza_actual * 100 + '%' }"
              ></div>
            </div>
          </div>
        </template>
      </div>
    </section>

    <!-- Panel derecho: captura de mensaje y envio -->
    <section class="panel-mensaje">
      <!-- Captura de senas -->
      <div class="card" style="margin-bottom: 16px">
        <h2 class="panel-titulo" style="margin-bottom: 14px">Capturar sena</h2>

        <p
          style="
            font-size: 13px;
            color: var(--texto-suave);
            margin-bottom: 14px;
          "
        >
          Haz la seña frente a la cámara y presiona el botón para agregarla al
          mensaje.
        </p>

        <button
          class="btn btn-verde"
          style="width: 100%; justify-content: center; padding: 12px"
          :disabled="!estado.sena_actual"
          @click="capturarSena"
        >
          + Capturar "{{ estado.sena_actual || "—" }}"
        </button>
      </div>

      <!-- Mensaje acumulado -->
      <div class="card" style="margin-bottom: 16px">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
          "
        >
          <h2 class="panel-titulo">Mensaje</h2>
          <button
            class="btn btn-gris"
            style="padding: 5px 12px; font-size: 12px"
            @click="limpiarMensaje"
          >
            Limpiar
          </button>
        </div>

        <div class="mensaje-chips">
          <template v-if="senasCapturadas.length > 0">
            <span
              v-for="(item, i) in senasCapturadas"
              :key="i"
              class="chip"
              @click="quitarSena(i)"
              title="Clic para quitar"
            >
              {{ item.sena }}
              <small style="opacity: 0.6; font-size: 10px; margin-left: 3px">
                {{ (item.confianza * 100).toFixed(0) }}%
              </small>
            </span>
          </template>
          <span v-else style="color: var(--texto-suave); font-size: 13px">
            Sin senas capturadas todavia
          </span>
        </div>

        <div v-if="senasCapturadas.length > 0" style="margin-top: 14px">
          <label>Vista previa del mensaje</label>
          <div class="mensaje-preview">{{ mensajeTexto }}</div>
        </div>
      </div>

      <!-- Envio a Telegram -->
      <div class="card">
        <h2 class="panel-titulo" style="margin-bottom: 14px">
          Enviar a Telegram
        </h2>

        <div v-if="!configTelegramActivo" class="alerta-info">
          El envio a Telegram esta desactivado. Activalo en el Panel Admin.
        </div>

        <button
          class="btn btn-azul"
          style="width: 100%; justify-content: center; padding: 12px"
          :disabled="senasCapturadas.length === 0 || enviandoTelegram"
          @click="enviarTelegram"
        >
          <span v-if="enviandoTelegram">Enviando...</span>
          <span v-else>Enviar mensaje a Telegram</span>
        </button>

        <div v-if="resultadoTelegram" style="margin-top: 12px">
          <span
            :class="
              resultadoTelegram.exito ? 'badge badge-verde' : 'badge badge-rojo'
            "
          >
            {{ resultadoTelegram.mensaje }}
          </span>
        </div>
      </div>

      <!-- Senas disponibles -->
      <div class="card" style="margin-top: 16px">
        <h2 class="panel-titulo" style="margin-bottom: 12px">
          Senas disponibles
        </h2>
        <div class="senas-grid">
          <span v-for="s in senasDisponibles" :key="s" class="badge badge-gris">
            {{ s }}
          </span>
        </div>
      </div>
    </section>

    <!-- Toast de notificacion -->
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="toast.tipo">
        {{ toast.texto }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";

// URL del stream MJPEG — se define como variable para evitar que Vite lo resuelva como modulo local
const urlStreamCamara = "/video_feed";

// Estado de la camara (se actualiza cada 300ms con polling al backend)
const estado = ref({
  sena_actual: null,
  confianza_actual: 0,
  mano_detectada: false,
  modelo_listo: false,
});

const senasCapturadas = ref([]);
const senasDisponibles = ref([]);
const configTelegramActivo = ref(false);
const enviandoTelegram = ref(false);
const resultadoTelegram = ref(null);

const toast = ref({ visible: false, texto: "", tipo: "exito" });
let intervaloPolling = null;

// Construye el texto del mensaje a partir de las senas capturadas
const mensajeTexto = computed(() => {
  return senasCapturadas.value.map((s) => s.sena).join(" ");
});

function mostrarToast(texto, tipo = "exito") {
  toast.value = { visible: true, texto, tipo };
  setTimeout(() => {
    toast.value.visible = false;
  }, 3000);
}

async function obtenerEstado() {
  try {
    const res = await fetch("/api/estado");
    if (res.ok) {
      estado.value = await res.json();
    }
  } catch {
    // Silencioso si el backend no responde temporalmente
  }
}

async function cargarSenas() {
  try {
    const res = await fetch("/api/senas");
    if (res.ok) {
      const data = await res.json();
      senasDisponibles.value = data.senas;
    }
  } catch {
    /* sin conexion */
  }
}

async function cargarConfig() {
  try {
    const res = await fetch("/admin/config_publica");
    if (res.ok) {
      const data = await res.json();
      configTelegramActivo.value = data.telegram_activo ?? false;
    }
  } catch {
    /* sin conexion */
  }
}

async function capturarSena() {
  const { sena_actual, confianza_actual } = estado.value;
  if (!sena_actual) return;

  senasCapturadas.value.push({
    sena: sena_actual,
    confianza: confianza_actual,
  });

  // Registrar en el historial del backend para las metricas
  try {
    await fetch("/api/registrar_sena", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sena: sena_actual, confianza: confianza_actual }),
    });
  } catch {
    /* no es critico */
  }

  mostrarToast(`"${sena_actual}" agregada al mensaje`);
}

function quitarSena(indice) {
  senasCapturadas.value.splice(indice, 1);
}

function limpiarMensaje() {
  senasCapturadas.value = [];
  resultadoTelegram.value = null;
}

async function enviarTelegram() {
  if (senasCapturadas.value.length === 0) return;
  enviandoTelegram.value = true;
  resultadoTelegram.value = null;

  try {
    const res = await fetch("/api/enviar_telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje: mensajeTexto.value }),
    });

    const data = await res.json();
    resultadoTelegram.value = data;

    if (data.exito) {
      mostrarToast("Mensaje enviado a Telegram correctamente", "exito");
      limpiarMensaje();
    } else {
      mostrarToast(data.mensaje, "error");
    }
  } catch {
    mostrarToast("Error de conexion con el backend", "error");
  } finally {
    enviandoTelegram.value = false;
  }
}

onMounted(() => {
  cargarSenas();
  cargarConfig();
  obtenerEstado();
  // Polling de estado cada 300ms para mostrar la prediccion en tiempo real
  intervaloPolling = setInterval(obtenerEstado, 300);
});

onUnmounted(() => {
  clearInterval(intervaloPolling);
});
</script>

<style scoped>
.vista-usuario {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 20px;
  align-items: start;
}

@media (max-width: 900px) {
  .vista-usuario {
    grid-template-columns: 1fr;
  }
}

.panel-titulo {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.panel-camara__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.camara-contenedor {
  position: relative;
  background: #0a0c12;
  border-radius: 8px;
  overflow: hidden;
  aspect-ratio: 4/3;
}

.camara-imagen {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.camara-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 12, 18, 0.8);
  font-weight: 600;
}

.prediccion-card {
  margin-top: 14px;
  padding: 14px;
  background: #12151f;
  border: 1px solid var(--borde);
  border-radius: 8px;
}

.prediccion-sena__texto {
  font-size: 28px;
  font-weight: 700;
  color: var(--verde);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.prediccion-sena__analizando {
  font-size: 18px;
  color: #22d3ee;
  font-style: italic;
}

.prediccion-sena__vacio {
  font-size: 15px;
  color: var(--texto-suave);
}

.conf-fila {
  display: flex;
  justify-content: space-between;
}

.mensaje-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 42px;
  padding: 10px;
  background: #0f1117;
  border: 1px solid var(--borde);
  border-radius: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  background: #1e3a5f;
  color: #93c5fd;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.chip:hover {
  background: #7f1d1d;
  color: #fca5a5;
}

.mensaje-preview {
  padding: 10px 14px;
  background: #0f1117;
  border: 1px dashed var(--borde);
  border-radius: 8px;
  font-family: monospace;
  font-size: 15px;
  color: var(--texto);
  margin-top: 6px;
  min-height: 44px;
  word-break: break-word;
}

.alerta-info {
  padding: 10px 14px;
  background: #1c1a06;
  border: 1px solid #854d0e;
  border-radius: 8px;
  color: #fde047;
  font-size: 13px;
  margin-bottom: 12px;
}

.senas-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Transicion del toast */
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
</style>
