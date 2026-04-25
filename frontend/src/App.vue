<template>
  <div class="layout">
    <nav class="navbar">
      <div class="navbar__marca">
        <span class="navbar__icon">✋</span>
        <span class="navbar__titulo">HandTalk AI</span>
        <span class="badge badge-gris" style="margin-left: 8px; font-size: 11px"
          >LENSEGUA</span
        >
      </div>
      <div class="navbar__links">
        <RouterLink
          to="/"
          class="navbar__link"
          :class="{ activo: $route.name === 'usuario' }"
        >
          Detector
        </RouterLink>
        <RouterLink
          to="/admin"
          class="navbar__link"
          :class="{ activo: $route.name === 'admin' }"
        >
          Panel Admin
        </RouterLink>
      </div>
    </nav>

    <main class="contenido">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  height: 60px;
  background: #13161f;
  border-bottom: 1px solid var(--borde);
}

.navbar__marca {
  display: flex;
  align-items: center;
  gap: 10px;
}

.navbar__icon {
  font-size: 22px;
}

.navbar__titulo {
  font-weight: 700;
  font-size: 18px;
  letter-spacing: -0.3px;
}

.navbar__links {
  display: flex;
  gap: 6px;
}

.navbar__link {
  padding: 7px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--texto-suave);
  transition:
    color 0.15s,
    background 0.15s;
}

.navbar__link:hover {
  color: var(--texto);
  background: var(--borde);
}

.navbar__link.activo {
  color: var(--texto);
  background: #2d3348;
  font-weight: 600;
}

.contenido {
  flex: 1;
  padding: 28px;
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
}
</style>
