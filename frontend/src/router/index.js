import { createRouter, createWebHashHistory } from "vue-router";
import VistaUsuario from "../views/VistaUsuario.vue";
import VistaAdmin from "../views/VistaAdmin.vue";

// Usamos hash history para no necesitar configuracion especial en el servidor
const routes = [
  { path: "/", name: "usuario", component: VistaUsuario },
  { path: "/admin", name: "admin", component: VistaAdmin },
];

export default createRouter({
  history: createWebHashHistory(),
  routes,
});
