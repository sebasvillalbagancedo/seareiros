<template>
  <div class="main">

    <header class="topbar">
      <span class="titulo">Seareiros</span>
      <div class="usuario-info">
        <span>{{ usuario.nombre }} {{ usuario.apellidos }}</span>
        <span class="rol">{{ usuario.rol }}</span>
        <button @click="handleLogout">Cerrar sesión</button>
      </div>
    </header>

    <main class="contenido">
      <h2>Panel principal</h2>
      <p>Bienvenido, <strong>{{ usuario.nombre }}</strong>.</p>
      <p>Las funcionalidades se irán añadiendo en las siguientes iteraciones.</p>
    </main>

  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'MainView',
  emits: ['logout'],

  computed: {
    usuario() {
      return useAuthStore().usuario
    }
  },

  methods: {
    handleLogout() {
      useAuthStore().logout()
      this.$emit('logout')
    }
  }
}
</script>

<style scoped>
.main {
  min-height: 100vh;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #2c3e50;
  color: white;
  padding: 0 24px;
  height: 56px;
}

.titulo {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 1px;
}

.usuario-info {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 0.9rem;
}

.rol {
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  text-transform: capitalize;
}

button {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: white;
  padding: 5px 14px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.2s;
}

button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.contenido {
  padding: 40px;
}

.contenido h2 {
  color: #2c3e50;
  margin-bottom: 12px;
}

.contenido p {
  color: #555;
  line-height: 1.6;
}
</style>