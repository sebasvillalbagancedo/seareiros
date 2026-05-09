<template>
  <div v-if="cargando"></div>
  <LoginView v-else-if="!autenticado" @login-ok="onLoginOk" />
  <MainView  v-else                   @logout="onLogout"     />
</template>

<script>
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import MainView  from '@/views/MainView.vue'

export default {
  name: 'App',
  components: { LoginView, MainView },

  data() {
    return {
      autenticado: false,
      cargando:    true,
    }
  },

  async created() {
    const auth = useAuthStore()
    if (auth.estaAutenticado()) {
      try {
        await auth.cargarUsuario()
        this.autenticado = true
      } catch {
        auth.logout()
      }
    }
    this.cargando = false
  },

  methods: {
    onLoginOk() { this.autenticado = true  },
    onLogout()  { this.autenticado = false },
  }
}
</script>