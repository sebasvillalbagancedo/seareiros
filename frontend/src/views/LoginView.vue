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

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h1 {
  margin-bottom: 4px;
  font-size: 1.8rem;
  color: #2c3e50;
  text-align: center;
}

.subtitulo {
  text-align: center;
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 28px;
}

.campo {
  margin-bottom: 16px;
}

.btn-login {
  width: 100%;
  margin-top: 8px;
}
</style>