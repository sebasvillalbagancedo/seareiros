<template>
  <div class="app-layout">
    <header class="topbar">
      <span class="topbar-titulo">Seareiros</span>
      <div class="topbar-usuario">
        <span>{{ usuario.nombre }} {{ usuario.apellidos }}</span>
        <span class="topbar-rol">{{ usuario.rol }}</span>
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
            <span
              v-if="item.id === 'chat' && mensajesNoLeidos > 0"
              class="badge badge-noLeidos sidebar-badge"
            >
              {{ mensajesNoLeidos }}
            </span>
          </li>
        </ul>
      </nav>

      <main class="app-contenido">
        <SociosView v-if="moduloActivo === 'socios'" />
        <SorteosView v-else-if="moduloActivo === 'sorteos'" />
        <ChatView v-else-if="moduloActivo === 'chat'" />
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
  import { useChatStore } from '@/stores/chat'
  import SociosView from '@/views/SociosView.vue'
  import SorteosView from '@/views/SorteosView.vue'
  import ChatView from '@/views/ChatView.vue'
  import { Users, Dices, CalendarDays, MessageCircle } from 'lucide-vue-next'

  export default {
    name: 'MainView',
    components: {
      SociosView,
      SorteosView,
      ChatView,
      Users,
      Dices,
      CalendarDays,
      MessageCircle,
    },
    emits: ['logout'],

    data() {
      return {
        moduloActivo: localStorage.getItem('moduloActivo') || 'socios',
        pollingId: null,
        menu: [
          { id: 'socios', icono: Users, etiqueta: 'Socios' },
          { id: 'sorteos', icono: Dices, etiqueta: 'Sorteos' },
          { id: 'eventos', icono: CalendarDays, etiqueta: 'Eventos' },
          { id: 'chat', icono: MessageCircle, etiqueta: 'Chat' },
        ],
      }
    },

    computed: {
      usuario() {
        return useUsuariosStore().usuario
      },

      mensajesNoLeidos() {
        return useChatStore().totalNoLeidos
      },
    },

    async created() {
      await Promise.all([useChatStore().cargarHistorial(), useChatStore().cargarInvitaciones()])
    },

    mounted() {
      this.pollingId = setInterval(async () => {
        await Promise.all([useChatStore().cargarHistorial(), useChatStore().cargarInvitaciones()])
      }, 15000)
    },

    beforeUnmount() {
      clearInterval(this.pollingId)
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
      },
    },
  }
</script>
