import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import { useUsuariosStore } from '@/stores/usuarios'

export const useAuthStore = defineStore('auth', () => {
  const token   = ref(localStorage.getItem('token') || null)

  const estaAutenticado = () => !!token.value

  async function login(identificador, contrasena) {
    const { data } = await api.post('/auth/login', {
      identificador,
      contrasena,
    })
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await useUsuariosStore().cargarUsuario()
  }

  function logout() {
    token.value   = null
    localStorage.removeItem('token')
    useUsuariosStore().limpiar()
  }

  return { token, estaAutenticado, login, logout }
})