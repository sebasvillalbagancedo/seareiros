<template>
  <div class="app-layout">

    <header class="topbar">
      <span class="topbar-titulo">Seareiros</span>
      <div class="topbar-usuario">
        <span>{{ usuario.nombre }} {{ usuario.apellidos }}</span>
        <span class="rol">{{ usuario.rol }}</span>
        <button @click="handleLogout">Cerrar sesión</button>
      </div>
    </header>

    <div class="app-body">
      <nav class="sidebar">
        <ul>
          <li
            v-for="item in menu"
            :key="item.id"
            :class="{ activo: moduloActivo === item.id }"
            @click="cambiarModulo(item.id)"
          >
            <component :is="item.icono" :size="18" class="sidebar-icono" />
            <span>{{ item.etiqueta }}</span>
          </li>
        </ul>
      </nav>
        
      <main class="app-contenido">
        <SociosView v-if="moduloActivo === 'socios'" />
        <SorteosView v-else-if="moduloActivo === 'sorteos'" />
          <div v-else class="app-placeholder">
            <p>Módulo en desarrollo.</p>
          </div>
      </main>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth'
import { useUsuariosStore } from '@/stores/usuarios'
import SociosView from '@/views/SociosView.vue'
import SorteosView from '@/views/SorteosView.vue'
import { Users, Dices, CalendarDays, MessageCircle } from 'lucide-vue-next'

export default {
  name: 'MainView',
  components: { SociosView, SorteosView, Users, Dices, CalendarDays, MessageCircle },
  emits: ['logout'],

  data() {
    return {
      moduloActivo: localStorage.getItem('moduloActivo') || 'socios',
      menu: [
        { id: 'socios',  icono: Users,         etiqueta: 'Socios' },
        { id: 'sorteos', icono: Dices,         etiqueta: 'Sorteos' },
        { id: 'eventos', icono: CalendarDays,  etiqueta: 'Eventos' },
        { id: 'chat',    icono: MessageCircle, etiqueta: 'Chat'    },
      ],
    }
  },

  computed: {
    usuario() {
      return useUsuariosStore().usuario
    }
  },

  methods: {
    cambiarModulo(id) {
      this.moduloActivo = id
      localStorage.setItem('moduloActivo', id)
    },
    handleLogout() {
      localStorage.removeItem('moduloActivo')
      useAuthStore().logout()
      this.$emit('logout')
    }
  }
}
</script>