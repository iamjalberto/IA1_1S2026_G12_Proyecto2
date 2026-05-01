import { Bot, webhookCallback } from "grammy";

export interface Env {
  TELEGRAM_TOKEN: string;
}

// Las senas que el sistema HandTalk AI puede reconocer
const SENAS_DISPONIBLES = [
  "hola",
  "gracias",
  "si",
  "no",
  "ayuda",
  "agua",
  "bien",
  "mal",
  "por_favor",
  "casa",
];

// Se crea el bot con todos los handlers cada vez que llega una peticion.
// Cloudflare Workers es stateless, por lo que este patron es el correcto.
function crearBot(token: string): Bot {
  const bot = new Bot(token);

  // --- Comandos de Tarea 5 (se mantienen igual) ---

  bot.command("hola", async (ctx) => {
    const nombre = ctx.from?.first_name ?? "usuario";
    await ctx.reply(
      `Hola, ${nombre}! Soy el bot de HandTalk AI - Grupo 12.\n` +
        `Puedo informarte sobre el proyecto de reconocimiento de senas LENSEGUA.\n` +
        `Usa /ayuda para ver todos los comandos disponibles.`,
    );
  });

  bot.command("hora", async (ctx) => {
    const ahora = new Date();
    // Guatemala no tiene horario de verano, siempre UTC-6
    const fecha = new Intl.DateTimeFormat("es-GT", {
      timeZone: "America/Guatemala",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    }).format(ahora);
    const hora = new Intl.DateTimeFormat("es-GT", {
      timeZone: "America/Guatemala",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).format(ahora);
    await ctx.reply(
      `La hora actual en Guatemala es:\n` +
        `Fecha: ${fecha}\n` +
        `Hora:  ${hora} (UTC-6)`,
    );
  });

  bot.command("contacto", async (ctx) => {
    await ctx.reply(
      "Integrantes del Grupo 12:\n\n" +
        "Jose Alberto Alarcon Chigua\n" +
        "Carne: 201346084\n\n" +
        "Curso: Inteligencia Artificial 1\n" +
        "Universidad San Carlos de Guatemala\n" +
        "Facultad de Ingenieria",
    );
  });

  bot.command("proyecto", async (ctx) => {
    await ctx.reply(
      "Proyecto 2 - HandTalk AI\n\n" +
        "Sistema de reconocimiento de senas del lenguaje LENSEGUA en tiempo real.\n\n" +
        "Tecnologias utilizadas:\n" +
        "- MediaPipe: extraccion de landmarks de la mano\n" +
        "- scikit-learn: clasificacion con Random Forest / SVM\n" +
        "- Flask: API REST para predicciones\n" +
        "- Vue 3 + Vite: interfaz web\n" +
        "- Docker: contenedores para despliegue\n\n" +
        "Repositorio: https://github.com/iamjalberto/IA1_1S2026_G12_Proyecto2",
    );
  });

  // --- Comandos adicionales del Proyecto 2 ---

  bot.command("senas", async (ctx) => {
    // Muestra la lista de senas que el sistema puede reconocer
    const lista = SENAS_DISPONIBLES.map((s, i) => `  ${i + 1}. ${s}`).join(
      "\n",
    );
    await ctx.reply(
      "Senas que HandTalk AI puede reconocer:\n\n" +
        lista +
        "\n\n" +
        "Total: " +
        SENAS_DISPONIBLES.length +
        " senas del lenguaje LENSEGUA.",
    );
  });

  bot.command("ayuda", async (ctx) => {
    await ctx.reply(
      "Comandos disponibles:\n\n" +
        "-- Informacion general --\n" +
        "/hola       - Saludo del bot\n" +
        "/hora       - Hora actual en Guatemala\n" +
        "/contacto   - Informacion del grupo\n" +
        "/proyecto   - Descripcion del proyecto\n\n" +
        "-- HandTalk AI --\n" +
        "/senas      - Lista de senas reconocidas\n\n" +
        "/ayuda      - Muestra este mensaje",
    );
  });

  return bot;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const bot = crearBot(env.TELEGRAM_TOKEN);
    const handleUpdate = webhookCallback(bot, "cloudflare-mod");
    return handleUpdate(request);
  },
};
