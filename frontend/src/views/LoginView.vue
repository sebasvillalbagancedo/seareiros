<template>
  <div class="login-wrapper">
    <div class="login-card">

      <h1>Seareiros</h1>
      <p class="subtitulo">Plataforma de gestión de la peña</p>

      <form @submit.prevent="handleLogin">

        <div class="campo">
          <label>Email o código de usuario</label>
          <input
            v-model="identificador"
            type="text"
            placeholder="Email o código de usuario"
            required
          />
        </div>

        <div class="campo">
          <label>Contraseña</label>
          <input
            v-model="contrasena"
            type="password"
            placeholder="Contraseña"
            required
          />
        </div>

        <p v-if="error" class="error">{{ error }}</p>

        <button type="submit" :disabled="cargando">
          {{ cargando ? 'Accediendo...' : 'Iniciar sesión' }}
        </button>

      </form>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'LoginView',
  emits: ['login-ok'],

  data() {
    return {
      identificador: '',
      contrasena:    '',
      error:         null,
      cargando:      false,
    }
  },

  methods: {
    async handleLogin() {
      this.error    = null
      this.cargando = true
      try {
        const auth = useAuthStore()
        await auth.login(this.identificador, this.contrasena)
        this.$emit('login-ok')
      } catch {
        this.error = 'Credenciales incorrectas o cuenta inactiva.'
      } finally {
        this.cargando = false
      }
    }
  }
}
</script>